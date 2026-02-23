import sqlite3
import os
import threading

DB_PATH = os.path.join(os.path.dirname(__file__), "cloudbites.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    order_id TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    country TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    internal_status TEXT NOT NULL,
    internal_sub_status TEXT NOT NULL,
    processor_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL REFERENCES payments(id),
    type TEXT NOT NULL,
    internal_status TEXT NOT NULL,
    internal_sub_status TEXT NOT NULL,
    response_message TEXT,
    processor_name TEXT NOT NULL,
    processor_transaction_id TEXT,
    processor_status TEXT,
    processor_status_detail TEXT,
    processor_response_code TEXT,
    processor_raw_response TEXT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliation_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    total_checked INTEGER DEFAULT 0,
    mismatches_found INTEGER DEFAULT 0,
    auto_resolved INTEGER DEFAULT 0,
    status TEXT DEFAULT 'RUNNING'
);

CREATE TABLE IF NOT EXISTS reconciliation_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    internal_status TEXT NOT NULL,
    processor_raw_status TEXT NOT NULL,
    processor_normalized_status TEXT NOT NULL,
    mismatch_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TEXT,
    resolution_action TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(internal_status);
CREATE INDEX IF NOT EXISTS idx_payments_processor ON payments(processor_name);
CREATE INDEX IF NOT EXISTS idx_payments_merchant ON payments(merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_payment ON transactions(payment_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(internal_status);
CREATE INDEX IF NOT EXISTS idx_recon_results_run ON reconciliation_results(run_id);
CREATE INDEX IF NOT EXISTS idx_recon_results_resolved ON reconciliation_results(resolved);
"""

_lock = threading.Lock()
_conn = None


def get_connection() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        try:
            _conn.execute("SELECT 1")
        except Exception:
            _conn = None
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=OFF")
    return _conn


def get_lock():
    return _lock


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
