"""Schemas for dashboard, command center and analytics responses."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class MetricCard(BaseModel):
    label: str
    value: float
    display: str
    sublabel: Optional[str] = None


class LossTypeBreakdown(BaseModel):
    loss_type: str
    label: str
    count: int
    amount_at_risk: float


class ActionCount(BaseModel):
    action_type: str
    count: int


class FunnelStage(BaseModel):
    stage: str
    amount: float
    count: int


class InterventionPerformance(BaseModel):
    action_type: str
    attempts: int
    successes: int
    success_rate: Optional[float]  # None => "N/A" (e.g. DO_NOTHING)
    recovered_amount: float


class TopOpportunity(BaseModel):
    case_id: int
    customer_name: str
    amount: float
    currency: str
    recovery_probability: float
    recommended_action: Optional[str]
    risk_level: str


class EmailStats(BaseModel):
    configured: bool
    sent: int
    failed: int
    blocked: int
    attempts: int
    recoveries: int          # recovered cases that received a sent email
    recovered_amount: float  # ₹ recovered on those cases


class DashboardResponse(BaseModel):
    mode: str  # test-mode banner text
    razorpay_configured: bool
    llm_configured: bool
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    active_cases: int
    total_cases: int
    metrics: List[MetricCard]
    loss_type_breakdown: List[LossTypeBreakdown]
    action_counts: List[ActionCount]
    top_opportunities: List[TopOpportunity]
    funnel: List[FunnelStage]
    email: EmailStats


class AnalyticsResponse(BaseModel):
    intervention_performance: List[InterventionPerformance]
    funnel: List[FunnelStage]
    action_counts: List[ActionCount]
    loss_type_breakdown: List[LossTypeBreakdown]
    recovery_memory: List[InterventionPerformance]
    risk_distribution: List[ActionCount]
