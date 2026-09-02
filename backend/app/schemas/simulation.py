from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .dashboard import FunnelStage, InterventionPerformance


class SimulationRequest(BaseModel):
    num_cases: int = Field(default=200, ge=1, le=2000)
    seed: Optional[int] = None
    use_llm: bool = Field(
        default=False,
        description="Use the configured LLM for a small sample; limited to 10 cases.",
    )
    persist: bool = Field(
        default=False,
        description="If true, generated cases are written to the database; "
        "otherwise the simulation is computed in-memory only.",
    )


class SimulationResult(BaseModel):
    num_cases: int
    revenue_at_risk: float
    decision_engine: str
    llm_calls: int
    llm_successes: int
    llm_fallbacks: int
    ai_analyzed: int
    recovery_attempts: int
    recovered_cases: int
    revenue_recovered: float
    recovery_rate: float
    do_nothing_count: int
    intervention_performance: List[InterventionPerformance]
    funnel: List[FunnelStage]
    persisted: bool
    persisted_cases: int
