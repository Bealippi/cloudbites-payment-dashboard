from typing import Optional
from fastapi import APIRouter
from .base import BaseProcessor

router = APIRouter(prefix="/mock/latampay/v1", tags=["LatamPay Mock"])

LATAMPAY_STATUS_MAP = {
    "200": "SUCCEEDED",
    "100": "PENDING",
    "300": "DECLINED",
    "301": "DECLINED",
    "302": "DECLINED",
    "400": "REFUNDED",
    "500": "EXPIRED",
}


class LatamPayProcessor(BaseProcessor):
    name = "LatamPay"

    def __init__(self):
        self.store = {}

    def get_transaction(self, processor_txn_id: str) -> Optional[dict]:
        return self.store.get(processor_txn_id)

    def extract_raw_status(self, response: dict) -> str:
        return response.get("status", "UNKNOWN")

    def normalize_status(self, response: dict) -> str:
        code = response.get("status_code", "999")
        return LATAMPAY_STATUS_MAP.get(str(code), "ERROR")

    def add_to_store(self, processor_txn_id: str, data: dict):
        self.store[processor_txn_id] = data


latampay_instance = LatamPayProcessor()


@router.get("/payments/{payment_id}")
def get_latampay_payment(payment_id: str):
    data = latampay_instance.store.get(payment_id)
    if data is None:
        return {"code": 5000, "message": "Payment not found", "id": payment_id}
    return data
