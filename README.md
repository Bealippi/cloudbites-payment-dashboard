# CloudBites Payment Visibility Dashboard

A multi-processor payment reconciliation dashboard that detects and resolves status mismatches between CloudBites' internal database and three payment processors (PayFlow, StripeConnect, LatamPay).

## Quick Start

### Backend (Python 3.9+)
```bash
cd backend
pip3 install -r requirements.txt
python3 seed.py          # Seeds 120 transactions with 18 ghost mismatches
uvicorn main:app --reload --port 8000
```

### Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev              # Starts on http://localhost:5173
```

Open **http://localhost:5173** — the frontend proxies API calls to the backend.

## Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   React UI  │────▶│   FastAPI Backend     │────▶│  Mock Processors    │
│  (Vite+TS)  │     │   (SQLite + REST)     │     │  (In-memory stores) │
└─────────────┘     └──────────────────────┘     └─────────────────────┘
                           │                        ├── PayFlow (Adyen-like)
                           │                        ├── StripeConnect (Stripe-like)
                           ▼                        └── LatamPay (dLocal-like)
                    ┌──────────────┐
                    │   SQLite DB  │
                    │  (payments,  │
                    │ transactions,│
                    │   recon)     │
                    └──────────────┘
```

- **Backend**: FastAPI + SQLite — REST API with live processor querying and status normalization
- **Frontend**: React 18 + TypeScript + Tailwind CSS + TanStack Query
- **Mock Processors**: 3 in-process modules with structurally different response formats

## How It Works

1. **Internal DB** stores CloudBites' normalized transaction status
2. Each **mock processor** stores its own status in a fundamentally different format:
   - PayFlow: nested objects, amounts in cents, camelCase, British spelling (`Authorised`)
   - StripeConnect: flat snake_case, boolean flags, Unix timestamps
   - LatamPay: triple-status system (status + status_detail + status_code), decimal amounts
3. **Reconciliation engine** queries all 3 processors live, normalizes responses through processor-specific maps, and detects mismatches
4. **Support agents** resolve mismatches with one click (Accept Processor / Keep Internal / Ignore)

## Key Features

- **Dashboard**: KPI summary cards, per-processor health bars, recent mismatches
- **Transaction Explorer**: Full-text search, status/processor filters, paginated table with mismatch indicators
- **Transaction Detail**: Side-by-side status comparison (internal vs live processor), raw JSON viewer, reconciliation history timeline
- **Reconciliation**: One-click and bulk resolution, run history with audit trail
- **Auto-refresh**: Toggle for 30-second polling across all views
- **Severity classification**: CRITICAL (ghost charges, missing at processor) → HIGH (missed webhooks, untracked refunds) → MEDIUM (generic divergence)

## Design Decisions

- **SQLite** for zero-setup portability (single file, no Docker)
- **In-process mock processors** (not separate services) for simplicity while maintaining structural fidelity
- **Processor response formats intentionally different**: nested vs flat, cents vs decimal, camelCase vs snake_case, ISO vs Unix timestamps
- **Deterministic seed data** (`random.seed(42)`) for reproducible demos — 120 transactions, 18 deliberate ghost mismatches
- **TanStack Query** for caching, auto-refresh, and loading/error state management

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/dashboard/stats` | GET | Dashboard KPIs and breakdowns |
| `/api/transactions` | GET | Search + filter + paginate |
| `/api/transactions/{id}` | GET | Full detail with reconciliation history |
| `/api/transactions/{id}/live-status` | GET | Live processor query |
| `/api/reconciliation/run` | POST | Trigger reconciliation |
| `/api/reconciliation/runs` | GET | Past runs (audit trail) |
| `/api/reconciliation/results/unresolved` | GET | Current mismatches |
| `/api/reconciliation/results/{id}/resolve` | POST | Resolve single mismatch |
| `/api/reconciliation/results/bulk-resolve` | POST | Bulk resolve |

Swagger docs available at **http://localhost:8000/docs**
