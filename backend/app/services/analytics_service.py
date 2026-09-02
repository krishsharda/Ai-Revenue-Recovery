"""Dashboard + analytics aggregation. All numbers are computed from the DB —
nothing is hardcoded."""
from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models.customer import Customer
from ..models.enums import RecoveryActionType
from ..models.recovery_case import RecoveryCase
from ..models.transaction import Transaction
from ..schemas.dashboard import (
    ActionCount,
    AnalyticsResponse,
    DashboardResponse,
    EmailStats,
    FunnelStage,
    InterventionPerformance,
    LossTypeBreakdown,
    MetricCard,
    TopOpportunity,
)
from . import memory_service

ACTIVE_STATUSES = {"OPEN", "ANALYZING", "RECOMMENDED", "IN_RECOVERY"}
LOST_STATUSES = {"FAILED", "CLOSED"}

_LOSS_LABELS = {
    "PAYMENT_FAILURE": "Failed Payments",
    "CHECKOUT_ABANDONMENT": "Checkout Abandonments",
    "SUBSCRIPTION_FAILURE": "Subscription Failures",
    "OVERDUE_INVOICE": "Overdue Receivables",
}


def _fmt_inr(amount: float) -> str:
    """Format rupees in Indian lakh/crore short form."""
    if amount >= 1e7:
        return f"₹{amount/1e7:.2f}Cr"
    if amount >= 1e5:
        return f"₹{amount/1e5:.2f}L"
    if amount >= 1e3:
        return f"₹{amount/1e3:.1f}K"
    return f"₹{amount:,.0f}"


def _cases_with_txn(db: Session):
    return db.execute(
        select(RecoveryCase, Transaction, Customer)
        .join(Transaction, RecoveryCase.transaction_id == Transaction.id)
        .join(Customer, Transaction.customer_id == Customer.id)
    ).all()


def dashboard(db: Session) -> DashboardResponse:
    rows = _cases_with_txn(db)
    revenue_at_risk = sum(t.amount for c, t, _ in rows if c.status in ACTIVE_STATUSES)
    revenue_recovered = sum(c.recovered_amount for c, _, _ in rows if c.status == "RECOVERED")
    # Recovery rate = recovered / all revenue that ever entered recovery (spec definition).
    total_addressable = sum(t.amount for _, t, _ in rows)
    recovery_rate = round(100.0 * revenue_recovered / total_addressable, 1) if total_addressable else 0.0
    active_cases = sum(1 for c, _, _ in rows if c.status in ACTIVE_STATUSES)

    metrics = [
        MetricCard(label="Revenue at Risk", value=round(revenue_at_risk, 2),
                   display=_fmt_inr(revenue_at_risk), sublabel="Active, still winnable"),
        MetricCard(label="Revenue Recovered", value=round(revenue_recovered, 2),
                   display=_fmt_inr(revenue_recovered), sublabel="Captured back"),
        MetricCard(label="Recovery Rate", value=recovery_rate,
                   display=f"{recovery_rate:.1f}%", sublabel="Of revenue at risk"),
        MetricCard(label="Active Recovery Cases", value=float(active_cases),
                   display=f"{active_cases:,}", sublabel="In flight"),
    ]

    # Loss-type breakdown (amount currently at risk per type).
    breakdown: Dict[str, LossTypeBreakdown] = {}
    for key, label in _LOSS_LABELS.items():
        breakdown[key] = LossTypeBreakdown(loss_type=key, label=label, count=0, amount_at_risk=0.0)
    for c, t, _ in rows:
        b = breakdown.get(c.loss_type)
        if b is None:
            b = LossTypeBreakdown(loss_type=c.loss_type, label=c.loss_type, count=0, amount_at_risk=0.0)
            breakdown[c.loss_type] = b
        if c.status in ACTIVE_STATUSES:
            b.count += 1
            b.amount_at_risk += t.amount

    # Action distribution across all cases.
    action_counter: Dict[str, int] = {}
    for c, _, _ in rows:
        if c.recommended_action:
            action_counter[c.recommended_action] = action_counter.get(c.recommended_action, 0) + 1
    action_counts = [ActionCount(action_type=a, count=n)
                     for a, n in sorted(action_counter.items(), key=lambda kv: kv[1], reverse=True)]

    # Top opportunities (active, by expected recovery value).
    active = [(c, t, cu) for c, t, cu in rows if c.status in ACTIVE_STATUSES]
    active.sort(key=lambda r: r[0].expected_recovery_value, reverse=True)
    top = [
        TopOpportunity(case_id=c.id, customer_name=cu.name, amount=t.amount, currency=t.currency,
                       recovery_probability=c.recovery_probability,
                       recommended_action=c.recommended_action, risk_level=c.risk_level)
        for c, t, cu in active[:6]
    ]

    return DashboardResponse(
        mode="Razorpay Test Mode",
        razorpay_configured=settings.razorpay_configured,
        llm_configured=settings.llm_configured,
        revenue_at_risk=round(revenue_at_risk, 2),
        revenue_recovered=round(revenue_recovered, 2),
        recovery_rate=recovery_rate,
        active_cases=active_cases,
        total_cases=len(rows),
        metrics=metrics,
        loss_type_breakdown=list(breakdown.values()),
        action_counts=action_counts,
        top_opportunities=top,
        funnel=_funnel(rows),
        email=_email_stats(db, rows),
    )


