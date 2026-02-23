"""Integration tests for API endpoints."""

import os
import pytest
from fastapi.testclient import TestClient

# Use a separate test database
os.environ["CLOUDBITES_TEST"] = "1"

from database import DB_PATH, init_db, get_connection
import database


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Create a fresh database for each test."""
    test_db = str(tmp_path / "test.db")
    database.DB_PATH = test_db
    database._conn = None

    # Re-init
    conn = database.get_connection()
    conn.executescript(database.SCHEMA)
    conn.commit()

    # Seed minimal data
    conn.execute(
        """INSERT INTO payments (id, merchant_id, merchant_name, order_id, description,
           amount, currency, country, payment_method, internal_status, internal_sub_status,
           processor_name, created_at, updated_at)
           VALUES ('pay_001', 'merch_001', 'TestCo', 'ORD-001', 'Test',
                   150.00, 'USD', 'US', 'CARD', 'SUCCEEDED', 'APPROVED',
                   'PayFlow', '2026-02-20T10:00:00Z', '2026-02-20T10:00:00Z')"""
    )
    conn.execute(
        """INSERT INTO transactions (id, payment_id, type, internal_status, internal_sub_status,
           response_message, processor_name, processor_transaction_id, processor_status,
           processor_status_detail, processor_response_code, processor_raw_response,
           amount, currency, created_at, updated_at)
           VALUES ('txn_001', 'pay_001', 'PURCHASE', 'SUCCEEDED', 'APPROVED',
                   'OK', 'PayFlow', 'PF-abc123', 'Authorised', '', '', '{}',
                   150.00, 'USD', '2026-02-20T10:00:00Z', '2026-02-20T10:00:00Z')"""
    )
    conn.commit()

    # Add to processor store
    from processors.payflow import payflow_instance
    payflow_instance.add_to_store("PF-abc123", {
        "pspReference": "PF-abc123",
        "resultCode": "Authorised",
        "amount": {"value": 15000, "currency": "USD"},
    })

    yield

    database._conn = None
    database.DB_PATH = DB_PATH


@pytest.fixture
def client():
    from main import app
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestDashboardEndpoint:
    def test_stats_returns_totals(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_transactions"] >= 1
        assert "success_rate" in data
        assert "processor_breakdown" in data


class TestTransactionsEndpoint:
    def test_list_returns_paginated(self, client):
        resp = client.get("/api/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data

    def test_search_filter(self, client):
        resp = client.get("/api/transactions?search=TestCo")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_status_filter(self, client):
        resp = client.get("/api/transactions?status=SUCCEEDED")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_processor_filter(self, client):
        resp = client.get("/api/transactions?processor=PayFlow")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_transaction_found(self, client):
        resp = client.get("/api/transactions/txn_001")
        assert resp.status_code == 200
        assert resp.json()["id"] == "txn_001"
        assert "reconciliation_history" in resp.json()

    def test_get_transaction_not_found(self, client):
        resp = client.get("/api/transactions/txn_nonexistent")
        assert resp.status_code == 404

    def test_live_status(self, client):
        resp = client.get("/api/transactions/txn_001/live-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["processor_name"] == "PayFlow"
        assert "normalized_status" in data
        assert "has_mismatch" in data

    def test_live_status_not_found(self, client):
        resp = client.get("/api/transactions/txn_nonexistent/live-status")
        assert resp.status_code == 404


class TestReconciliationEndpoint:
    def test_run_reconciliation(self, client):
        resp = client.post("/api/reconciliation/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert "total_checked" in data
        assert "mismatches_found" in data

    def test_list_runs(self, client):
        client.post("/api/reconciliation/run")
        resp = client.get("/api/reconciliation/runs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_unresolved_results(self, client):
        resp = client.get("/api/reconciliation/results/unresolved")
        assert resp.status_code == 200
        assert "results" in resp.json()
        assert "total" in resp.json()

    def test_audit_log(self, client):
        resp = client.get("/api/reconciliation/audit")
        assert resp.status_code == 200
        assert "audit_log" in resp.json()


class TestReconcileTransaction:
    def test_reconcile_no_mismatch(self, client):
        resp = client.post("/api/transactions/txn_001/reconcile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reconciled"] is False
        assert "already match" in data["message"]

    def test_reconcile_not_found(self, client):
        resp = client.post("/api/transactions/txn_nonexistent/reconcile")
        assert resp.status_code == 404
