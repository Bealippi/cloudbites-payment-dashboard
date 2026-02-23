from typing import Optional
from fastapi import APIRouter
from .base import BaseProcessor

router = APIRouter(prefix="/mock/stripeconnect/v1", tags=["StripeConnect Mock"])

STRIPECONNECT_STATUS_MAP = {
    "succeeded": "SUCCEEDED",
    "pending": "PENDING",
    "failed": "DECLINED",
    "refunded": "REFUNDED",
    "canceled": "CANCELED",
}


class StripeConnectProcessor(BaseProcessor):
    name = "StripeConnect"

    def __init__(self):
        self.store = {}

    def get_transaction(self, processor_txn_id: str) -> Optional[dict]:
        return self.store.get(processor_txn_id)

    def extract_raw_status(self, response: dict) -> str:
        return response.get("status", "unknown")

    def normalize_status(self, response: dict) -> str:
        raw = self.extract_raw_status(response)
        return STRIPECONNECT_STATUS_MAP.get(raw, "ERROR")

    def add_to_store(self, processor_txn_id: str, data: dict):
        self.store[processor_txn_id] = data


stripeconnect_instance = StripeConnectProcessor()


@router.get("/charges/{charge_id}")
def get_stripe_charge(charge_id: str):
    data = stripeconnect_instance.store.get(charge_id)
    if data is None:
        return {"error": {"type": "invalid_request_error", "message": f"No such charge: '{charge_id}'"}}
    return data