def _email_stats(db: Session, rows) -> "EmailStats":
    from ..models.communication import CommunicationRecord

    comms = db.execute(select(CommunicationRecord)).scalars().all()
    sent = sum(1 for c in comms if c.status == "SENT")
    failed = sum(1 for c in comms if c.status == "FAILED")
    blocked = sum(1 for c in comms if c.status == "BLOCKED")
    # Recovered cases that received a SENT email.
    emailed_case_ids = {c.recovery_case_id for c in comms if c.status == "SENT" and c.recovery_case_id}
    recovered_email_cases = [(c, t) for c, t, _ in rows
                             if c.id in emailed_case_ids and c.status == "RECOVERED"]
    return EmailStats(
        configured=settings.resend_configured,
        sent=sent, failed=failed, blocked=blocked, attempts=len(comms),
        recoveries=len(recovered_email_cases),
        recovered_amount=round(sum(c.recovered_amount for c, _ in recovered_email_cases), 2),
    )


def _funnel(rows) -> List[FunnelStage]:
    total_amt = sum(t.amount for _, t, _ in rows)
    eligible = [(c, t) for c, t, _ in rows
                if c.recommended_action and c.recommended_action != RecoveryActionType.DO_NOTHING.value]
    recommended = [(c, t) for c, t, _ in rows if c.recommended_action]
    acted = [(c, t) for c, t, _ in rows
             if c.status in {"IN_RECOVERY", "RECOVERED", "FAILED", "CLOSED"}]
    recovered = [(c, t) for c, t, _ in rows if c.status == "RECOVERED"]

    def amt(pairs):
        return round(sum(t.amount for _, t in pairs), 2)

    return [
        FunnelStage(stage="Revenue at Risk", amount=round(total_amt, 2), count=len(rows)),
        FunnelStage(stage="Eligible for Recovery", amount=amt(eligible), count=len(eligible)),
        FunnelStage(stage="AI Recommended", amount=amt(recommended), count=len(recommended)),
        FunnelStage(stage="Recovery Action", amount=amt(acted), count=len(acted)),
        FunnelStage(stage="Payment Completed", amount=round(sum(c.recovered_amount for c, _ in recovered), 2),
                    count=len(recovered)),
        FunnelStage(stage="Revenue Recovered",
                    amount=round(sum(c.recovered_amount for c, _ in recovered), 2), count=len(recovered)),
    ]


def analytics(db: Session) -> AnalyticsResponse:
    rows = _cases_with_txn(db)

    # Intervention performance from executed cases (attempts/successes per action).
    perf: Dict[str, Dict[str, float]] = {}
    for c, t, _ in rows:
        action = c.recommended_action
        if not action:
            continue
        p = perf.setdefault(action, {"attempts": 0, "successes": 0, "recovered": 0.0})
        if action == RecoveryActionType.DO_NOTHING.value:
            p["attempts"] += 1  # counted, but rate stays N/A
            continue
        if c.status in {"IN_RECOVERY", "RECOVERED", "FAILED", "CLOSED", "DO_NOTHING"}:
            p["attempts"] += 1
            if c.status == "RECOVERED":
                p["successes"] += 1
                p["recovered"] += c.recovered_amount

    intervention = []
    for action, p in sorted(perf.items(), key=lambda kv: kv[1]["attempts"], reverse=True):
        is_do_nothing = action == RecoveryActionType.DO_NOTHING.value
        rate = None if is_do_nothing or p["attempts"] == 0 else round(p["successes"] / p["attempts"], 4)
        intervention.append(InterventionPerformance(
            action_type=action, attempts=int(p["attempts"]), successes=int(p["successes"]),
            success_rate=rate, recovered_amount=round(p["recovered"], 2)))

    # Recovery memory as its own performance table, aggregated per
    # (action, root cause) across loss types so labels are unique + meaningful.
    mem_agg: Dict[tuple, Dict[str, float]] = {}
    for m in memory_service.list_memory(db):
        acc = mem_agg.setdefault((m.action_type, m.root_cause),
                                 {"attempts": 0, "successes": 0, "recovered": 0.0})
        acc["attempts"] += m.attempts
        acc["successes"] += m.successes
        acc["recovered"] += m.recovered_amount
    memory = [
        InterventionPerformance(
            action_type=f"{action} · {cause}", attempts=int(v["attempts"]),
            successes=int(v["successes"]),
            success_rate=round(v["successes"] / v["attempts"], 4) if v["attempts"] else None,
            recovered_amount=round(v["recovered"], 2))
        for (action, cause), v in sorted(mem_agg.items(), key=lambda kv: kv[1]["attempts"], reverse=True)
    ]

    # Risk distribution.
    risk_counter: Dict[str, int] = {}
    for c, _, _ in rows:
        risk_counter[c.risk_level] = risk_counter.get(c.risk_level, 0) + 1
    risk_dist = [ActionCount(action_type=k, count=v)
                 for k, v in sorted(risk_counter.items(), key=lambda kv: kv[1], reverse=True)]

    dash = dashboard(db)
    return AnalyticsResponse(
        intervention_performance=intervention,
        funnel=dash.funnel,
        action_counts=dash.action_counts,
        loss_type_breakdown=dash.loss_type_breakdown,
        recovery_memory=memory,
        risk_distribution=risk_dist,
    )
