from pydantic import BaseModel
from typing import Optional


class TransactionResponse(BaseModel):
    id: str
    payment_id: str
    type: str
    internal_status: str
    internal_sub_status: str
    response_message: Optional[str] = None
    processor_name: str
    processor_transaction_id: Optional[str] = None
    processor_status: Optional[str] = None
    processor_status_detail: Optional[str] = None
    processor_response_code: Optional[str] = None
    processor_raw_response: Optional[str] = None
    amount: float
    currency: str
    created_at: str
    updated_at: str
    # Joined fields
    merchant_name: Optional[str] = None
    merchant_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_method: Optional[str] = None
    country: Optional[str] = None
    has_mismatch: Optional[bool] = False
    mismatch_severity: Optional[str] = None
    mismatch_type: Optional[str] = None
    reconciliation_result_id: Optional[str] = None


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class LiveStatusResponse(BaseModel):
    transaction_id: str
    processor_name: str
    processor_transaction_id: str
    raw_response: dict
    processor_raw_status: str
    normalized_status: str
    internal_status: str
    has_mismatch: bool
    mismatch_type: Optional[str] = None
