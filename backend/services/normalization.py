from processors.payflow import PAYFLOW_STATUS_MAP
from processors.stripeconnect import STRIPECONNECT_STATUS_MAP
from processors.latampay import LATAMPAY_STATUS_MAP


def normalize_processor_status(processor_name: str, raw_response: dict) -> str:
    if processor_name == "PayFlow":
        raw = raw_response.get("resultCode", "Unknown")
        return PAYFLOW_STATUS_MAP.get(raw, "ERROR")
    elif processor_name == "StripeConnect":
        raw = raw_response.get("status", "unknown")
        return STRIPECONNECT_STATUS_MAP.get(raw, "ERROR")
    elif processor_name == "LatamPay":
        code = str(raw_response.get("status_code", "999"))
        return LATAMPAY_STATUS_MAP.get(code, "ERROR")
    return "ERROR"


def extract_raw_status(processor_name: str, raw_response: dict) -> str:
    if processor_name == "PayFlow":
        return raw_response.get("resultCode", "Unknown")
    elif processor_name == "StripeConnect":
        return raw_response.get("status", "unknown")
    elif processor_name == "LatamPay":
        return raw_response.get("status", "UNKNOWN")
    return "UNKNOWN"


def classify_mismatch(internal: str, processor: str) -> str:
    if processor == "NOT_FOUND":
        return "MISSING_AT_PROCESSOR"
    if internal == "SUCCEEDED" and processor == "DECLINED":
        return "CRITICAL_STATUS_MISMATCH"
    if internal == "PENDING" and processor in ("SUCCEEDED", "AUTHORIZED"):
        return "MISSED_WEBHOOK"
    if internal == "SUCCEEDED" and processor == "REFUNDED":
        return "UNTRACKED_REFUND"
    if internal == "AUTHORIZED" and processor in ("CANCELED", "DECLINED"):
        return "STATUS_MISMATCH"
    return "STATUS_MISMATCH"


SEVERITY_MAP = {
    "CRITICAL_STATUS_MISMATCH": "CRITICAL",
    "MISSING_AT_PROCESSOR": "CRITICAL",
    "MISSED_WEBHOOK": "HIGH",
    "UNTRACKED_REFUND": "HIGH",
    "STATUS_MISMATCH": "MEDIUM",
}


def get_severity(mismatch_type: str) -> str:
    return SEVERITY_MAP.get(mismatch_type, "LOW")
