from pydantic import BaseModel
from typing import Optional


class ReconciliationRunResponse(BaseModel):
    id: str
    started_at: str
    completed_at: Optional[str] = None
    total_checked: int
    mismatches_found: int
    auto_resolved: int
    status: str


class ReconciliationResultResponse(BaseModel):
    id: str
    run_id: str
    transaction_id: str
    internal_status: str
    processor_raw_status: str
    processor_normalized_status: str
    mismatch_type: str
    severity: str
    resolved: bool
    resolved_at: Optional[str] = None
    resolution_action: Optional[str] = None
    created_at: str
    # Joined fields
    processor_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    merchant_name: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None


class ResolveRequest(BaseModel):
    action: str  # ACCEPT_PROCESSOR | ACCEPT_INTERNAL | IGNORED


class BulkResolveRequest(BaseModel):
    result_ids: list[str]
    action: str


class ReconciliationResultsResponse(BaseModel):
    results: list[ReconciliationResultResponse]
    total: int


class DashboardStats(BaseModel):
    total_transactions: int
    success_rate: float
    total_mismatches: int
    pending_transactions: int
    total_amount: float
    processor_breakdown: list[dict]
    status_breakdown: list[dict]
    recent_mismatches: list[ReconciliationResultResponse]
