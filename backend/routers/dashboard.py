from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats():
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) as c FROM transactions").fetchone()["c"]
    succeeded = conn.execute(
        "SELECT COUNT(*) as c FROM transactions WHERE internal_status = 'SUCCEEDED'"
    ).fetchone()["c"]
    pending = conn.execute(
        "SELECT COUNT(*) as c FROM transactions WHERE internal_status = 'PENDING'"
    ).fetchone()["c"]
    total_amount = conn.execute("SELECT COALESCE(SUM(amount), 0) as s FROM transactions").fetchone()["s"]

    unresolved = conn.execute(
        "SELECT COUNT(*) as c FROM reconciliation_results WHERE resolved = FALSE"
    ).fetchone()["c"]

    processors = conn.execute("""
        SELECT p.processor_name,
               COUNT(*) as total,
               SUM(CASE WHEN t.internal_status = 'SUCCEEDED' THEN 1 ELSE 0 END) as succeeded
        FROM transactions t
        JOIN payments p ON t.payment_id = p.id
        GROUP BY p.processor_name
    """).fetchall()

    processor_breakdown = []
    for proc in processors:
        proc_mismatches = conn.execute("""
            SELECT COUNT(*) as c FROM reconciliation_results rr
            JOIN transactions t ON rr.transaction_id = t.id
            JOIN payments p ON t.payment_id = p.id
            WHERE p.processor_name = ? AND rr.resolved = FALSE
        """, (proc["processor_name"],)).fetchone()["c"]

        processor_breakdown.append({
            "name": proc["processor_name"],
            "total": proc["total"],
            "succeeded": proc["succeeded"],
            "success_rate": round(proc["succeeded"] / proc["total"] * 100, 1) if proc["total"] > 0 else 0,
            "mismatches": proc_mismatches,
        })

    statuses = conn.execute("""
        SELECT internal_status, COUNT(*) as count FROM transactions GROUP BY internal_status
    """).fetchall()
    status_breakdown = [{"status": s["internal_status"], "count": s["count"]} for s in statuses]

    recent_mismatches = conn.execute("""
        SELECT rr.*, t.processor_name, t.amount, t.currency, t.payment_id,
               p.merchant_name, p.order_id
        FROM reconciliation_results rr
        JOIN transactions t ON rr.transaction_id = t.id
        JOIN payments p ON t.payment_id = p.id
        WHERE rr.resolved = FALSE
        ORDER BY
            CASE rr.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
            rr.created_at DESC
        LIMIT 5
    """).fetchall()


    return {
        "total_transactions": total,
        "success_rate": round(succeeded / total * 100, 1) if total > 0 else 0,
        "total_mismatches": unresolved,
        "pending_transactions": pending,
        "total_amount": round(total_amount, 2),
        "processor_breakdown": processor_breakdown,
        "status_breakdown": status_breakdown,
        "recent_mismatches": [dict(m) for m in recent_mismatches],
    }
