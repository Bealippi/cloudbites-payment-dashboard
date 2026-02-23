from typing import Optional
from fastapi import APIRouter
from .base import BaseProcessor

router = APIRouter(prefix="/mock/payflow/v1", tags=["PayFlow Mock"])

PAYFLOW_STATUS_MAP = {
    "Authorised": "SUCCEEDED",
    "Refused": "DECLINED",
    "Pending": "PENDING",
    "Received": "PENDING",
    "Cancelled": "CANCELED",
    "Error": "ERROR",
    "RedirectShopper": "PENDING",
    "ChallengeShopper": "PENDING",
    "Refunded": "REFUNDED",
}


class PayFlowProcessor(BaseProcessor):
    name = "PayFlow"

    def __init__(self):
        self.store = {}

    def get_transaction(self, processor_txn_id: str) -> Optional[dict]:
        return self.store.get(processor_txn_id)

    def extract_raw_status(self, response: dict) -> str:
        return response.get("resultCode", "Unknown")

    def normalize_status(self, response: dict) -> str:
        raw = self.extract_raw_status(response)
        return PAYFLOW_STATUS_MAP.get(raw, "ERROR")

    def add_to_store(self, processor_txn_id: str, data: dict):
        self.store[processor_txn_id] = data


payflow_instance = PayFlowProcessor()


@router.get("/payments/{psp_reference}")
def get_payflow_payment(psp_reference: str):
    data = payflow_instance.store.get(psp_reference)
    if data is None:
        return {"status": 404, "message": "Payment not found", "pspReference": psp_reference}
    return data
