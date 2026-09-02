"""API response/request schemas for customers, transactions and recovery cases."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerOut(ORMModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    historical_recovery_rate: float
    average_payment_amount: float
    customer_value: str
    opted_out: bool
    last_payment_at: Optional[str] = None


class TransactionOut(ORMModel):
    id: int
    customer_id: int
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    amount: float
    currency: str
    payment_method: str
    status: str
    failure_reason: Optional[str] = None
    loss_type: str
    is_synthetic: bool
    created_at: datetime


class DecisionOut(ORMModel):
    id: int
    decision: str
    channel: Optional[str] = None
    risk_level: Optional[str] = None
    recovery_probability: float
    expected_recovery_value: float
    confidence: float
    delay_minutes: int
    max_attempts: int
    reason: Optional[str] = None
    root_cause: Optional[str] = None
    decided_by: str
    model_version: str
    rationale_signals: Optional[str] = None
    created_at: datetime


class ActionOut(ORMModel):
    id: int
    action_type: str
    channel: Optional[str] = None
    status: str
    execution_mode: str
    attempt_number: int
    result: Optional[str] = None
    external_reference: Optional[str] = None
    executed_at: Optional[str] = None
    created_at: datetime


class EventOut(ORMModel):
    id: int
    label: str
    detail: Optional[str] = None
    actor: str
    icon: Optional[str] = None
    created_at: datetime


class RecoveryCaseOut(ORMModel):
    id: int
    transaction_id: int
    loss_type: str
    risk_level: str
    recovery_probability: float
    expected_recovery_value: float
    root_cause: Optional[str] = None
    root_cause_detail: Optional[str] = None
    recommended_action: Optional[str] = None
    recommended_channel: Optional[str] = None
    status: str
    priority: str
    recovered_amount: float
    created_at: datetime
    updated_at: datetime


class RecoveryCaseListItem(RecoveryCaseOut):
    customer_name: str
    customer_value: str
    amount: float
    currency: str
    payment_method: str
    failure_reason: Optional[str] = None


class CommunicationOut(ORMModel):
    id: int
    channel: str
    provider: str
    recipient: Optional[str] = None
    subject: Optional[str] = None
    status: str
    provider_message_id: Optional[str] = None
    payment_link: Optional[str] = None
    failure_reason: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: datetime


class InterventionOption(BaseModel):
    action_type: str
    label: str
    success_probability: float
    expected_value: float
    recommended: bool = False
    is_best_value: bool = False
    note: Optional[str] = None  # e.g. "Historical: 72% · n=14"


class RecoveryCaseDetail(RecoveryCaseOut):
    customer: CustomerOut
    transaction: TransactionOut
    decisions: List[DecisionOut] = []
    actions: List[ActionOut] = []
    events: List[EventOut] = []
    explainability: List[str] = []
    intervention_options: List[InterventionOption] = []
    communications: List[CommunicationOut] = []
    decided_by: Optional[str] = None
    fallback_reason: Optional[str] = None


class PaginatedCases(BaseModel):
    total: int
    items: List[RecoveryCaseListItem]


class MessagePreview(BaseModel):
    channel: str
    subject: Optional[str] = None
    body: str
    generated_by: str  # llm | template
