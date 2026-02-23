"""End-to-end smoke test: seed → reconcile → resolve → verify."""

import os
import json
import pytest

import database
from database import DB_PATH, init_db


@pytest.fixture(autouse=True)
def fresh_db_with_seed(tmp_path):
    """Create a fresh seeded database for e2e tests."""
    test_db = str(tmp_path / "e2e.db")
    database.DB_PATH = test_db
    database._conn = None

    init_db()

    from seed import seed
    seed()

    yield

    database._conn = None
    database.DB_PATH = DB_PATH


@pytest.fixture
def client():
    from main import app
    from fastapi.testclient import TestClient
    return TestClient(app, raise_server_exceptions=False)


class TestE2EReconciliation:
    """Full ghost transaction detection and resolution flow."""

    def test_full_reconciliation_flow(self, client):
        # Step 1: Run reconciliation — should detect ghost transactions
        run_resp = client.post("/api/reconciliation/run")
        assert run_resp.status_code == 200
        run = run_resp.json()
        assert run["status"] == "COMPLETED"
        assert run["total_checked"] == 120
        assert run["mismatches_found"] >= 15  # At least 15 of the 18 ghosts

        # Step 2: Check unresolved results exist
        unresolved_resp = client.get("/api/reconciliation/results/unresolved")
        assert unresolved_resp.status_code == 200
        unresolved = unresolved_resp.json()
        assert unresolved["total"] >= 15

        # Step 3: Verify mismatch types are classified correctly
        mismatch_types = {r["mismatch_type"] for r in unresolved["results"]}
        assert "CRITICAL_STATUS_MISMATCH" in mismatch_types
        assert "MISSED_WEBHOOK" in mismatch_types
        assert "MISSING_AT_PROCESSOR" in mismatch_types

        # Step 4: Verify severity classification
        severities = {r["severity"] for r in unresolved["results"]}
        assert "CRITICAL" in severities
        assert "HIGH" in severities

        # Step 5: Pick a CRITICAL mismatch and resolve it
        critical = next(r for r in unresolved["results"] if r["severity"] == "CRITICAL")
        txn_id = critical["transaction_id"]

        # Get transaction status before resolution
        txn_before = client.get(f"/api/transactions/{txn_id}").json()
        old_status = txn_before["internal_status"]

        # Resolve: accept processor as source of truth
        resolve_resp = client.post(
            f"/api/reconciliation/results/{critical['id']}/resolve",
            json={"action": "ACCEPT_PROCESSOR"},
        )
        assert resolve_resp.status_code == 200
        resolved = resolve_resp.json()
        assert resolved["resolved"] == 1  # SQLite boolean
        assert resolved["resolution_action"] == "ACCEPT_PROCESSOR"

        # Step 6: Verify internal status was actually updated
        txn_after = client.get(f"/api/transactions/{txn_id}").json()
        assert txn_after["internal_status"] != old_status

        # Step 7: Verify it appears in audit trail
        audit_resp = client.get("/api/reconciliation/audit")
        assert audit_resp.status_code == 200
        resolved_entries = [
            e for e in audit_resp.json()["audit_log"]
            if e["resolved"] and e["transaction_id"] == txn_id
        ]
        assert len(resolved_entries) >= 1

    def test_bulk_resolve(self, client):
        # Run reconciliation first
        client.post("/api/reconciliation/run")

        # Get first 3 unresolved
        unresolved = client.get("/api/reconciliation/results/unresolved").json()
        ids = [r["id"] for r in unresolved["results"][:3]]
        assert len(ids) == 3

        # Bulk resolve
        bulk_resp = client.post(
            "/api/reconciliation/results/bulk-resolve",
            json={"result_ids": ids, "action": "ACCEPT_PROCESSOR"},
        )
        assert bulk_resp.status_code == 200
        assert bulk_resp.json()["resolved"] == 3

        # Verify they're no longer unresolved
        after = client.get("/api/reconciliation/results/unresolved").json()
        remaining_ids = {r["id"] for r in after["results"]}
        for rid in ids:
            assert rid not in remaining_ids

    def test_processors_return_different_formats(self, client):
        """Verify the 3 mock processors have structurally different responses."""
        conn = database.get_connection()

        # Get one transaction per processor
        for proc_name in ["PayFlow", "StripeConnect", "LatamPay"]:
            row = conn.execute(
                """SELECT t.id FROM transactions t
                   JOIN payments p ON t.payment_id = p.id
                   WHERE p.processor_name = ? AND t.processor_raw_response IS NOT NULL
                   LIMIT 1""",
                (proc_name,),
            ).fetchone()
            assert row is not None, f"No transaction found for {proc_name}"

            resp = client.get(f"/api/transactions/{row['id']}")
            assert resp.status_code == 200
            txn = resp.json()
            raw = json.loads(txn["processor_raw_response"]) if txn.get("processor_raw_response") else None
            assert raw is not None, f"No raw response for {proc_name}"

            # Verify each processor has its unique structure
            if proc_name == "PayFlow":
                assert "pspReference" in raw  # camelCase
                assert "resultCode" in raw
                assert isinstance(raw.get("amount"), dict)  # nested {value, currency}
            elif proc_name == "StripeConnect":
                assert "status" in raw  # snake_case
                assert isinstance(raw.get("amount"), int)  # flat cents
                assert "paid" in raw  # boolean flags
            elif proc_name == "LatamPay":
                assert "status_code" in raw  # triple status system
                assert "status_detail" in raw
                assert isinstance(raw.get("amount"), float)  # major units

    def test_run_history_tracks_runs(self, client):
        # Run reconciliation twice
        client.post("/api/reconciliation/run")
        client.post("/api/reconciliation/run")

        runs = client.get("/api/reconciliation/runs").json()
        assert len(runs) >= 2
        # Most recent first
        assert runs[0]["started_at"] >= runs[1]["started_at"]
