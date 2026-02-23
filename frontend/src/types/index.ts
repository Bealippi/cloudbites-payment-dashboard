export interface Transaction {
  id: string;
  payment_id: string;
  type: string;
  internal_status: string;
  internal_sub_status: string;
  response_message: string | null;
  processor_name: string;
  processor_transaction_id: string | null;
  processor_status: string | null;
  processor_status_detail: string | null;
  processor_response_code: string | null;
  processor_raw_response: string | null;
  processor_raw_response_parsed?: Record<string, unknown> | null;
  amount: number;
  currency: string;
  created_at: string;
  updated_at: string;
  merchant_name?: string;
  merchant_id?: string;
  order_id?: string;
  payment_method?: string;
  country?: string;
  has_mismatch?: boolean;
  mismatch_severity?: string | null;
  mismatch_type?: string | null;
  reconciliation_result_id?: string | null;
  reconciliation_history?: ReconciliationResult[];
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface LiveStatusResponse {
  transaction_id: string;
  processor_name: string;
  processor_transaction_id: string;
  raw_response: Record<string, unknown>;
  processor_raw_status: string;
  normalized_status: string;
  internal_status: string;
  has_mismatch: boolean;
  mismatch_type: string | null;
}

export interface ReconciliationRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  total_checked: number;
  mismatches_found: number;
  auto_resolved: number;
  status: string;
}

export interface ReconciliationResult {
  id: string;
  run_id: string;
  transaction_id: string;
  internal_status: string;
  processor_raw_status: string;
  processor_normalized_status: string;
  mismatch_type: string;
  severity: string;
  resolved: boolean;
  resolved_at: string | null;
  resolution_action: string | null;
  created_at: string;
  processor_name?: string;
  amount?: number;
  currency?: string;
  merchant_name?: string;
  order_id?: string;
  payment_id?: string;
}

export interface DashboardStats {
  total_transactions: number;
  success_rate: number;
  total_mismatches: number;
  pending_transactions: number;
  total_amount: number;
  processor_breakdown: ProcessorBreakdown[];
  status_breakdown: StatusBreakdown[];
  recent_mismatches: ReconciliationResult[];
}

export interface ProcessorBreakdown {
  name: string;
  total: number;
  succeeded: number;
  success_rate: number;
  mismatches: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
}

export interface TransactionFilters {
  status?: string;
  processor?: string;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  page: number;
  limit: number;
}

export interface ReconcileResponse {
  transaction_id: string;
  previous_status: string;
  new_status: string;
  processor_status: string;
  mismatch_type: string | null;
  severity: string | null;
  action: string | null;
  reconciled: boolean;
  message?: string;
}
