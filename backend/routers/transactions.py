import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from typing import Optional

from database import get_connection
from processors.registry import get_processor
from services.normalization import (
    normalize_processor_status,
    extract_raw_status,
    classify_mismatch,
    get_severity,
)

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("")
def list_transactions(
    status: Optional[str] = Query(None),
    processor: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    merchant_id: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    dateFrom: Optional[str] = Query(None),
    dateTo: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    conn = get_connection()
    conditions = []
    params = []

    if status:
        conditions.append("t.internal_status = ?")
        params.append(status)

    if processor:
        conditions.append("p.processor_name = ?")
        params.append(processor)

    if merchant_id:
        conditions.append("p.merchant_id = ?")
        params.append(merchant_id)

    if payment_method:
        conditions.append("p.payment_method = ?")
        params.append(payment_method)

    if dateFrom:
        conditions.append("t.created_at >= ?")
        params.append(dateFrom)

    if dateTo:
        conditions.append("t.created_at <= ?")
        params.append(dateTo)

    if search:
        conditions.append(
            "(t.id LIKE ? OR t.payment_id LIKE ? OR p.order_id LIKE ? OR p.merchant_name LIKE ? OR t.processor_transaction_id LIKE ?)"
        )
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * limit

    total = conn.execute(
        f"""SELECT COUNT(*) as c FROM transactions t
            JOIN payments p ON t.payment_id = p.id
            WHERE {where}""",
        params,
    ).fetchone()["c"]

    rows = conn.execute(
        f"""SELECT t.*, p.merchant_name, p.merchant_id, p.order_id, p.payment_method, p.country,
                   rr.id as rr_id, rr.severity as rr_severity, rr.mismatch_type as rr_mismatch_type,
                   rr.resolved as rr_resolved
            FROM transactions t
            JOIN payments p ON t.payment_id = p.id
            LEFT JOIN reconciliation_results rr ON rr.transaction_id = t.id AND rr.resolved = FALSE
            WHERE {where}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ).fetchall()

    transactions = []
    for row in rows:
        txn = dict(row)
        txn["has_mismatch"] = txn.pop("rr_id", None) is not None
        txn["mismatch_severity"] = txn.pop("rr_severity", None)
        txn["mismatch_type"] = txn.pop("rr_mismatch_type", None)
        txn["reconciliation_result_id"] = None
        rr_resolved = txn.pop("rr_resolved", None)
        if txn["has_mismatch"]:
            txn["reconciliation_result_id"] = row["rr_id"]
        transactions.append(txn)



    total_pages = (total + limit - 1) // limit
    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str):
    conn = get_connection()

    row = conn.execute(
        """SELECT t.*, p.merchant_name, p.merchant_id, p.order_id, p.payment_method, p.country
           FROM transactions t
           JOIN payments p ON t.payment_id = p.id
           WHERE t.id = ?""",
        (transaction_id,),
    ).fetchone()

    if row is None:
    
        return {"error": "Transaction not found"}

    txn = dict(row)

    # Get reconciliation history
    recon_history = conn.execute(
        """SELECT * FROM reconciliation_results
           WHERE transaction_id = ?
           ORDER BY created_at DESC""",
        (transaction_id,),
    ).fetchall()
    txn["reconciliation_history"] = [dict(r) for r in recon_history]

    # Parse raw response
    if txn.get("processor_raw_response"):
        try:
            txn["processor_raw_response_parsed"] = json.loads(txn["processor_raw_response"])
        except json.JSONDecodeError:
            txn["processor_raw_response_parsed"] = None


    return txn


@router.get("/{transaction_id}/live-status")
def get_live_status(transaction_id: str):
    conn = get_connection()

    row = conn.execute(
        """SELECT t.*, p.processor_name
           FROM transactions t
           JOIN payments p ON t.payment_id = p.id
           WHERE t.id = ?""",
        (transaction_id,),
    ).fetchone()

    if row is None:
    
        return {"error": "Transaction not found"}

    proc_name = row["processor_name"]
    proc_txn_id = row["processor_transaction_id"]

    processor = get_processor(proc_name)
    if processor is None:
    
        return {"error": f"Unknown processor: {proc_name}"}

    raw_response = processor.get_transaction(proc_txn_id)


    if raw_response is None:
        return {
            "transaction_id": transaction_id,
            "processor_name": proc_name,
            "processor_transaction_id": proc_txn_id,
            "raw_response": {},
            "processor_raw_status": "NOT_FOUND",
            "normalized_status": "NOT_FOUND",
            "internal_status": row["internal_status"],
            "has_mismatch": True,
            "mismatch_type": "MISSING_AT_PROCESSOR",
        }

    normalized = normalize_processor_status(proc_name, raw_response)
    raw_status = extract_raw_status(proc_name, raw_response)
    has_mismatch = normalized != row["internal_status"]
    mismatch_type = classify_mismatch(row["internal_status"], normalized) if has_mismatch else None

    return {
        "transaction_id": transaction_id,
        "processor_name": proc_name,
        "processor_transaction_id": proc_txn_id,
        "raw_response": raw_response,
        "processor_raw_status": raw_status,
        "normalized_status": normalized,
        "internal_status": row["internal_status"],
        "has_mismatch": has_mismatch,
        "mismatch_type": mismatch_type,
    }


@router.post("/{transaction_id}/reconcile")
def reconcile_transaction(transaction_id: str):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    row = conn.execute(
        """SELECT t.*, p.processor_name
           FROM transactions t
           JOIN payments p ON t.payment_id = p.id
           WHERE t.id = ?""",
        (transaction_id,),
    ).fetchone()

    if row is None:
    
        return {"error": "Transaction not found"}

    proc_name = row["processor_name"]
    proc_txn_id = row["processor_transaction_id"]
    internal_status = row["internal_status"]

    processor = get_processor(proc_name)
    if processor is None:
    
        return {"error": f"Unknown processor: {proc_name}"}

    raw_response = processor.get_transaction(proc_txn_id)

    if raw_response is None:
        mismatch_type = classify_mismatch(internal_status, "NOT_FOUND")
        severity = get_severity(mismatch_type)
        conn.execute(
            "UPDATE transactions SET internal_status = 'ERROR', updated_at = ? WHERE id = ?",
            (now, transaction_id),
        )
        conn.execute(
            "UPDATE payments SET internal_status = 'ERROR', updated_at = ? WHERE id = ?",
            (now, row["payment_id"]),
        )
        conn.commit()
    
        return {
            "transaction_id": transaction_id,
            "previous_status": internal_status,
            "new_status": "ERROR",
            "processor_status": "NOT_FOUND",
            "mismatch_type": mismatch_type,
            "severity": severity,
            "action": "ACCEPT_PROCESSOR",
            "reconciled": True,
        }

    normalized = normalize_processor_status(proc_name, raw_response)
    raw_status = extract_raw_status(proc_name, raw_response)
    has_mismatch = normalized != internal_status

    if has_mismatch:
        mismatch_type = classify_mismatch(internal_status, normalized)
        severity = get_severity(mismatch_type)

        conn.execute(
            "UPDATE transactions SET internal_status = ?, updated_at = ? WHERE id = ?",
            (normalized, now, transaction_id),
        )
        conn.execute(
            "UPDATE payments SET internal_status = ?, updated_at = ? WHERE id = ?",
            (normalized, now, row["payment_id"]),
        )

        result_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO reconciliation_results
               (id, run_id, transaction_id, internal_status, processor_raw_status,
                processor_normalized_status, mismatch_type, severity, resolved, resolved_at,
                resolution_action, created_at)
               VALUES (?, 'manual', ?, ?, ?, ?, ?, ?, TRUE, ?, 'ACCEPT_PROCESSOR', ?)""",
            (result_id, transaction_id, internal_status, raw_status, normalized,
             mismatch_type, severity, now, now),
        )
        conn.commit()
    

        return {
            "transaction_id": transaction_id,
            "previous_status": internal_status,
            "new_status": normalized,
            "processor_status": raw_status,
            "mismatch_type": mismatch_type,
            "severity": severity,
            "action": "ACCEPT_PROCESSOR",
            "reconciled": True,
        }


    return {
        "transaction_id": transaction_id,
        "previous_status": internal_status,
        "new_status": internal_status,
        "processor_status": raw_status,
        "mismatch_type": None,
        "severity": None,
        "action": None,
        "reconciled": False,
        "message": "No mismatch detected — statuses already match",
    }
