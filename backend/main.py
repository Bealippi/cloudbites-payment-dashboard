import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_connection, DB_PATH
from routers import dashboard, transactions, reconciliation
from processors.payflow import router as payflow_router, payflow_instance
from processors.stripeconnect import router as stripeconnect_router, stripeconnect_instance
from processors.latampay import router as latampay_router, latampay_instance


def load_processor_stores():
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.processor_transaction_id, t.processor_raw_response, p.processor_name
        FROM transactions t
        JOIN payments p ON t.payment_id = p.id
        WHERE t.processor_raw_response IS NOT NULL
    """).fetchall()


    stores = {
        "PayFlow": payflow_instance,
        "StripeConnect": stripeconnect_instance,
        "LatamPay": latampay_instance,
    }
    loaded = 0
    for row in rows:
        proc = stores.get(row["processor_name"])
        if proc and row["processor_raw_response"]:
            try:
                data = json.loads(row["processor_raw_response"])
                proc.add_to_store(row["processor_transaction_id"], data)
                loaded += 1
            except json.JSONDecodeError:
                pass
    print(f"Loaded {loaded} transactions into processor mock stores")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(DB_PATH):
        init_db()
        from seed import seed
        seed()
    load_processor_stores()
    yield


app = FastAPI(
    title="CloudBites Payment Visibility Dashboard",
    description="Multi-processor payment reconciliation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)

# Mock processor routers
app.include_router(payflow_router)
app.include_router(stripeconnect_router)
app.include_router(latampay_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "cloudbites-dashboard"}
