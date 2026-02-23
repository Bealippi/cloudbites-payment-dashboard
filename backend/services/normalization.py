from processors.registry import get_processor


def normalize_processor_status(processor_name: str, raw_response: dict) -> str:
    """Delegates to processor's own normalize_status method — single source of truth."""
    processor = get_processor(processor_name)
    if processor is None:
        return "ERROR"
    return processor.normalize_status(raw_response)


def extract_raw_status(processor_name: str, raw_response: dict) -> str:
    """Delegates to processor's own extract_raw_status method."""
    processor = get_processor(processor_name)
    if processor is None:
        return "UNKNOWN"
    return processor.extract_raw_status(raw_response)


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
    "AMOUNT_MISMATCH": "CRITICAL",
    "STATUS_MISMATCH": "MEDIUM",
}


def get_severity(mismatch_type: str) -> str:
    return SEVERITY_MAP.get(mismatch_type, "LOW")
