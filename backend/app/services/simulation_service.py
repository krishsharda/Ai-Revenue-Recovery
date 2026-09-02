"""Batch recovery simulation ("Run Recovery Simulation").

Generates realistic synthetic revenue-loss cases and runs each through the FULL
pipeline (ML probability -> AI decision -> guardrails -> sampled outcome),
returning metrics computed dynamically. No numbers are hardcoded.
"""
from __future__ import annotations

import random
from typing import Dict, List

from sqlalchemy.orm import Session

from ..agents import decide
from ..ml import get_model
from ..models.enums import RecoveryActionType
from ..policies import GuardrailContext, evaluate
from ..schemas.decision import AIDecisionInput
from ..schemas.dashboard import FunnelStage, InterventionPerformance
from ..schemas.simulation import SimulationResult
from .synthetic_cases import generate_case_inputs

_INTERVENTION_ORDER = [
    RecoveryActionType.RETRY_PAYMENT.value,
    RecoveryActionType.PAYMENT_LINK.value,
    RecoveryActionType.ALTERNATE_PAYMENT_METHOD.value,
    RecoveryActionType.SCHEDULE_RETRY.value,
    RecoveryActionType.EMAIL.value,
    RecoveryActionType.WHATSAPP.value,
    RecoveryActionType.HUMAN_ESCALATION.value,
    RecoveryActionType.DO_NOTHING.value,
]


def run_simulation(num_cases: int, seed: int | None = None, db: Session | None = None,
                   persist: bool = False, use_llm: bool = False) -> SimulationResult:
    seed = seed if seed is not None else random.randint(1, 10_000_000)
    rng = random.Random(seed)
    model = get_model()

    inputs = generate_case_inputs(num_cases, seed=seed)

    revenue_at_risk = 0.0
    recovery_attempts = 0
    recovered_cases = 0
    revenue_recovered = 0.0
    do_nothing_count = 0
    llm_calls = 0
    llm_successes = 0
    llm_fallbacks = 0

    perf: Dict[str, Dict[str, float]] = {
        a: {"attempts": 0, "successes": 0, "recovered": 0.0} for a in _INTERVENTION_ORDER
    }
    eligible_amt = recommended_amt = acted_amt = 0.0

    for idx, payload in enumerate(inputs):
        payload.model_recovery_probability = model.predict_proba(payload)
        revenue_at_risk += payload.transaction_amount
        recommended_amt += payload.transaction_amount

        decision = decide(payload, use_llm=use_llm)
        if use_llm:
            llm_calls += 1
            if decision.decided_by == "llm":
                llm_successes += 1
            else:
                llm_fallbacks += 1
        action = decision.recommended_action

        # Guardrail validation (fresh case: no prior attempts/messages).
        ctx = GuardrailContext(
            payment_already_succeeded=False, case_terminal=False, retries_used=0,
            messages_used=0, customer_opted_out=False,
            hours_since_failure=payload.time_since_payment_failure_minutes / 60.0,
            recovery_probability=payload.model_recovery_probability,
        )
        verdict = evaluate(action, ctx)
        if verdict.override_action is not None:
            action = verdict.override_action
        elif not verdict.allowed:
            action = RecoveryActionType.DO_NOTHING

        perf.setdefault(action.value, {"attempts": 0, "successes": 0, "recovered": 0.0})

        if action == RecoveryActionType.DO_NOTHING:
            do_nothing_count += 1
            perf[action.value]["attempts"] += 1
            continue

        eligible_amt += payload.transaction_amount
        acted_amt += payload.transaction_amount
        recovery_attempts += 1
        perf[action.value]["attempts"] += 1

        recovered = rng.random() < payload.model_recovery_probability
        if recovered:
            recovered_cases += 1
            revenue_recovered += payload.transaction_amount
            perf[action.value]["successes"] += 1
            perf[action.value]["recovered"] += payload.transaction_amount

    recovery_rate = round(100.0 * revenue_recovered / revenue_at_risk, 1) if revenue_at_risk else 0.0

    intervention = []
    for action in _INTERVENTION_ORDER:
        p = perf.get(action, {"attempts": 0, "successes": 0, "recovered": 0.0})
        if p["attempts"] == 0:
            continue
        is_do_nothing = action == RecoveryActionType.DO_NOTHING.value
        rate = None if is_do_nothing else round(p["successes"] / p["attempts"], 4)
        intervention.append(InterventionPerformance(
            action_type=action, attempts=int(p["attempts"]), successes=int(p["successes"]),
            success_rate=rate, recovered_amount=round(p["recovered"], 2)))

    funnel = [
        FunnelStage(stage="Revenue at Risk", amount=round(revenue_at_risk, 2), count=num_cases),
        FunnelStage(stage="Eligible for Recovery", amount=round(eligible_amt, 2),
                    count=num_cases - do_nothing_count),
        FunnelStage(stage="AI Recommended", amount=round(recommended_amt, 2), count=num_cases),
        FunnelStage(stage="Recovery Action", amount=round(acted_amt, 2), count=recovery_attempts),
        FunnelStage(stage="Payment Completed", amount=round(revenue_recovered, 2), count=recovered_cases),
        FunnelStage(stage="Revenue Recovered", amount=round(revenue_recovered, 2), count=recovered_cases),
    ]

    persisted = False
    persisted_cases = 0
    if persist and db is not None:
        persisted_cases = _persist(db, inputs)
        persisted = persisted_cases > 0

    return SimulationResult(
        num_cases=num_cases,
        revenue_at_risk=round(revenue_at_risk, 2),
        decision_engine="openai + heuristic fallback" if use_llm else "deterministic heuristic",
        llm_calls=llm_calls,
        llm_successes=llm_successes,
        llm_fallbacks=llm_fallbacks,
        ai_analyzed=num_cases,
        recovery_attempts=recovery_attempts,
        recovered_cases=recovered_cases,
        revenue_recovered=round(revenue_recovered, 2),
        recovery_rate=recovery_rate,
        do_nothing_count=do_nothing_count,
        intervention_performance=intervention,
        funnel=funnel,
        persisted=persisted,
        persisted_cases=persisted_cases,
    )


