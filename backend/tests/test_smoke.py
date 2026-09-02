"""End-to-end smoke test exercising the full API surface."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


def run() -> None:
    with TestClient(app) as client:
        # Health + config
        h = client.get("/api/health").json()
        assert h["status"] == "ok", h
        cfg = client.get("/api/config").json()
        assert cfg["mode"] == "Razorpay Test Mode"
        print("health:", h["status"], "| engine:", h["database_engine"],
              "| model acc:", h["model"]["train_accuracy"])
        print("decision engine:", cfg["decision_engine"], "| policy:", cfg["policy"])

        # Dashboard
        dash = client.get("/api/dashboard").json()
        print("\nDASHBOARD")
        for m in dash["metrics"]:
            print(f"  {m['label']:<24} {m['display']}")
        print("  action mix:", {a["action_type"]: a["count"] for a in dash["action_counts"]})
        print("  top opportunities:")
        for t in dash["top_opportunities"][:5]:
            print(f"    {t['customer_name']:<16} ₹{t['amount']:>8,.0f}  "
                  f"{t['recovery_probability']*100:>4.0f}%  {t['recommended_action']}")

        # Cases
        cases = client.get("/api/recovery-cases?limit=5").json()
        print("\nCASES total:", cases["total"])
        first_id = cases["items"][0]["id"]
        detail = client.get(f"/api/recovery-cases/{first_id}").json()
        print("  detail case", first_id, "->", detail["status"],
              "| action:", detail["recommended_action"],
              "| explain:", detail["explainability"][:2])

        # Analyze + execute a fresh active case
        active = client.get("/api/recovery-cases?status=RECOMMENDED&limit=1").json()
        if active["items"]:
            cid = active["items"][0]["id"]
            ex = client.post(f"/api/recovery-cases/{cid}/execute",
                             json={"simulate": True}).json()
            print("\nEXECUTE case", cid, "->", ex["result"].get("status"),
                  "| action:", ex["result"].get("action"),
                  "| outcome:", ex["result"].get("outcome"),
                  "| mode:", ex["result"].get("execution_mode"))

        # Analytics
        an = client.get("/api/analytics").json()
        print("\nINTERVENTION PERFORMANCE")
        for p in an["intervention_performance"]:
            rate = "N/A" if p["success_rate"] is None else f"{p['success_rate']*100:.0f}%"
            print(f"  {p['action_type']:<26} attempts={p['attempts']:<3} rate={rate}")

        # Audit
        audit = client.get("/api/audit-logs?limit=6").json()
        print("\nAUDIT total:", audit["total"])
        for a in audit["items"][:6]:
            print(f"  {a['event']:<20} {a['actor']:<14} {a.get('action') or ''} "
                  f"{a.get('result') or ''}")

        # Simulation
        sim = client.post("/api/simulation/run", json={"num_cases": 1000, "seed": 7}).json()
        print("\nSIMULATION (1000 cases)")
        print(f"  revenue_at_risk=₹{sim['revenue_at_risk']:,.0f} "
              f"recovered=₹{sim['revenue_recovered']:,.0f} rate={sim['recovery_rate']}% "
              f"attempts={sim['recovery_attempts']} do_nothing={sim['do_nothing_count']}")
        for p in sim["intervention_performance"]:
            rate = "N/A" if p["success_rate"] is None else f"{p['success_rate']*100:.0f}%"
            print(f"    {p['action_type']:<26} n={p['attempts']:<4} rate={rate}")

        # Webhook (payment.failed then payment.captured), signature-verified path
        _webhook_roundtrip(client)

        print("\nALL SMOKE CHECKS PASSED ✅")


def _webhook_roundtrip(client) -> None:
    settings.razorpay_webhook_secret = "whsec_demo_secret"  # enable verification path
    order_id = "order_TEST_WEBHOOK_1"
    payment_id = "pay_TEST_WEBHOOK_1"
    failed = {
        "event": "payment.failed",
        "payload": {"payment": {"entity": {
            "id": payment_id, "order_id": order_id, "amount": 999900, "currency": "INR",
            "method": "card", "status": "failed", "error_code": "BAD_REQUEST_ERROR",
            "error_description": "payment declined by bank", "email": "webhook.user@example.test",
        }}},
    }
    body = json.dumps(failed).encode()
    sig = hmac.new(b"whsec_demo_secret", body, hashlib.sha256).hexdigest()

    bad = client.post("/api/webhooks/razorpay", content=body,
                      headers={"X-Razorpay-Signature": "deadbeef"})
    assert bad.status_code == 400, bad.text
    good = client.post("/api/webhooks/razorpay", content=body,
                       headers={"X-Razorpay-Signature": sig})
    assert good.status_code == 200, good.text
    res = good.json()
    print("\nWEBHOOK payment.failed ->", res)
    assert res["handled"] and res.get("case_id")

    captured = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {
            "id": payment_id, "order_id": order_id, "amount": 999900, "currency": "INR",
            "method": "card", "status": "captured",
        }}},
    }
    cbody = json.dumps(captured).encode()
    csig = hmac.new(b"whsec_demo_secret", cbody, hashlib.sha256).hexdigest()
    cap = client.post("/api/webhooks/razorpay", content=cbody,
                      headers={"X-Razorpay-Signature": csig}).json()
    print("WEBHOOK payment.captured ->", cap)
    assert cap["handled"] and cap.get("matched")


if __name__ == "__main__":
    run()
