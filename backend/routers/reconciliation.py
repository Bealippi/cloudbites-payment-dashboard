from fastapi import APIRouter

from database import get_connection
from models.reconciliation import ResolveRequest, BulkResolveRequest
from services.reconciliation_service import (
    run_reconciliation,
    resolve_mismatch,
    bulk_resolve,
    get_runs,
    get_run_results,
    get_all_unresolved_results,
)

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])


@router.post("/run")
def trigger_reconciliation():
    result = run_reconciliation()
    return result


@router.get("/runs")
def list_runs():
    return get_runs()


@router.get("/runs/{run_id}/results")
def list_run_results(run_id: str):
    results = get_run_results(run_id)
    return {"results": results, "total": len(results)}


@router.get("/results/unresolved")
def list_unresolved_results():
    results = get_all_unresolved_results()
    return {"results": results, "total": len(results)}


@router.post("/results/{result_id}/resolve")
def resolve_result(result_id: str, body: ResolveRequest):
    return resolve_mismatch(result_id, body.action)


@router.post("/results/bulk-resolve")
def bulk_resolve_results(body: BulkResolveRequest):
    results = bulk_resolve(body.result_ids, body.action)
    return {"resolved": len(results), "results": results}


@router.get("/audit")
def get_audit_log():
    conn = get_connection()
    rows = conn.execute("""
        SELECT rr.*, t.processor_name, t.amount, t.currency, t.payment_id,
               p.merchant_name, p.order_id
        FROM reconciliation_results rr
        JOIN transactions t ON rr.transaction_id = t.id
        JOIN payments p ON t.payment_id = p.id
        ORDER BY rr.created_at DESC
    """).fetchall()

    return {"audit_log": [dict(r) for r in rows], "total": len(rows)}
