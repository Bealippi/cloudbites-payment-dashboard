from pydantic import BaseModel
from typing import Optional


class PaymentResponse(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str
    order_id: str
    description: Optional[str] = None
    amount: float
    currency: str
    country: str
    payment_method: str
    internal_status: str
    internal_sub_status: str
    processor_name: str
    created_at: str
    updated_at: str
