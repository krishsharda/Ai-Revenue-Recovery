// TypeScript mirrors of the backend response schemas.

export interface AppConfig {
  mode: string;
  app_name: string;
  environment: string;
  features: {
    razorpay_configured: boolean;
    razorpay_webhook_configured: boolean;
    llm_configured: boolean;
    llm_provider: string | null;
    llm_model: string | null;
    email_configured: boolean;
    email_provider: string | null;
    database_engine: string;
  };
  policy: {
    max_payment_retries: number;
    max_customer_messages: number;
    recovery_window_hours: number;
    min_recovery_probability: number;
  };
  decision_engine: string;
}

export interface MetricCard {
  label: string;
  value: number;
  display: string;
  sublabel?: string | null;
}

export interface LossTypeBreakdown {
  loss_type: string;
  label: string;
  count: number;
  amount_at_risk: number;
}

export interface ActionCount {
  action_type: string;
  count: number;
}

export interface FunnelStage {
  stage: string;
  amount: number;
  count: number;
}

export interface InterventionPerformance {
  action_type: string;
  attempts: number;
  successes: number;
  success_rate: number | null;
  recovered_amount: number;
}

export interface TopOpportunity {
  case_id: number;
  customer_name: string;
  amount: number;
  currency: string;
  recovery_probability: number;
  recommended_action: string | null;
  risk_level: string;
}

export interface EmailStats {
  configured: boolean;
  sent: number;
  failed: number;
  blocked: number;
  attempts: number;
  recoveries: number;
  recovered_amount: number;
}

export interface DashboardResponse {
  mode: string;
  razorpay_configured: boolean;
  llm_configured: boolean;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  active_cases: number;
  total_cases: number;
  metrics: MetricCard[];
  loss_type_breakdown: LossTypeBreakdown[];
  action_counts: ActionCount[];
  top_opportunities: TopOpportunity[];
  funnel: FunnelStage[];
  email: EmailStats;
}

export interface AnalyticsResponse {
  intervention_performance: InterventionPerformance[];
  funnel: FunnelStage[];
  action_counts: ActionCount[];
  loss_type_breakdown: LossTypeBreakdown[];
  recovery_memory: InterventionPerformance[];
  risk_distribution: ActionCount[];
}

export interface RecoveryCaseListItem {
  id: number;
  transaction_id: number;
  loss_type: string;
  risk_level: string;
  recovery_probability: number;
  expected_recovery_value: number;
  root_cause: string | null;
  recommended_action: string | null;
  recommended_channel: string | null;
  status: string;
  priority: string;
  recovered_amount: number;
  created_at: string;
  updated_at: string;
  customer_name: string;
  customer_value: string;
  amount: number;
  currency: string;
  payment_method: string;
  failure_reason: string | null;
}

export interface PaginatedCases {
  total: number;
  items: RecoveryCaseListItem[];
}

export interface CustomerOut {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  historical_recovery_rate: number;
  average_payment_amount: number;
  customer_value: string;
  opted_out: boolean;
  last_payment_at: string | null;
}

export interface TransactionOut {
  id: number;
  customer_id: number;
  razorpay_payment_id: string | null;
  razorpay_order_id: string | null;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  failure_reason: string | null;
  loss_type: string;
  is_synthetic: boolean;
  created_at: string;
}

export interface DecisionOut {
  id: number;
  decision: string;
  channel: string | null;
  risk_level: string | null;
  recovery_probability: number;
  expected_recovery_value: number;
  confidence: number;
  delay_minutes: number;
  max_attempts: number;
  reason: string | null;
  root_cause: string | null;
  decided_by: string;
  model_version: string;
  rationale_signals: string | null;
  created_at: string;
}

export interface ActionOut {
  id: number;
  action_type: string;
  channel: string | null;
  status: string;
  execution_mode: string;
  attempt_number: number;
  result: string | null;
  external_reference: string | null;
  executed_at: string | null;
  created_at: string;
}

export interface EventOut {
  id: number;
  label: string;
  detail: string | null;
  actor: string;
  icon: string | null;
  created_at: string;
}

export interface InterventionOption {
  action_type: string;
  label: string;
  success_probability: number;
  expected_value: number;
  recommended: boolean;
  is_best_value: boolean;
  note: string | null;
}

export interface CommunicationOut {
  id: number;
  channel: string;
  provider: string;
  recipient: string | null;
  subject: string | null;
  status: string;
  provider_message_id: string | null;
  payment_link: string | null;
  failure_reason: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface RecoveryCaseDetail {
  id: number;
  transaction_id: number;
  loss_type: string;
  risk_level: string;
  recovery_probability: number;
  expected_recovery_value: number;
  root_cause: string | null;
  root_cause_detail: string | null;
  recommended_action: string | null;
  recommended_channel: string | null;
  status: string;
  priority: string;
  recovered_amount: number;
  created_at: string;
  updated_at: string;
  customer: CustomerOut;
  transaction: TransactionOut;
  decisions: DecisionOut[];
  actions: ActionOut[];
  events: EventOut[];
  explainability: string[];
  intervention_options: InterventionOption[];
  communications: CommunicationOut[];
  decided_by: string | null;
  fallback_reason: string | null;
}

export interface ExecuteResult {
  result: {
    status: string;
    action?: string;
    channel?: string;
    execution_mode?: string;
    external_reference?: string | null;
    detail?: string;
    outcome?: string;
    reason?: string;
    rule?: string;
    message_body?: string | null;
  };
  case: RecoveryCaseDetail | null;
}

export interface SimulationResult {
  num_cases: number;
  revenue_at_risk: number;
  decision_engine: string;
  llm_calls: number;
  llm_successes: number;
  llm_fallbacks: number;
  ai_analyzed: number;
  recovery_attempts: number;
  recovered_cases: number;
  revenue_recovered: number;
  recovery_rate: number;
  do_nothing_count: number;
  intervention_performance: InterventionPerformance[];
  funnel: FunnelStage[];
  persisted: boolean;
  persisted_cases: number;
}

export interface AuditLogOut {
  id: number;
  recovery_case_id: number | null;
  actor: string;
  event: string;
  action: string | null;
  result: string | null;
  reason: string | null;
  input_data: string | null;
  decision_data: string | null;
  created_at: string;
}

export interface PaginatedAudit {
  total: number;
  items: AuditLogOut[];
}

export interface AppSettings {
  email: {
    connected: boolean;
    provider: string | null;
    environment: string | null;
    sender: string | null;
    reply_to: string | null;
  };
  razorpay: {
    connected: boolean;
    mode: string;
    webhook_configured: boolean;
  };
  llm: {
    connected: boolean;
    provider: string | null;
    model: string | null;
  };
}

export interface TestEmailResult {
  ok: boolean;
  status: "SENT" | "FAILED" | "BLOCKED";
  provider_message_id?: string;
  recipient?: string;
  error?: string;
}
