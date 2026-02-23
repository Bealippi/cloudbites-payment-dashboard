"""Unit tests for status normalization and mismatch classification."""

import pytest
from services.normalization import (
    normalize_processor_status,
    extract_raw_status,
    classify_mismatch,
    get_severity,
)
from processors.payflow import payflow_instance
from processors.stripeconnect import stripeconnect_instance
from processors.latampay import latampay_instance


# --- PayFlow normalization ---

class TestPayFlowNormalization:
    def test_authorised_maps_to_succeeded(self):
        resp = {"resultCode": "Authorised", "amount": {"value": 10000, "currency": "USD"}}
        assert normalize_processor_status("PayFlow", resp) == "SUCCEEDED"

    def test_refused_maps_to_declined(self):
        resp = {"resultCode": "Refused", "refusalReason": "Not enough balance"}
        assert normalize_processor_status("PayFlow", resp) == "DECLINED"

    def test_pending_maps_to_pending(self):
        resp = {"resultCode": "Pending"}
        assert normalize_processor_status("PayFlow", resp) == "PENDING"

    def test_cancelled_maps_to_canceled(self):
        resp = {"resultCode": "Cancelled"}
        assert normalize_processor_status("PayFlow", resp) == "CANCELED"

    def test_refunded_maps_to_refunded(self):
        resp = {"resultCode": "Refunded"}
        assert normalize_processor_status("PayFlow", resp) == "REFUNDED"

    def test_unknown_code_maps_to_error(self):
        resp = {"resultCode": "SomethingWeird"}
        assert normalize_processor_status("PayFlow", resp) == "ERROR"

    def test_extract_raw_status(self):
        resp = {"resultCode": "Authorised"}
        assert extract_raw_status("PayFlow", resp) == "Authorised"


# --- StripeConnect normalization ---

class TestStripeConnectNormalization:
    def test_succeeded_maps_to_succeeded(self):
        resp = {"status": "succeeded", "paid": True}
        assert normalize_processor_status("StripeConnect", resp) == "SUCCEEDED"

    def test_failed_maps_to_declined(self):
        resp = {"status": "failed", "failure_code": "card_declined"}
        assert normalize_processor_status("StripeConnect", resp) == "DECLINED"

    def test_pending_maps_to_pending(self):
        resp = {"status": "pending"}
        assert normalize_processor_status("StripeConnect", resp) == "PENDING"

    def test_refunded_maps_to_refunded(self):
        resp = {"status": "refunded", "refunded": True}
        assert normalize_processor_status("StripeConnect", resp) == "REFUNDED"

    def test_extract_raw_status(self):
        resp = {"status": "failed"}
        assert extract_raw_status("StripeConnect", resp) == "failed"


# --- LatamPay normalization ---

class TestLatamPayNormalization:
    def test_status_code_200_maps_to_succeeded(self):
        resp = {"status": "PAID", "status_code": "200", "status_detail": "The payment was paid."}
        assert normalize_processor_status("LatamPay", resp) == "SUCCEEDED"

    def test_status_code_302_maps_to_declined(self):
        resp = {"status": "REJECTED", "status_code": "302"}
        assert normalize_processor_status("LatamPay", resp) == "DECLINED"

    def test_status_code_400_maps_to_refunded(self):
        resp = {"status": "REFUNDED", "status_code": "400"}
        assert normalize_processor_status("LatamPay", resp) == "REFUNDED"

    def test_status_code_500_maps_to_expired(self):
        resp = {"status": "EXPIRED", "status_code": "500"}
        assert normalize_processor_status("LatamPay", resp) == "EXPIRED"

    def test_unknown_code_maps_to_error(self):
        resp = {"status": "UNKNOWN", "status_code": "999"}
        assert normalize_processor_status("LatamPay", resp) == "ERROR"

    def test_extract_raw_status(self):
        resp = {"status": "PAID", "status_code": "200"}
        assert extract_raw_status("LatamPay", resp) == "PAID"


# --- Unknown processor ---

class TestUnknownProcessor:
    def test_unknown_processor_returns_error(self):
        assert normalize_processor_status("NonExistent", {}) == "ERROR"

    def test_unknown_processor_raw_status(self):
        assert extract_raw_status("NonExistent", {}) == "UNKNOWN"


# --- Mismatch classification ---

class TestClassifyMismatch:
    def test_not_found_is_missing_at_processor(self):
        assert classify_mismatch("SUCCEEDED", "NOT_FOUND") == "MISSING_AT_PROCESSOR"

    def test_succeeded_vs_declined_is_critical(self):
        assert classify_mismatch("SUCCEEDED", "DECLINED") == "CRITICAL_STATUS_MISMATCH"

    def test_pending_vs_succeeded_is_missed_webhook(self):
        assert classify_mismatch("PENDING", "SUCCEEDED") == "MISSED_WEBHOOK"

    def test_pending_vs_authorized_is_missed_webhook(self):
        assert classify_mismatch("PENDING", "AUTHORIZED") == "MISSED_WEBHOOK"

    def test_succeeded_vs_refunded_is_untracked_refund(self):
        assert classify_mismatch("SUCCEEDED", "REFUNDED") == "UNTRACKED_REFUND"

    def test_authorized_vs_canceled_is_status_mismatch(self):
        assert classify_mismatch("AUTHORIZED", "CANCELED") == "STATUS_MISMATCH"

    def test_generic_mismatch(self):
        assert classify_mismatch("PENDING", "ERROR") == "STATUS_MISMATCH"


# --- Severity ---

class TestSeverity:
    def test_critical_mismatch_severity(self):
        assert get_severity("CRITICAL_STATUS_MISMATCH") == "CRITICAL"

    def test_missing_at_processor_severity(self):
        assert get_severity("MISSING_AT_PROCESSOR") == "CRITICAL"

    def test_missed_webhook_severity(self):
        assert get_severity("MISSED_WEBHOOK") == "HIGH"

    def test_untracked_refund_severity(self):
        assert get_severity("UNTRACKED_REFUND") == "HIGH"

    def test_amount_mismatch_severity(self):
        assert get_severity("AMOUNT_MISMATCH") == "CRITICAL"

    def test_status_mismatch_severity(self):
        assert get_severity("STATUS_MISMATCH") == "MEDIUM"

    def test_unknown_type_severity(self):
        assert get_severity("SOMETHING_ELSE") == "LOW"


# --- Processor store operations ---

class TestProcessorStores:
    def test_payflow_store_roundtrip(self):
        data = {"pspReference": "PF-test123", "resultCode": "Authorised"}
        payflow_instance.add_to_store("PF-test123", data)
        assert payflow_instance.get_transaction("PF-test123") == data
        assert payflow_instance.get_transaction("PF-nonexistent") is None

    def test_stripe_store_roundtrip(self):
        data = {"id": "ch_test456", "status": "succeeded"}
        stripeconnect_instance.add_to_store("ch_test456", data)
        assert stripeconnect_instance.get_transaction("ch_test456") == data
        assert stripeconnect_instance.get_transaction("ch_nonexistent") is None

    def test_latampay_store_roundtrip(self):
        data = {"id": "LP-PAY-7890", "status": "PAID", "status_code": "200"}
        latampay_instance.add_to_store("LP-PAY-7890", data)
        assert latampay_instance.get_transaction("LP-PAY-7890") == data
        assert latampay_instance.get_transaction("LP-PAY-nonexistent") is None