def _persist(db: Session, inputs: List[AIDecisionInput]) -> int:
    """Materialise at most 80 simulated cases for serverless safety."""
    from ..models.customer import Customer
    from ..models.transaction import Transaction
    from . import recovery_service

    names = ["Aarav", "Vivaan", "Aditya", "Diya", "Ananya", "Ishaan", "Kabir", "Myra",
             "Sara", "Reyansh", "Anika", "Vihaan", "Kiara", "Arjun", "Neha", "Rohan"]
    inputs = inputs[:80]  # persisting is bounded — the in-memory run handles large batches
    created = 0
    for i, payload in enumerate(inputs):
        cust = Customer(
            name=f"{names[i % len(names)]} {chr(65 + i % 26)}. (sim)",
            email=f"sim{i}@example.test",
            phone=None,
            total_transactions=payload.previous_successful_payments + payload.previous_failed_payments + 1,
            successful_transactions=payload.previous_successful_payments,
            failed_transactions=payload.previous_failed_payments + 1,
            historical_recovery_rate=payload.historical_recovery_rate,
            average_payment_amount=payload.transaction_amount,
            customer_value=payload.customer_value.value,
        )
        db.add(cust)
        db.flush()
        txn = Transaction(
            customer_id=cust.id, amount=payload.transaction_amount, currency=payload.currency,
            payment_method=payload.payment_method.value, status="FAILED",
            failure_reason=payload.failure_reason.value, loss_type=payload.loss_type.value,
            is_synthetic=True,
        )
        db.add(txn)
        db.flush()
        recovery_service.process_failed_transaction(db, txn, execute=True, simulate=True, use_llm=False)
        created += 1
    db.commit()
    return created
