"""Email recovery tests — run standalone: python tests/test_email.py

Uses a throwaway SQLite DB and monkeypatches the Resend transport so no real
email is sent. Covers guardrail blocks, send success/failure, and the
webhook-driven recovery (email delivery is kept separate from revenue recovery).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_email.db"
os.environ["RESEND_API_KEY"] = "re_test_key"
os.environ["EMAIL_FROM"] = "AI Revenue Recovery <recovery@example.test>"

# Fresh DB file.
if os.path.exists("test_email.db"):
    os.remove("test_email.db")

from app.config import settings  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.integrations import resend_client  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402
from app.models.communication import CommunicationRecord  # noqa: E402
from app.models.enums import RecoveryActionType, TransactionStatus  # noqa: E402
from app.policies import GuardrailContext, evaluate  # noqa: E402
from app.services import email_service, recovery_service  # noqa: E402

EMAIL = RecoveryActionType.EMAIL
_ok = 0
_fail = 0


def check(name, cond):
    global _ok, _fail
    if cond:
        _ok += 1
        print(f"  PASS  {name}")
    else:
        _fail += 1
        print(f"  FAIL  {name}")


def _customer(db, email="rahul@example.test", opted_out=False):
    c = Customer(name="Rahul", email=email, opted_out=opted_out, customer_value="high",
                 total_transactions=16, successful_transactions=14, failed_transactions=2,
                 historical_recovery_rate=0.8, average_payment_amount=12000)
    db.add(c); db.flush()
    t = Transaction(customer_id=c.id, amount=12500, currency="INR", payment_method="card",
                    status="FAILED", failure_reason="BANK_DECLINE", loss_type="PAYMENT_FAILURE",
                    razorpay_order_id="order_TEST_EMAIL", is_synthetic=True)
    db.add(t); db.flush()
    return c, t


def run():
    init_db()
    db = SessionLocal()

    # --- Guardrail-level blocks --------------------------------------------
    check("missing email -> guardrail blocks EMAIL",
          not evaluate(EMAIL, GuardrailContext(recovery_probability=0.8, customer_email_present=False)).allowed)
    check("opted-out -> guardrail blocks EMAIL",
          not evaluate(EMAIL, GuardrailContext(recovery_probability=0.8, customer_opted_out=True)).allowed)
    check("payment already captured -> blocks",
          not evaluate(EMAIL, GuardrailContext(recovery_probability=0.8, payment_already_succeeded=True)).allowed)
    check("max messages reached -> blocks",
          not evaluate(EMAIL, GuardrailContext(recovery_probability=0.8, messages_used=settings.max_customer_messages)).allowed)
    check("recovery window expired -> blocks",
          not evaluate(EMAIL, GuardrailContext(recovery_probability=0.8, hours_since_failure=999)).allowed)
    check("valid context -> EMAIL allowed",
          evaluate(EMAIL, GuardrailContext(recovery_probability=0.8)).allowed)

    # --- Send success (Resend accepts) -------------------------------------
    resend_client.send = lambda *a, **k: "msg_abc123"  # monkeypatch transport
    c, t = _customer(db)
    rec = email_service.send_recovery_email(
        db, recovery_case_id=None, customer_id=c.id, to_email=c.email, customer_name="Rahul",
        amount=12500, currency="INR", subject="Complete your ₹12,500 payment",
        body="Please complete your payment.", payment_link="https://rzp.io/x")
    check("valid email + Resend ok -> SENT with provider id",
          rec.status == "SENT" and rec.provider_message_id == "msg_abc123")

    # --- Missing recipient -> BLOCKED (never sent) -------------------------
    rec2 = email_service.send_recovery_email(
        db, recovery_case_id=None, customer_id=None, to_email=None, customer_name="X",
        amount=100, currency="INR", subject="s", body="b")
    check("missing recipient -> BLOCKED", rec2.status == "BLOCKED")

    # --- Resend API failure -> FAILED (not SENT) ---------------------------
    def _boom(*a, **k):
        raise resend_client.ResendError("Resend API error 500: upstream")
    resend_client.send = _boom
    rec3 = email_service.send_recovery_email(
        db, recovery_case_id=None, customer_id=c.id, to_email=c.email, customer_name="Rahul",
        amount=12500, currency="INR", subject="s", body="b")
    check("Resend failure -> FAILED, no fake success",
          rec3.status == "FAILED" and rec3.provider_message_id is None)

    # --- Webhook drives recovery (email SENT != recovered) -----------------
    case = recovery_service.process_failed_transaction(db, t, execute=False, use_llm=False)
    db.commit()
    check("email sent but case not RECOVERED yet", case.status != "RECOVERED")
    recovery_service.mark_recovered_by_webhook(db, t, "pay_TEST_1")
    db.commit()
    check("Razorpay capture webhook -> case RECOVERED", case.status == "RECOVERED"
          and case.recovered_amount == 12500)
    # Duplicate webhook -> idempotent
    before = case.recovered_amount
    recovery_service.mark_recovered_by_webhook(db, t, "pay_TEST_1")
    db.commit()
    check("duplicate webhook -> no double recovery", case.recovered_amount == before)

    db.close()
    print(f"\n{_ok} passed, {_fail} failed")
    if _fail:
        sys.exit(1)


if __name__ == "__main__":
    run()
