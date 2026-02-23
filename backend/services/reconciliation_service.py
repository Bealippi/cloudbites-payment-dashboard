import uuid
from datetime import datetime, timezone

from database import get_connection
from processors.registry import get_processor
from services.normalization import (
    normalize_processor_status,
    extract_raw_status,
    classify_mismatch,
    get_severity,
)


def run_reconciliation() -> dict:
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    run_id = str(uuid.uuid4())

    conn.execute(
        "INSERT INTO reconciliation_runs (id, started_at, status) VALUES (?, ?, 'RUNNING')",
        (run_id, now),
    )
    conn.commit()

    rows = conn.execute("""
        SELECT t.id, t.internal_status, t.processor_transaction_id, p.processor_name
        FROM transactions t
        JOIN payments p ON t.payment_id = p.id
    """).fetchall()

    total_checked = 0
    mismatches_found = 0

    for row in rows:
        txn_id = row["id"]
        internal_status = row["internal_status"]
        proc_txn_id = row["processor_transaction_id"]
        proc_name = row["processor_name"]

        processor = get_processor(proc_name)
        if processor is None:
            continue

        total_checked += 1
        raw_response = processor.get_transaction(proc_txn_id)

        if raw_response is None:
            mismatches_found += 1
            result_id = str(uuid.uuid4())
            mismatch_type = classify_mismatch(internal_status, "NOT_FOUND")
            severity = get_severity(mismatch_type)
            conn.execute(
                """INSERT INTO reconciliation_results
                   (id, run_id, transaction_id, internal_status, processor_raw_status,
                    processor_normalized_status, mismatch_type, severity, resolved, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, FALSE, ?)""",
                (result_id, run_id, txn_id, internal_status, "NOT_FOUND", "NOT_FOUND",
                 mismatch_type, severity, now),
            )
            continue

        normalized = normalize_processor_status(proc_name, raw_response)
        raw_status = extract_raw_status(proc_name, raw_response)

        if normalized != internal_status:
            mismatches_found += 1
            result_id = str(uuid.uuid4())
            mismatch_type = classify_mismatch(internal_status, normalized)
            severity = get_severity(mismatch_type)
            conn.execute(
                """INSERT INTO reconciliation_results
                   (id, run_id, transaction_id, internal_status, processor_raw_status,
                    processor_normalized_status, mismatch_type, severity, resolved, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, FALSE, ?)""",
                (result_id, run_id, txn_id, internal_status, raw_status, normalized,
                 mismatch_type, severity, now),
            )

    completed_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE reconciliation_runs
           SET completed_at = ?, total_checked = ?, mismatches_found = ?, status = 'COMPLETED'
           WHERE id = ?""",
        (completed_at, total_checked, mismatches_found, run_id),
    )
    conn.commit()

    run = conn.execute("SELECT * FROM reconciliation_runs WHERE id = ?", (run_id,)).fetchone()

    return dict(run)


def resolve_mismatch(result_id: str, action: str) -> dict:
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    result = conn.execute(
        "SELECT * FROM reconciliation_results WHERE id = ?", (result_id,)
    ).fetchone()

    if result is None:
    
        return {"error": "Result not found"}

    if action == "ACCEPT_PROCESSOR":
        new_status = result["processor_normalized_status"]
        txn_id = result["transaction_id"]
        conn.execute(
            "UPDATE transactions SET internal_status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, txn_id),
        )
        payment_id = conn.execute(
            "SELECT payment_id FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()["payment_id"]
        conn.execute(
            "UPDATE payments SET internal_status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, payment_id),
        )

    conn.execute(
        """UPDATE reconciliation_results
           SET resolved = TRUE, resolved_at = ?, resolution_action = ?
           WHERE id = ?""",
        (now, action, result_id),
    )
    conn.commit()

    updated = conn.execute(
        "SELECT * FROM reconciliation_results WHERE id = ?", (result_id,)
    ).fetchone()

    return dict(updated)


def bulk_resolve(result_ids: list[str], action: str) -> list[dict]:
    results = []
    for rid in result_ids:
        r = resolve_mismatch(rid, action)
        results.append(r)
    return results


def get_runs() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reconciliation_runs ORDER BY started_at DESC"
    ).fetchall()

    return [dict(r) for r in rows]


def get_run_results(run_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT rr.*, t.processor_name, t.amount, t.currency, t.payment_id,
               p.merchant_name, p.order_id
        FROM reconciliation_results rr
        JOIN transactions t ON rr.transaction_id = t.id
        JOIN payments p ON t.payment_id = p.id
        WHERE rr.run_id = ?
        ORDER BY
            CASE rr.severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END,
            rr.created_at DESC
    """, (run_id,)).fetchall()

    return [dict(r) for r in rows]


def get_all_unresolved_results() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT rr.*, t.processor_name, t.amount, t.currency, t.payment_id,
               p.merchant_name, p.order_id
        FROM reconciliation_results rr
        JOIN transactions t ON rr.transaction_id = t.id
        JOIN payments p ON t.payment_id = p.id
        WHERE rr.resolved = FALSE
        ORDER BY
            CASE rr.severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END,
            rr.created_at DESC
    """).fetchall()

    return [dict(r) for r in rows]
