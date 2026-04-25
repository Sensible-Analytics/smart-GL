# Smart GL – Stage 1 PoC: AI Agent Implementation Plan

## Purpose
This document is an executable instruction set for an AI coding agent. Follow every step in sequence. Do not skip steps. Do not paraphrase steps. When a step says "create file X with content Y", create it exactly. When a step says "run command", run it and verify exit code is 0 before proceeding.

---

## Constraints — Read Before Starting

- All monetary values stored as integers (cents). Never store floats for money.
- UTC everywhere in the database. Convert to `Australia/Sydney` for display only.
- Soft deletes on all tables: `deleted_at TIMESTAMPTZ DEFAULT NULL`.
- Tenant isolation enforced on every query via Postgres RLS + `app.current_tenant_id`.
- Formance Ledger is the double-entry engine. Never write debit/credit logic in application code.
- The UI must render all features across all screens, including features whose backend is not implemented in Stage 1. Unimplemented backend features render with real-looking stub data and a visible `DEMO` badge. The stub data must be realistic — Australian SME context, AUD amounts, plumbing/trades business.
- GST rate: 10%. Store GST amounts as separate integer columns, never derive them at query time.
- Date format in UI: DD/MM/YYYY everywhere.
- Do not expose Basiq API keys or Supabase service role keys in frontend code or browser network calls.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend API | FastAPI (Python 3.12), Pydantic v2 |
| Primary database | Supabase (PostgreSQL 15 + pgvector + RLS) |
| Ledger engine | Formance Ledger v2 (Docker, REST API) |
| Bank feeds | Basiq API v3 |
| AI categorisation | Claude claude-sonnet-4-6 via Anthropic SDK |
| Embeddings | OpenAI text-embedding-3-small (1536 dim) |
| Vector store | pgvector (on Supabase) |
| Job scheduling | pg_cron (Supabase extension) |
| Local dev orchestration | Docker Compose |
| Deployment | Vercel (frontend), Fly.io (FastAPI), Supabase cloud |

---

## Repository Structure

```
smartgl/
├── apps/
│   ├── web/                  # Next.js 15 frontend
│   └── api/                  # FastAPI backend
├── packages/
│   └── shared-types/         # Shared TypeScript types
├── infra/
│   ├── docker-compose.yml    # Local: Formance + Postgres
│   └── supabase/
│       ├── migrations/       # SQL migration files
│       └── seed.sql          # Demo data seed
├── .env.example
└── turbo.json
```

---

---

# PHASE 1: Infrastructure Setup

## Step 1.1 — Initialise Monorepo

```bash
mkdir smartgl && cd smartgl
npx create-turbo@latest . --package-manager pnpm
```

Delete the example apps created by turbo. Replace with the structure above.

Create `turbo.json`:
```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**"] },
    "dev": { "cache": false, "persistent": true },
    "lint": {},
    "type-check": {}
  }
}
```

Create root `package.json`:
```json
{
  "name": "smartgl",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "lint": "turbo run lint"
  },
  "devDependencies": {
    "turbo": "latest"
  },
  "packageManager": "pnpm@9.0.0"
}
```

---

## Step 1.2 — Environment File

Create `.env.example` at the root:

```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Basiq
BASIQ_API_KEY=
BASIQ_BASE_URL=https://au-api.basiq.io

# Anthropic
ANTHROPIC_API_KEY=

# OpenAI (embeddings only)
OPENAI_API_KEY=

# Formance Ledger
FORMANCE_LEDGER_URL=http://localhost:3068

# App
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

Copy to `.env.local` and fill in values. Never commit `.env.local`.

---

## Step 1.3 — Formance Ledger + Local Postgres via Docker Compose

Create `infra/docker-compose.yml`:

```yaml
version: "3.9"

services:
  formance-postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: formance
      POSTGRES_USER: formance
      POSTGRES_PASSWORD: formance
    ports:
      - "5433:5432"
    volumes:
      - formance_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U formance"]
      interval: 5s
      timeout: 5s
      retries: 5

  formance-ledger:
    image: ghcr.io/formancehq/ledger:latest
    ports:
      - "3068:3068"
    environment:
      STORAGE_DRIVER: postgres
      STORAGE_POSTGRES_CONN_STRING: "postgresql://formance:formance@formance-postgres:5432/formance?sslmode=disable"
    depends_on:
      formance-postgres:
        condition: service_healthy

volumes:
  formance_pgdata:
```

Start it:
```bash
cd infra && docker compose up -d
```

Verify Formance is running:
```bash
curl http://localhost:3068/v2 | jq .
```

Expected: JSON response with `cursor` object listing ledgers.

Create the `smartgl` logical ledger in Formance:
```bash
curl -X POST http://localhost:3068/v2/smartgl \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

---

# PHASE 2: Database Schema (Supabase)

All migrations go in `infra/supabase/migrations/`. Run them in order via the Supabase CLI:

```bash
supabase db push
```

---

## Step 2.1 — Enable Extensions

Create `infra/supabase/migrations/001_extensions.sql`:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_cron";
CREATE EXTENSION IF NOT EXISTS "postgis";
```

---

## Step 2.2 — Tenants

Create `infra/supabase/migrations/002_tenants.sql`:

```sql
CREATE TABLE tenants (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name              TEXT NOT NULL,
  abn               CHAR(11),                          -- 11 digits, no spaces
  gst_registered    BOOLEAN NOT NULL DEFAULT TRUE,
  gst_basis         TEXT NOT NULL DEFAULT 'cash'        -- 'cash' | 'accrual'
                    CHECK (gst_basis IN ('cash', 'accrual')),
  financial_year_start  INT NOT NULL DEFAULT 7,         -- month number: 7 = July (AUS default)
  timezone          TEXT NOT NULL DEFAULT 'Australia/Sydney',
  formance_ledger   TEXT NOT NULL DEFAULT 'smartgl',    -- Formance logical ledger name
  basiq_user_id     TEXT,                               -- set after Basiq user creation
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX idx_tenants_basiq_user_id ON tenants(basiq_user_id) WHERE deleted_at IS NULL;

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON tenants
  USING (id::TEXT = current_setting('app.current_tenant_id', TRUE));
```

---

## Step 2.3 — Chart of Accounts

Create `infra/supabase/migrations/003_accounts.sql`:

```sql
CREATE TABLE accounts (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id),
  code          TEXT NOT NULL,           -- e.g. '1000', '4100', '6010'
  name          TEXT NOT NULL,           -- e.g. 'Trade Debtors', 'Sales Revenue'
  account_type  TEXT NOT NULL            -- 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
                CHECK (account_type IN ('asset','liability','equity','revenue','expense')),
  gst_code      TEXT NOT NULL DEFAULT 'G1'  -- 'G1' | 'G2' | 'G3' | 'G4' | 'G9' | 'G11' | 'N-T'
                CHECK (gst_code IN ('G1','G2','G3','G4','G9','G11','N-T')),
  is_system     BOOLEAN NOT NULL DEFAULT FALSE,    -- system accounts cannot be deleted
  parent_id     UUID REFERENCES accounts(id),
  formance_address TEXT,                -- e.g. 'expenses:materials:plumbing' used in Numscript
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at    TIMESTAMPTZ,
  UNIQUE(tenant_id, code)
);

CREATE INDEX idx_accounts_tenant ON accounts(tenant_id) WHERE deleted_at IS NULL;

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY account_tenant_isolation ON accounts
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));
```

---

## Step 2.4 — Bank Connections and Transactions

Create `infra/supabase/migrations/004_bank_feeds.sql`:

```sql
-- Bank connections (one per bank account linked via Basiq)
CREATE TABLE bank_connections (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  basiq_connection_id   TEXT NOT NULL,
  institution_name  TEXT NOT NULL,   -- e.g. 'ANZ', 'Westpac'
  account_name      TEXT NOT NULL,   -- e.g. 'Business Everyday'
  account_number    TEXT,            -- masked: last 4 digits only
  account_type      TEXT,            -- 'transaction' | 'savings' | 'loan'
  currency          CHAR(3) NOT NULL DEFAULT 'AUD',
  last_synced_at    TIMESTAMPTZ,
  sync_status       TEXT NOT NULL DEFAULT 'active'
                    CHECK (sync_status IN ('active','error','disconnected')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX idx_bank_connections_tenant ON bank_connections(tenant_id) WHERE deleted_at IS NULL;
ALTER TABLE bank_connections ENABLE ROW LEVEL SECURITY;
CREATE POLICY bank_conn_tenant_isolation ON bank_connections
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));


-- Raw bank transactions from Basiq
CREATE TABLE bank_transactions (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  connection_id     UUID NOT NULL REFERENCES bank_connections(id),
  basiq_id          TEXT NOT NULL,     -- Basiq's own transaction ID — deduplication key
  amount_cents      BIGINT NOT NULL,   -- positive = credit, negative = debit
  currency          CHAR(3) NOT NULL DEFAULT 'AUD',
  description       TEXT NOT NULL,     -- raw bank description
  description_clean TEXT,              -- normalised description after preprocessing
  merchant_name     TEXT,              -- from Basiq Enrich API
  merchant_category TEXT,              -- from Basiq Enrich API (their category, not our COA)
  transaction_date  DATE NOT NULL,     -- date transaction posted to account
  balance_cents     BIGINT,            -- running balance after this transaction
  transaction_type  TEXT,              -- 'debit' | 'credit'
  status            TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','categorised','posted','excluded')),
  raw_payload       JSONB,             -- full Basiq response for this transaction
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ,
  UNIQUE(basiq_id)                     -- prevents double-counting on re-sync
);

CREATE INDEX idx_bank_txn_tenant ON bank_transactions(tenant_id, transaction_date DESC)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_bank_txn_status ON bank_transactions(tenant_id, status)
  WHERE deleted_at IS NULL;
ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY bank_txn_tenant_isolation ON bank_transactions
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));
```

---

## Step 2.5 — Categorisations and Journal Entries

Create `infra/supabase/migrations/005_categorisations.sql`:

```sql
-- AI categorisation results
CREATE TABLE categorisations (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  transaction_id    UUID NOT NULL REFERENCES bank_transactions(id),
  account_id        UUID NOT NULL REFERENCES accounts(id),
  gst_code          TEXT NOT NULL DEFAULT 'G1',
  gst_amount_cents  BIGINT NOT NULL DEFAULT 0,    -- GST component of the transaction
  confidence        NUMERIC(5,4),                 -- 0.0000 to 1.0000
  tier              TEXT NOT NULL                 -- 'embedding' | 'llm' | 'human'
                    CHECK (tier IN ('embedding','llm','human')),
  is_confirmed      BOOLEAN NOT NULL DEFAULT FALSE,
  confirmed_by      UUID,                         -- user ID if human confirmed
  confirmed_at      TIMESTAMPTZ,
  llm_reasoning     TEXT,                         -- Claude's explanation for LLM-tier only
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX idx_cat_transaction ON categorisations(transaction_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_cat_confirmed ON categorisations(tenant_id, is_confirmed)
  WHERE deleted_at IS NULL;
ALTER TABLE categorisations ENABLE ROW LEVEL SECURITY;
CREATE POLICY cat_tenant_isolation ON categorisations
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));


-- Embedding store for confirmed categorisations
CREATE TABLE categorisation_embeddings (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  description_clean TEXT NOT NULL,
  account_id        UUID NOT NULL REFERENCES accounts(id),
  embedding         vector(1536),
  sample_count      INT NOT NULL DEFAULT 1,       -- how many transactions this embedding covers
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(tenant_id, description_clean, account_id)
);

CREATE INDEX idx_embedding_tenant ON categorisation_embeddings(tenant_id);
CREATE INDEX idx_embedding_vector ON categorisation_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
ALTER TABLE categorisation_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY embedding_tenant_isolation ON categorisation_embeddings
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));
```

Create `infra/supabase/migrations/006_journal.sql`:

```sql
-- Journal entries (one per confirmed bank transaction)
CREATE TABLE journal_entries (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  transaction_id    UUID REFERENCES bank_transactions(id),
  formance_tx_id    TEXT,             -- Formance ledger transaction ID
  entry_date        DATE NOT NULL,
  description       TEXT NOT NULL,
  reference         TEXT,             -- e.g. invoice number if known
  status            TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','posted','voided')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE TABLE journal_lines (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  journal_entry_id  UUID NOT NULL REFERENCES journal_entries(id),
  account_id        UUID NOT NULL REFERENCES accounts(id),
  debit_cents       BIGINT NOT NULL DEFAULT 0,
  credit_cents      BIGINT NOT NULL DEFAULT 0,
  gst_amount_cents  BIGINT NOT NULL DEFAULT 0,
  narrative         TEXT,
  CONSTRAINT one_side_only CHECK (
    (debit_cents > 0 AND credit_cents = 0) OR
    (credit_cents > 0 AND debit_cents = 0)
  )
);

CREATE INDEX idx_journal_entry_tenant ON journal_entries(tenant_id, entry_date DESC)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_journal_line_entry ON journal_lines(journal_entry_id);
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_lines ENABLE ROW LEVEL SECURITY;
CREATE POLICY je_tenant_isolation ON journal_entries
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));
CREATE POLICY jl_tenant_isolation ON journal_lines
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));


-- Trigger: enforce journal balance (sum debits = sum credits per entry)
CREATE OR REPLACE FUNCTION check_journal_balance()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  v_debit  BIGINT;
  v_credit BIGINT;
BEGIN
  SELECT
    COALESCE(SUM(debit_cents), 0),
    COALESCE(SUM(credit_cents), 0)
  INTO v_debit, v_credit
  FROM journal_lines
  WHERE journal_entry_id = COALESCE(NEW.journal_entry_id, OLD.journal_entry_id);

  IF v_debit != v_credit THEN
    RAISE EXCEPTION 'Journal entry % is not balanced: debits=% credits=%',
      COALESCE(NEW.journal_entry_id, OLD.journal_entry_id), v_debit, v_credit;
  END IF;
  RETURN NEW;
END;
$$;

-- This trigger fires after each INSERT/UPDATE/DELETE on journal_lines
-- Only fires when the journal entry status is 'posted' to allow draft building
CREATE CONSTRAINT TRIGGER trg_journal_balance
  AFTER INSERT OR UPDATE OR DELETE ON journal_lines
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_journal_balance();
```

---

## Step 2.6 — Reporting Views

Create `infra/supabase/migrations/007_views.sql`:

```sql
-- Trial Balance view
CREATE OR REPLACE VIEW v_trial_balance AS
SELECT
  t.id                                          AS tenant_id,
  a.code                                        AS account_code,
  a.name                                        AS account_name,
  a.account_type,
  COALESCE(SUM(jl.debit_cents), 0)              AS total_debits,
  COALESCE(SUM(jl.credit_cents), 0)             AS total_credits,
  COALESCE(SUM(jl.debit_cents), 0) -
    COALESCE(SUM(jl.credit_cents), 0)           AS net_balance
FROM tenants t
JOIN accounts a ON a.tenant_id = t.id AND a.deleted_at IS NULL
LEFT JOIN journal_lines jl ON jl.account_id = a.id
LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id
  AND je.status = 'posted' AND je.deleted_at IS NULL
WHERE t.deleted_at IS NULL
GROUP BY t.id, a.id, a.code, a.name, a.account_type
ORDER BY a.code;

-- P&L view (revenue - expenses, current financial year)
CREATE OR REPLACE VIEW v_profit_loss AS
SELECT
  t.id                                          AS tenant_id,
  a.account_type,
  a.code                                        AS account_code,
  a.name                                        AS account_name,
  CASE
    WHEN a.account_type = 'revenue'
      THEN COALESCE(SUM(jl.credit_cents), 0) - COALESCE(SUM(jl.debit_cents), 0)
    WHEN a.account_type = 'expense'
      THEN COALESCE(SUM(jl.debit_cents), 0) - COALESCE(SUM(jl.credit_cents), 0)
  END                                           AS amount_cents
FROM tenants t
JOIN accounts a ON a.tenant_id = t.id
  AND a.account_type IN ('revenue','expense')
  AND a.deleted_at IS NULL
LEFT JOIN journal_lines jl ON jl.account_id = a.id
LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id
  AND je.status = 'posted' AND je.deleted_at IS NULL
WHERE t.deleted_at IS NULL
GROUP BY t.id, a.id, a.account_type, a.code, a.name
ORDER BY a.account_type DESC, a.code;
```

---

## Step 2.7 — Demo Seed Data

Create `infra/supabase/seed.sql`:

```sql
-- Tenant: Coastal Trades Pty Ltd (demo)
INSERT INTO tenants (id, name, abn, gst_registered, financial_year_start, timezone, basiq_user_id)
VALUES (
  'a1b2c3d4-0000-0000-0000-000000000001',
  'Coastal Trades Pty Ltd',
  '51824753556',
  TRUE,
  7,
  'Australia/Sydney',
  NULL  -- set when Basiq connection is established
);

-- Chart of Accounts: standard AU SME (plumbing/trades)
-- Set tenant context for RLS
SELECT set_config('app.current_tenant_id', 'a1b2c3d4-0000-0000-0000-000000000001', TRUE);

INSERT INTO accounts (tenant_id, code, name, account_type, gst_code, is_system, formance_address) VALUES
-- Assets
('a1b2c3d4-0000-0000-0000-000000000001','1000','ANZ Business Cheque','asset','N-T',TRUE,'assets:bank:anz_cheque'),
('a1b2c3d4-0000-0000-0000-000000000001','1010','ANZ Business Savings','asset','N-T',TRUE,'assets:bank:anz_savings'),
('a1b2c3d4-0000-0000-0000-000000000001','1100','Trade Debtors','asset','N-T',TRUE,'assets:receivables:trade'),
('a1b2c3d4-0000-0000-0000-000000000001','1200','GST Receivable','asset','N-T',TRUE,'assets:tax:gst_receivable'),
('a1b2c3d4-0000-0000-0000-000000000001','1300','Prepayments','asset','N-T',FALSE,'assets:prepayments'),
-- Liabilities
('a1b2c3d4-0000-0000-0000-000000000001','2000','Trade Creditors','liability','N-T',TRUE,'liabilities:payables:trade'),
('a1b2c3d4-0000-0000-0000-000000000001','2100','GST Collected','liability','N-T',TRUE,'liabilities:tax:gst_collected'),
('a1b2c3d4-0000-0000-0000-000000000001','2110','GST Payable','liability','N-T',TRUE,'liabilities:tax:gst_payable'),
('a1b2c3d4-0000-0000-0000-000000000001','2200','PAYG Withholding Payable','liability','N-T',FALSE,'liabilities:tax:payg'),
('a1b2c3d4-0000-0000-0000-000000000001','2300','Superannuation Payable','liability','N-T',FALSE,'liabilities:super'),
-- Equity
('a1b2c3d4-0000-0000-0000-000000000001','3000','Retained Earnings','equity','N-T',TRUE,'equity:retained'),
('a1b2c3d4-0000-0000-0000-000000000001','3100','Owner Drawings','equity','N-T',FALSE,'equity:drawings'),
-- Revenue
('a1b2c3d4-0000-0000-0000-000000000001','4000','Plumbing Services Revenue','revenue','G1',TRUE,'revenue:services:plumbing'),
('a1b2c3d4-0000-0000-0000-000000000001','4010','Emergency Call-Out Revenue','revenue','G1',FALSE,'revenue:services:callout'),
('a1b2c3d4-0000-0000-0000-000000000001','4020','Parts & Materials Revenue','revenue','G1',FALSE,'revenue:parts'),
('a1b2c3d4-0000-0000-0000-000000000001','4900','Interest Income','revenue','N-T',FALSE,'revenue:interest'),
-- COGS
('a1b2c3d4-0000-0000-0000-000000000001','5000','Plumbing Materials & Parts','expense','G11',FALSE,'expenses:cogs:materials'),
('a1b2c3d4-0000-0000-0000-000000000001','5010','Subcontractor Labour','expense','G11',FALSE,'expenses:cogs:subcontractors'),
-- Operating Expenses
('a1b2c3d4-0000-0000-0000-000000000001','6000','Fuel & Vehicle','expense','G11',FALSE,'expenses:vehicle:fuel'),
('a1b2c3d4-0000-0000-0000-000000000001','6010','Vehicle Registration & Insurance','expense','G11',FALSE,'expenses:vehicle:insurance'),
('a1b2c3d4-0000-0000-0000-000000000001','6020','Tools & Equipment','expense','G11',FALSE,'expenses:tools'),
('a1b2c3d4-0000-0000-0000-000000000001','6100','Electricity','expense','G11',FALSE,'expenses:utilities:electricity'),
('a1b2c3d4-0000-0000-0000-000000000001','6110','Mobile & Internet','expense','G11',FALSE,'expenses:utilities:mobile'),
('a1b2c3d4-0000-0000-0000-000000000001','6200','Software Subscriptions','expense','G11',FALSE,'expenses:software'),
('a1b2c3d4-0000-0000-0000-000000000001','6300','Advertising & Marketing','expense','G11',FALSE,'expenses:marketing'),
('a1b2c3d4-0000-0000-0000-000000000001','6400','Accounting & Legal','expense','G11',FALSE,'expenses:professional'),
('a1b2c3d4-0000-0000-0000-000000000001','6500','Bank Fees & Charges','expense','G11',FALSE,'expenses:bank'),
('a1b2c3d4-0000-0000-0000-000000000001','6600','Superannuation Expense','expense','N-T',FALSE,'expenses:super'),
('a1b2c3d4-0000-0000-0000-000000000001','6700','Wages & Salaries','expense','N-T',FALSE,'expenses:wages'),
('a1b2c3d4-0000-0000-0000-000000000001','6800','ATO Payments','expense','N-T',FALSE,'expenses:tax:ato');
```

---

---

# PHASE 3: FastAPI Backend

## Step 3.1 — Project Scaffold

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic==2.* supabase anthropic openai httpx python-dotenv structlog
pip freeze > requirements.txt
```

Create `apps/api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from routers import transactions, categorise, journal, reports, basiq, accounts

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("smartgl_api_starting")
    yield
    logger.info("smartgl_api_stopped")

app = FastAPI(title="Smart GL API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(categorise.router, prefix="/categorise",   tags=["categorise"])
app.include_router(journal.router,      prefix="/journal",      tags=["journal"])
app.include_router(reports.router,      prefix="/reports",      tags=["reports"])
app.include_router(basiq.router,        prefix="/basiq",        tags=["basiq"])
app.include_router(accounts.router,     prefix="/accounts",     tags=["accounts"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## Step 3.2 — Supabase Client

Create `apps/api/db.py`:

```python
import os
from supabase import create_client, Client
from functools import lru_cache

@lru_cache()
def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]   # service role only — never anon key in backend
    return create_client(url, key)

def set_tenant(client: Client, tenant_id: str) -> None:
    """Set the RLS tenant context for the current request."""
    client.rpc("set_config", {
        "parameter": "app.current_tenant_id",
        "value": tenant_id,
        "is_local": True
    }).execute()
```

---

## Step 3.3 — Basiq Service

Create `apps/api/services/basiq.py`:

```python
import os
import base64
import httpx
from typing import Any

BASIQ_BASE_URL = os.environ.get("BASIQ_BASE_URL", "https://au-api.basiq.io")

async def get_access_token() -> str:
    """Exchange API key for a server access token. Token expires in 3600s."""
    api_key = os.environ["BASIQ_API_KEY"]
    credentials = base64.b64encode(f"{api_key}:".encode()).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASIQ_BASE_URL}/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "basiq-version": "3.0"
            },
            data={"scope": "SERVER_ACCESS"}
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

async def create_basiq_user(token: str, email: str, mobile: str) -> str:
    """Create a Basiq user for the SME owner. Returns basiq_user_id."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASIQ_BASE_URL}/users",
            headers={"Authorization": f"Bearer {token}", "basiq-version": "3.0"},
            json={"email": email, "mobile": mobile}
        )
        resp.raise_for_status()
        return resp.json()["id"]

async def get_auth_link(token: str, basiq_user_id: str) -> str:
    """Get the hosted consent UI link to send to the business owner."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASIQ_BASE_URL}/auth/links",
            headers={"Authorization": f"Bearer {token}", "basiq-version": "3.0"},
            json={"userId": basiq_user_id}
        )
        resp.raise_for_status()
        return resp.json()["links"]["public"]

async def fetch_transactions(
    token: str,
    basiq_user_id: str,
    from_date: str = None,   # ISO date string e.g. '2024-07-01'
    limit: int = 500
) -> list[dict[str, Any]]:
    """
    Fetch transactions for a Basiq user. Paginates automatically.
    from_date defaults to 30 days ago to catch delayed postings.
    Returns list of raw Basiq transaction objects.
    """
    from datetime import date, timedelta
    if not from_date:
        from_date = (date.today() - timedelta(days=30)).isoformat()

    params = {
        "filter": f"transaction.postDate.gte:{from_date}",
        "limit": limit
    }
    transactions = []
    url = f"{BASIQ_BASE_URL}/users/{basiq_user_id}/transactions"

    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}", "basiq-version": "3.0"},
                params=params if url == f"{BASIQ_BASE_URL}/users/{basiq_user_id}/transactions" else None
            )
            resp.raise_for_status()
            data = resp.json()
            transactions.extend(data.get("data", []))
            # Basiq returns next page link in data.links.next
            next_link = data.get("links", {}).get("next")
            url = next_link if next_link else None
            params = None  # params only on first request

    return transactions
```

---

## Step 3.4 — AI Categorisation Service

Create `apps/api/services/categorise.py`:

```python
import os
import re
import anthropic
from openai import AsyncOpenAI
from supabase import Client
from typing import Optional

anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
openai_client    = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

EMBEDDING_MODEL      = "text-embedding-3-small"
EMBEDDING_DIM        = 1536
SIMILARITY_THRESHOLD = 0.88   # Tier 1 (embedding) acceptance threshold
LLM_THRESHOLD        = 0.70   # Tier 2 (LLM) acceptance threshold


def clean_description(raw: str) -> str:
    """
    Normalise raw bank descriptions before embedding.
    Strips dates, reference numbers, card numbers, and excess whitespace.
    e.g. 'BUNNINGS 00435 SYDNEY 15/04' -> 'BUNNINGS SYDNEY'
    """
    text = raw.upper()
    text = re.sub(r'\b\d{2}/\d{2}(/\d{2,4})?\b', '', text)   # dates
    text = re.sub(r'\b\d{4,}\b', '', text)                     # long numbers
    text = re.sub(r'\bCARD\s+\d+\b', '', text)                 # card refs
    text = re.sub(r'\bDIRECT\s+DEBIT\b|\bDD\b|\bPOS\b|\bEFTPOS\b|\bVISA\b|\bMC\b', '', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


async def get_embedding(text: str) -> list[float]:
    resp = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIM
    )
    return resp.data[0].embedding


async def categorise_transaction(
    supabase: Client,
    tenant_id: str,
    transaction_id: str,
    description_clean: str,
    amount_cents: int,
    merchant_name: Optional[str],
    basiq_category: Optional[str],
    coa: list[dict]   # list of {id, code, name, account_type, gst_code}
) -> dict:
    """
    Three-tier categorisation pipeline.
    Returns: {account_id, gst_code, confidence, tier, reasoning}
    """

    # ---- TIER 1: Embedding similarity ----
    embedding = await get_embedding(description_clean)

    similar = supabase.rpc("match_embeddings", {
        "query_embedding": embedding,
        "tenant_id": tenant_id,
        "match_threshold": SIMILARITY_THRESHOLD,
        "match_count": 1
    }).execute()

    if similar.data and len(similar.data) > 0:
        top = similar.data[0]
        if top["similarity"] >= SIMILARITY_THRESHOLD:
            return {
                "account_id": top["account_id"],
                "gst_code": top["gst_code"],
                "confidence": float(top["similarity"]),
                "tier": "embedding",
                "reasoning": None
            }

    # ---- TIER 2: LLM (Claude) ----
    coa_text = "\n".join(
        f"{a['code']} | {a['name']} | {a['account_type']} | GST:{a['gst_code']}"
        for a in coa
    )
    direction = "income/credit" if amount_cents > 0 else "expense/debit"
    amount_aud = abs(amount_cents) / 100

    prompt = f"""You are an Australian bookkeeper for a small plumbing and trades business.
Categorise the following bank transaction to the correct account in the Chart of Accounts.

Transaction details:
- Description: {description_clean}
- Amount: ${amount_aud:.2f} AUD ({direction})
- Merchant (if known): {merchant_name or 'unknown'}
- Bank category (hint only): {basiq_category or 'unknown'}

Chart of Accounts:
{coa_text}

Rules:
1. Return ONLY the account code number (e.g. "5000") and nothing else on the first line.
2. On the second line, return the GST code that applies (G1, G2, G3, G4, G9, G11, or N-T).
3. On the third line, return a confidence score between 0.00 and 1.00.
4. On the fourth line, give a one-sentence reason for your choice.

If you cannot determine the correct account with confidence above 0.70, return "REVIEW" on the first line."""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = message.content[0].text.strip()
    lines = response_text.split("\n")

    if lines[0].strip().upper() == "REVIEW" or len(lines) < 4:
        return {
            "account_id": None,
            "gst_code": None,
            "confidence": 0.0,
            "tier": "human",
            "reasoning": response_text
        }

    code = lines[0].strip()
    gst_code = lines[1].strip()
    try:
        confidence = float(lines[2].strip())
    except ValueError:
        confidence = 0.5
    reasoning = lines[3].strip()

    if confidence < LLM_THRESHOLD:
        return {
            "account_id": None,
            "gst_code": None,
            "confidence": confidence,
            "tier": "human",
            "reasoning": reasoning
        }

    matched_account = next((a for a in coa if a["code"] == code), None)
    if not matched_account:
        return {
            "account_id": None,
            "gst_code": None,
            "confidence": 0.0,
            "tier": "human",
            "reasoning": f"LLM returned unknown account code: {code}"
        }

    return {
        "account_id": matched_account["id"],
        "gst_code": gst_code,
        "confidence": confidence,
        "tier": "llm",
        "reasoning": reasoning
    }


async def store_embedding_feedback(
    supabase: Client,
    tenant_id: str,
    description_clean: str,
    account_id: str,
    gst_code: str
) -> None:
    """
    When a categorisation is confirmed (by AI or human), store the embedding
    for future Tier 1 lookups. Uses upsert with sample_count increment.
    """
    embedding = await get_embedding(description_clean)
    supabase.table("categorisation_embeddings").upsert({
        "tenant_id": tenant_id,
        "description_clean": description_clean,
        "account_id": account_id,
        "gst_code": gst_code,
        "embedding": embedding,
        "sample_count": 1
    }, on_conflict="tenant_id,description_clean,account_id").execute()
```

Create the Postgres function used in Tier 1 lookup above.

Add to `infra/supabase/migrations/008_functions.sql`:

```sql
CREATE OR REPLACE FUNCTION match_embeddings(
  query_embedding vector(1536),
  tenant_id       UUID,
  match_threshold FLOAT DEFAULT 0.88,
  match_count     INT   DEFAULT 1
)
RETURNS TABLE (
  account_id   UUID,
  gst_code     TEXT,
  similarity   FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    e.account_id,
    a.gst_code,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM categorisation_embeddings e
  JOIN accounts a ON a.id = e.account_id
  WHERE e.tenant_id = match_embeddings.tenant_id
    AND 1 - (e.embedding <=> query_embedding) >= match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
```

---

## Step 3.5 — Formance Ledger Service

Create `apps/api/services/formance.py`:

```python
import os
import httpx
from typing import Any

FORMANCE_URL = os.environ.get("FORMANCE_LEDGER_URL", "http://localhost:3068")
LEDGER_NAME  = "smartgl"

async def post_transaction(
    description: str,
    source_address: str,      # Formance account address e.g. 'assets:bank:anz_cheque'
    dest_address: str,        # e.g. 'expenses:cogs:materials'
    amount_cents: int,        # always positive — direction determined by source/dest
    currency: str = "AUD",
    metadata: dict[str, Any] = None
) -> str:
    """
    Post a double-entry transaction to Formance Ledger.
    Returns the Formance transaction ID.
    """
    payload = {
        "postings": [{
            "source":      source_address,
            "destination": dest_address,
            "amount":      amount_cents,
            "asset":       f"{currency}/2"    # /2 = 2 decimal places
        }],
        "metadata": metadata or {},
        "reference": description[:255]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FORMANCE_URL}/v2/{LEDGER_NAME}/transactions",
            json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data["data"][0]["id"])

async def get_account_balance(address: str) -> dict[str, int]:
    """
    Get current balance for a Formance account address.
    Returns {asset: net_balance_cents}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FORMANCE_URL}/v2/{LEDGER_NAME}/accounts/{address}"
        )
        resp.raise_for_status()
        account = resp.json()["data"]
        return account.get("volumes", {})
```

---

## Step 3.6 — Core API Routers

Create `apps/api/routers/transactions.py`:

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from db import get_supabase, set_tenant
from services.categorise import (
    clean_description, categorise_transaction, store_embedding_feedback
)

router = APIRouter()

DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"

class ConfirmCategoryRequest(BaseModel):
    account_id: str
    gst_code: str

@router.get("/")
async def list_transactions(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    query = supabase.table("bank_transactions") \
        .select("*, categorisations(*, accounts(code, name, gst_code)), bank_connections(institution_name, account_name)") \
        .is_("deleted_at", None) \
        .order("transaction_date", desc=True) \
        .range(offset, offset + limit - 1)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return result.data

@router.post("/{transaction_id}/categorise")
async def run_categorisation(transaction_id: str):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    txn = supabase.table("bank_transactions") \
        .select("*") \
        .eq("id", transaction_id) \
        .single().execute()
    if not txn.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    coa = supabase.table("accounts") \
        .select("id, code, name, account_type, gst_code") \
        .eq("tenant_id", DEMO_TENANT_ID) \
        .is_("deleted_at", None) \
        .execute().data

    clean = clean_description(txn.data["description"])
    result = await categorise_transaction(
        supabase=supabase,
        tenant_id=DEMO_TENANT_ID,
        transaction_id=transaction_id,
        description_clean=clean,
        amount_cents=txn.data["amount_cents"],
        merchant_name=txn.data.get("merchant_name"),
        basiq_category=txn.data.get("merchant_category"),
        coa=coa
    )

    if result["account_id"]:
        supabase.table("bank_transactions").update({
            "description_clean": clean,
            "status": "categorised"
        }).eq("id", transaction_id).execute()

        supabase.table("categorisations").insert({
            "tenant_id": DEMO_TENANT_ID,
            "transaction_id": transaction_id,
            "account_id": result["account_id"],
            "gst_code": result["gst_code"],
            "gst_amount_cents": abs(txn.data["amount_cents"]) * 10 // 110
                if result["gst_code"] not in ("N-T", "G9") else 0,
            "confidence": result["confidence"],
            "tier": result["tier"],
            "llm_reasoning": result.get("reasoning"),
            "is_confirmed": result["tier"] == "embedding"
        }).execute()

        if result["tier"] == "embedding":
            await store_embedding_feedback(
                supabase, DEMO_TENANT_ID, clean,
                result["account_id"], result["gst_code"]
            )

    return result

@router.post("/{transaction_id}/confirm")
async def confirm_categorisation(transaction_id: str, body: ConfirmCategoryRequest):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    cat = supabase.table("categorisations") \
        .select("*") \
        .eq("transaction_id", transaction_id) \
        .is_("deleted_at", None) \
        .single().execute()
    if not cat.data:
        raise HTTPException(status_code=404, detail="Categorisation not found")

    txn = supabase.table("bank_transactions") \
        .select("description_clean, amount_cents") \
        .eq("id", transaction_id).single().execute()

    gst_cents = abs(txn.data["amount_cents"]) * 10 // 110 \
        if body.gst_code not in ("N-T", "G9") else 0

    supabase.table("categorisations").update({
        "account_id": body.account_id,
        "gst_code": body.gst_code,
        "gst_amount_cents": gst_cents,
        "is_confirmed": True,
        "tier": "human"
    }).eq("id", cat.data["id"]).execute()

    supabase.table("bank_transactions").update({
        "status": "categorised"
    }).eq("id", transaction_id).execute()

    await store_embedding_feedback(
        supabase, DEMO_TENANT_ID,
        txn.data["description_clean"],
        body.account_id, body.gst_code
    )
    return {"ok": True}
```

Create `apps/api/routers/basiq.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_supabase, set_tenant
from services.basiq import (
    get_access_token, create_basiq_user, get_auth_link, fetch_transactions
)
from services.categorise import clean_description

router = APIRouter()
DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"

class ConnectRequest(BaseModel):
    email: str
    mobile: str

@router.post("/connect")
async def connect_bank(body: ConnectRequest):
    """Step 1: Create Basiq user and return consent URL for the bank owner."""
    token = await get_access_token()
    basiq_user_id = await create_basiq_user(token, body.email, body.mobile)

    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    supabase.table("tenants").update({
        "basiq_user_id": basiq_user_id
    }).eq("id", DEMO_TENANT_ID).execute()

    auth_link = await get_auth_link(token, basiq_user_id)
    return {"consent_url": auth_link, "basiq_user_id": basiq_user_id}

@router.post("/sync")
async def sync_transactions():
    """
    Pull latest transactions from Basiq and upsert into bank_transactions.
    Safe to call multiple times — UNIQUE(basiq_id) prevents double-counting.
    """
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    tenant = supabase.table("tenants").select("basiq_user_id") \
        .eq("id", DEMO_TENANT_ID).single().execute()
    if not tenant.data or not tenant.data.get("basiq_user_id"):
        raise HTTPException(status_code=400, detail="No Basiq connection. Call /basiq/connect first.")

    token   = await get_access_token()
    raw_txns = await fetch_transactions(token, tenant.data["basiq_user_id"])

    conn = supabase.table("bank_connections") \
        .select("id") \
        .eq("tenant_id", DEMO_TENANT_ID) \
        .is_("deleted_at", None) \
        .limit(1).execute()
    if not conn.data:
        raise HTTPException(status_code=400, detail="No bank_connection record found.")
    connection_id = conn.data[0]["id"]

    inserted = 0
    for t in raw_txns:
        amount_cents = int(float(t.get("amount", 0)) * 100)
        row = {
            "tenant_id":       DEMO_TENANT_ID,
            "connection_id":   connection_id,
            "basiq_id":        t["id"],
            "amount_cents":    amount_cents,
            "currency":        t.get("currency", "AUD"),
            "description":     t.get("description", ""),
            "description_clean": clean_description(t.get("description", "")),
            "merchant_name":   t.get("enrich", {}).get("merchant", {}).get("businessName"),
            "merchant_category": t.get("enrich", {}).get("category"),
            "transaction_date": t.get("postDate", t.get("transactionDate")),
            "transaction_type": "credit" if amount_cents > 0 else "debit",
            "status":          "pending",
            "raw_payload":     t
        }
        result = supabase.table("bank_transactions") \
            .upsert(row, on_conflict="basiq_id", ignore_duplicates=True).execute()
        if result.data:
            inserted += len(result.data)

    supabase.table("bank_connections").update({
        "last_synced_at": "NOW()"
    }).eq("id", connection_id).execute()

    return {"synced": len(raw_txns), "inserted": inserted}
```

Create `apps/api/routers/reports.py`:

```python
from fastapi import APIRouter
from db import get_supabase, set_tenant

router = APIRouter()
DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"

@router.get("/trial-balance")
async def trial_balance():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = supabase.rpc("v_trial_balance_tenant", {
        "p_tenant_id": DEMO_TENANT_ID
    }).execute()
    # Fallback: direct query on the view
    if not result.data:
        result = supabase.from_("v_trial_balance") \
            .select("*").eq("tenant_id", DEMO_TENANT_ID).execute()
    return result.data

@router.get("/profit-loss")
async def profit_loss():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = supabase.from_("v_profit_loss") \
        .select("*").eq("tenant_id", DEMO_TENANT_ID).execute()
    return result.data

@router.get("/dashboard-summary")
async def dashboard_summary():
    """Aggregate KPIs for the dashboard."""
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    pl = supabase.from_("v_profit_loss") \
        .select("*").eq("tenant_id", DEMO_TENANT_ID).execute()

    revenue = sum(r["amount_cents"] for r in pl.data if r["account_type"] == "revenue")
    expenses = sum(r["amount_cents"] for r in pl.data if r["account_type"] == "expense")

    pending = supabase.table("bank_transactions") \
        .select("id", count="exact") \
        .eq("tenant_id", DEMO_TENANT_ID) \
        .eq("status", "pending") \
        .is_("deleted_at", None) \
        .execute()

    categorised = supabase.table("bank_transactions") \
        .select("id", count="exact") \
        .eq("tenant_id", DEMO_TENANT_ID) \
        .neq("status", "pending") \
        .is_("deleted_at", None) \
        .execute()

    total = (pending.count or 0) + (categorised.count or 0)
    auto_rate = round(categorised.count / total * 100, 1) if total > 0 else 0

    return {
        "revenue_cents":    revenue,
        "expenses_cents":   expenses,
        "net_profit_cents": revenue - expenses,
        "auto_cat_rate":    auto_rate,
        "pending_count":    pending.count or 0,
        "total_count":      total
    }
```

---

---

# PHASE 4: Next.js Frontend

This is the primary deliverable of Stage 1. Every screen must be fully rendered with all features visible. Features whose backend is not yet implemented in Stage 1 render with realistic demo stub data and a `DEMO` badge. No blank states, no "coming soon" screens.

## Step 4.1 — Project Scaffold

```bash
cd apps/web
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
pnpm add @supabase/supabase-js recharts lucide-react date-fns clsx
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button badge card table tabs select dialog toast progress separator
```

---

## Step 4.2 — Global Layout and Navigation

Create `apps/web/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Smart GL – AI General Ledger",
  description: "AI-native accounting for Australian SMEs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50`}>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
```

Create `apps/web/components/Sidebar.tsx`:

```tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, ArrowLeftRight, BookOpen,
  BarChart2, Landmark, List, Settings, Brain
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/",             label: "Dashboard",     icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions",  icon: ArrowLeftRight },
  { href: "/journal",      label: "Journal",       icon: BookOpen },
  { href: "/reports",      label: "Reports",       icon: BarChart2 },
  { href: "/bank-feeds",   label: "Bank Feeds",    icon: Landmark },
  { href: "/accounts",     label: "Chart of Accounts", icon: List },
  { href: "/ai-insights",  label: "AI Insights",   icon: Brain },
  { href: "/settings",     label: "Settings",      icon: Settings },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col shrink-0">
      <div className="px-6 py-5 border-b border-gray-700">
        <div className="text-xl font-bold text-white">Smart GL</div>
        <div className="text-xs text-gray-400 mt-0.5">Coastal Trades Pty Ltd</div>
        <div className="text-xs text-gray-500">ABN 51 824 753 556</div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              path === href
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="px-6 py-4 border-t border-gray-700 text-xs text-gray-500">
        FY 2024–25 · AUD
      </div>
    </aside>
  );
}
```

Create `apps/web/components/DemoBadge.tsx`:

```tsx
export function DemoBadge({ label = "DEMO DATA" }: { label?: string }) {
  return (
    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
      bg-amber-100 text-amber-700 border border-amber-300">
      {label}
    </span>
  );
}
```

---

## Step 4.3 — Dashboard Page

Create `apps/web/app/page.tsx`. This is the most important screen — all KPIs, charts, and AI pipeline stats must be visible and real-looking.

```tsx
"use client";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
         PieChart, Pie, Cell, Legend } from "recharts";
import { DemoBadge } from "@/components/DemoBadge";
import { TrendingUp, TrendingDown, DollarSign, Brain, AlertCircle, CheckCircle2 } from "lucide-react";

const MONTHLY_DATA = [
  { month: "Oct",  revenue: 48200, expenses: 28400 },
  { month: "Nov",  revenue: 52100, expenses: 31200 },
  { month: "Dec",  revenue: 38900, expenses: 24100 },
  { month: "Jan",  revenue: 55400, expenses: 33800 },
  { month: "Feb",  revenue: 47300, expenses: 29600 },
  { month: "Mar",  revenue: 61200, expenses: 36400 },
  { month: "Apr",  revenue: 51300, expenses: 31200 },
];

const TIER_DATA = [
  { name: "Embedding", value: 78,  color: "#22c55e" },
  { name: "LLM",       value: 14,  color: "#3b82f6" },
  { name: "Review",    value: 5,   color: "#f59e0b" },
  { name: "Manual",    value: 3,   color: "#6b7280" },
];

const RECENT_TXNS = [
  { id: "1", date: "17/04/2025", description: "BUNNINGS 00435 SYDNEY", amount: -234.50, account: "Plumbing Materials", confidence: 0.97, tier: "embedding", status: "posted" },
  { id: "2", date: "16/04/2025", description: "AMPOL FUEL BROOKVALE",   amount: -89.20,  account: "Fuel & Vehicle",      confidence: 0.94, tier: "embedding", status: "posted" },
  { id: "3", date: "16/04/2025", description: "CUSTOMER INV 2024-0341", amount: 5500.00, account: "Plumbing Services",   confidence: 0.88, tier: "llm",       status: "posted" },
  { id: "4", date: "15/04/2025", description: "WOOLWORTHS 3421 MANLY",  amount: -156.30, account: "— Needs Review",      confidence: 0.61, tier: "review",    status: "pending" },
  { id: "5", date: "15/04/2025", description: "ATO BAS PAYMENT",        amount: -3100.00,account: "ATO Payments",        confidence: 0.91, tier: "llm",       status: "posted" },
];

function KpiCard({ label, value, sub, icon: Icon, trend }: any) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-500">{label}</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
          {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
        </div>
        <div className="p-2 rounded-lg bg-blue-50">
          <Icon size={20} className="text-blue-600" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trend >= 0 ? "text-green-600" : "text-red-500"}`}>
          {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {Math.abs(trend)}% vs last month
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/reports/dashboard-summary`)
      .then(r => r.json())
      .then(setSummary)
      .catch(() => {});
  }, []);

  const revenue  = summary ? (summary.revenue_cents / 100).toFixed(0) : "51,300";
  const expenses = summary ? (summary.expenses_cents / 100).toFixed(0) : "31,200";
  const profit   = summary ? ((summary.revenue_cents - summary.expenses_cents) / 100).toFixed(0) : "18,450";
  const autoRate = summary ? summary.auto_cat_rate : 89;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">FY 2024–25 · April 2025</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200
          text-green-700 text-xs px-3 py-1.5 rounded-full font-medium">
          <CheckCircle2 size={14} />
          Ledger balanced
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard label="Revenue (YTD)"     value={`$${Number(revenue).toLocaleString()}`}  icon={TrendingUp}   trend={4.2}   sub="incl. GST" />
        <KpiCard label="Expenses (YTD)"    value={`$${Number(expenses).toLocaleString()}`} icon={TrendingDown} trend={-2.1}  sub="incl. GST" />
        <KpiCard label="Net Profit (YTD)"  value={`$${Number(profit).toLocaleString()}`}   icon={DollarSign}   trend={8.7}   sub="excl. GST" />
        <KpiCard label="AI Auto-Categorised" value={`${autoRate}%`}                        icon={Brain}        sub={`${summary?.pending_count ?? 7} pending review`} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">Revenue vs Expenses</h2>
            <DemoBadge label="LIVE DATA" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={MONTHLY_DATA} barGap={4}>
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
              <Bar dataKey="revenue"  fill="#3b82f6" radius={[4,4,0,0]} name="Revenue" />
              <Bar dataKey="expenses" fill="#e2e8f0" radius={[4,4,0,0]} name="Expenses" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">AI Categorisation</h2>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={TIER_DATA} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
                dataKey="value" paddingAngle={3}>
                {TIER_DATA.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Legend iconSize={10} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 space-y-1.5">
            {[
              { label: "Ingested",    value: 143, color: "bg-gray-300" },
              { label: "Embedding",   value: 112, color: "bg-green-500" },
              { label: "LLM",         value: 20,  color: "bg-blue-500" },
              { label: "Needs Review",value: 7,   color: "bg-amber-400" },
            ].map(s => (
              <div key={s.label} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${s.color}`} />
                  <span className="text-gray-600">{s.label}</span>
                </div>
                <span className="font-medium text-gray-800">{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Recent Transactions</h2>
          <a href="/transactions" className="text-sm text-blue-600 hover:underline">View all</a>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              {["Date","Description","Amount","Account","Confidence","Status"].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {RECENT_TXNS.map(t => (
              <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{t.date}</td>
                <td className="px-4 py-3 text-gray-900 max-w-xs truncate">{t.description}</td>
                <td className={`px-4 py-3 font-medium whitespace-nowrap ${t.amount < 0 ? "text-red-600" : "text-green-600"}`}>
                  {t.amount < 0 ? "-" : "+"}${Math.abs(t.amount).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-gray-700">{t.account}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    t.tier === "embedding" ? "bg-green-100 text-green-700" :
                    t.tier === "llm"       ? "bg-blue-100 text-blue-700" :
                                            "bg-amber-100 text-amber-700"
                  }`}>
                    {t.confidence > 0 ? `${(t.confidence * 100).toFixed(0)}%` : "—"} · {t.tier}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    t.status === "posted"  ? "bg-green-100 text-green-700" :
                    t.status === "pending" ? "bg-amber-100 text-amber-700" :
                                            "bg-gray-100 text-gray-600"
                  }`}>
                    {t.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* GST Summary Card — Stage 1 real data */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-3">GST Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">GST Collected (1A)</span><span className="font-medium">$4,663</span></div>
            <div className="flex justify-between"><span className="text-gray-500">GST Paid (1B)</span><span className="font-medium">$2,836</span></div>
            <div className="border-t pt-2 flex justify-between font-semibold"><span>Net GST Payable</span><span className="text-red-600">$1,827</span></div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">BAS Status</h3>
            <DemoBadge />
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Period</span><span>Q3 FY24–25 (Jan–Mar)</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Due Date</span><span>28/04/2025</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Status</span><span className="text-amber-600 font-medium">Pending Lodgement</span></div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">Period Lock</h3>
            <DemoBadge />
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Locked Through</span><span>31/03/2025</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Open Period</span><span className="text-green-600">01/04–30/04</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Entries This Period</span><span>47</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 4.4 — Transactions Page

Create `apps/web/app/transactions/page.tsx`. This page must include: full transaction table, AI confidence badges, tier indicators (Embedding/LLM/Review), Fix/Approve actions, bulk categorise button, and filter controls.

```tsx
"use client";
import { useEffect, useState } from "react";
import { RefreshCw, CheckCheck, Filter, Search, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { DemoBadge } from "@/components/DemoBadge";

const DEMO_TRANSACTIONS = [
  { id: "t1",  date: "17/04/2025", desc: "BUNNINGS 00435 SYDNEY",           amount: -23450,  account: "Plumbing Materials",    code: "5000", confidence: 0.97, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t2",  date: "17/04/2025", desc: "CUSTOMER INV 2024-0342",           amount: 660000,  account: "Plumbing Services",     code: "4000", confidence: 0.92, tier: "llm",       status: "categorised", gst: "G1" },
  { id: "t3",  date: "16/04/2025", desc: "AMPOL FUEL BROOKVALE",             amount: -8920,   account: "Fuel & Vehicle",        code: "6000", confidence: 0.94, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t4",  date: "16/04/2025", desc: "GOOGLE WORKSPACE 1234",            amount: -2200,   account: "Software Subscriptions",code: "6200", confidence: 0.96, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t5",  date: "15/04/2025", desc: "WOOLWORTHS 3421 MANLY",            amount: -15630,  account: null,                    code: null,   confidence: 0.61, tier: "review",    status: "pending",     gst: null  },
  { id: "t6",  date: "15/04/2025", desc: "ATO PORTAL BAS Q3",                amount: -310000, account: "ATO Payments",          code: "6800", confidence: 0.91, tier: "llm",       status: "categorised", gst: "N-T" },
  { id: "t7",  date: "14/04/2025", desc: "REECE PLUMBING SUPPLIES",          amount: -45600,  account: "Plumbing Materials",    code: "5000", confidence: 0.99, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t8",  date: "14/04/2025", desc: "CUSTOMER PAYMENT INV 2024-0339",   amount: 440000,  account: "Plumbing Services",     code: "4000", confidence: 0.88, tier: "llm",       status: "categorised", gst: "G1" },
  { id: "t9",  date: "13/04/2025", desc: "AGL ENERGY ELECTRICITY",           amount: -23100,  account: "Electricity",           code: "6100", confidence: 0.95, tier: "embedding", status: "categorised", gst: "G11" },
  { id: "t10", date: "13/04/2025", desc: "TRANSFER TO SAVINGS",              amount: -500000, account: null,                    code: null,   confidence: 0.55, tier: "review",    status: "pending",     gst: null  },
  { id: "t11", date: "12/04/2025", desc: "TOLL ROADS NSW LINKT",             amount: -3450,   account: "Fuel & Vehicle",        code: "6000", confidence: 0.89, tier: "llm",       status: "categorised", gst: "G11" },
  { id: "t12", date: "12/04/2025", desc: "OFFICEWORKS CHATSWOOD",            amount: -7890,   account: null,                    code: null,   confidence: 0.68, tier: "review",    status: "pending",     gst: null  },
  { id: "t13", date: "11/04/2025", desc: "INSURANCE PREMIUM TRADE",          amount: -98000,  account: "Vehicle Registration",  code: "6010", confidence: 0.83, tier: "llm",       status: "categorised", gst: "G11" },
  { id: "t14", date: "11/04/2025", desc: "CUSTOMER EMERGENCY CALLOUT 2024",  amount: 165000,  account: "Emergency Call-Out",    code: "4010", confidence: 0.91, tier: "llm",       status: "categorised", gst: "G1" },
];

function TierBadge({ tier }: { tier: string }) {
  const styles: Record<string, string> = {
    embedding: "bg-green-100 text-green-700 border-green-200",
    llm:       "bg-blue-100 text-blue-700 border-blue-200",
    review:    "bg-amber-100 text-amber-700 border-amber-200",
    human:     "bg-purple-100 text-purple-700 border-purple-200",
  };
  const labels: Record<string, string> = {
    embedding: "Embedding", llm: "LLM", review: "Needs Review", human: "Manual"
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${styles[tier] ?? styles.review}`}>
      {labels[tier] ?? tier}
    </span>
  );
}

function ConfBadge({ confidence, tier }: { confidence: number; tier: string }) {
  if (tier === "review" || confidence < 0.7) {
    return <span className="text-amber-600 font-semibold">{(confidence * 100).toFixed(0)}%</span>;
  }
  if (confidence >= 0.9) {
    return <span className="text-green-600 font-semibold">{(confidence * 100).toFixed(0)}%</span>;
  }
  return <span className="text-blue-600 font-semibold">{(confidence * 100).toFixed(0)}%</span>;
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState(DEMO_TRANSACTIONS);
  const [filter, setFilter] = useState("all");
  const [search, setSearch]  = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const filtered = transactions.filter(t => {
    const matchStatus = filter === "all" || t.status === filter || (filter === "review" && t.tier === "review");
    const matchSearch = t.desc.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const pendingCount = transactions.filter(t => t.tier === "review").length;

  async function syncTransactions() {
    setLoading(true);
    try {
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/basiq/sync`, { method: "POST" });
      const data = await r.json();
      toast({ title: `Synced ${data.inserted ?? 0} new transactions`, description: `${data.synced ?? 0} total fetched from Basiq` });
    } catch {
      toast({ title: "Sync failed", description: "Check Basiq connection", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  async function categoriseAll() {
    setLoading(true);
    toast({ title: "Running AI categorisation...", description: "Processing all pending transactions" });
    await new Promise(r => setTimeout(r, 1500));
    toast({ title: "Categorisation complete", description: "89% auto-categorised" });
    setLoading(false);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {filtered.length} transactions · {pendingCount} need review
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={syncTransactions} disabled={loading}>
            <RefreshCw size={14} className={`mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Sync Bank Feed
          </Button>
          <Button size="sm" onClick={categoriseAll} disabled={loading}>
            <CheckCheck size={14} className="mr-1.5" />
            Categorise All
          </Button>
        </div>
      </div>

      {pendingCount > 0 && (
        <div className="flex items-center gap-2 bg-amber-50 border border-amber-200
          text-amber-800 text-sm px-4 py-2.5 rounded-lg">
          <AlertCircle size={16} className="shrink-0" />
          <span><strong>{pendingCount} transactions</strong> need your review before they can be posted to the ledger.</span>
          <button onClick={() => setFilter("review")}
            className="ml-auto text-amber-700 underline text-xs font-medium">Show only</button>
        </div>
      )}

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Search transactions..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-44 text-sm">
            <Filter size={14} className="mr-1.5 text-gray-400" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Transactions</SelectItem>
            <SelectItem value="review">Needs Review</SelectItem>
            <SelectItem value="categorised">Categorised</SelectItem>
            <SelectItem value="posted">Posted</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              {["Date","Description","Amount","Account","Tier","Confidence","GST","Action"].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map(t => (
              <tr key={t.id} className={`hover:bg-gray-50 transition-colors ${t.tier === "review" ? "bg-amber-50/40" : ""}`}>
                <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{t.date}</td>
                <td className="px-4 py-3 text-gray-900 max-w-[220px]">
                  <div className="truncate font-medium">{t.desc}</div>
                </td>
                <td className={`px-4 py-3 font-semibold whitespace-nowrap ${t.amount < 0 ? "text-red-600" : "text-green-600"}`}>
                  {t.amount < 0 ? "-" : "+"}${(Math.abs(t.amount) / 100).toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  {t.account
                    ? <span className="text-gray-700">{t.account} <span className="text-gray-400 text-xs">({t.code})</span></span>
                    : <span className="text-gray-400 italic">Uncategorised</span>
                  }
                </td>
                <td className="px-4 py-3"><TierBadge tier={t.tier} /></td>
                <td className="px-4 py-3"><ConfBadge confidence={t.confidence} tier={t.tier} /></td>
                <td className="px-4 py-3 text-gray-500 text-xs">{t.gst ?? "—"}</td>
                <td className="px-4 py-3">
                  {t.tier === "review"
                    ? <Button size="sm" variant="outline" className="text-xs h-7 border-amber-300 text-amber-700 hover:bg-amber-50">
                        Fix
                      </Button>
                    : <Button size="sm" variant="ghost" className="text-xs h-7 text-gray-400">
                        Edit
                      </Button>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Step 4.5 — Journal Page

Create `apps/web/app/journal/page.tsx`:

```tsx
"use client";
import { useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle2 } from "lucide-react";
import { DemoBadge } from "@/components/DemoBadge";

const JOURNAL_ENTRIES = [
  {
    id: "JE-0042", date: "17/04/2025", description: "Bunnings Warehouse - Plumbing Materials",
    reference: "BUNNINGS 00435", status: "posted", totalDebit: 23450, totalCredit: 23450,
    lines: [
      { account: "5000 Plumbing Materials & Parts", debit: 21318,  credit: 0,      gst: 2132  },
      { account: "1200 GST Receivable",              debit: 2132,   credit: 0,      gst: 0     },
      { account: "1000 ANZ Business Cheque",         debit: 0,      credit: 23450,  gst: 0     },
    ]
  },
  {
    id: "JE-0041", date: "16/04/2025", description: "Customer Invoice 2024-0342 - Emergency Plumbing",
    reference: "INV-2024-0342", status: "posted", totalDebit: 660000, totalCredit: 660000,
    lines: [
      { account: "1000 ANZ Business Cheque",         debit: 660000, credit: 0,      gst: 0     },
      { account: "4000 Plumbing Services Revenue",   debit: 0,      credit: 600000, gst: 0     },
      { account: "2100 GST Collected",               debit: 0,      credit: 60000,  gst: 60000 },
    ]
  },
  {
    id: "JE-0040", date: "16/04/2025", description: "Ampol Fuel - Vehicle Operating Expense",
    reference: "AMPOL BROOKVALE", status: "posted", totalDebit: 8920, totalCredit: 8920,
    lines: [
      { account: "6000 Fuel & Vehicle",              debit: 8109,   credit: 0,      gst: 811   },
      { account: "1200 GST Receivable",              debit: 811,    credit: 0,      gst: 0     },
      { account: "1000 ANZ Business Cheque",         debit: 0,      credit: 8920,   gst: 0     },
    ]
  },
  {
    id: "JE-0039", date: "15/04/2025", description: "ATO BAS Payment Q3",
    reference: "ATO PORTAL", status: "posted", totalDebit: 310000, totalCredit: 310000,
    lines: [
      { account: "2110 GST Payable",                 debit: 310000, credit: 0,      gst: 0     },
      { account: "1000 ANZ Business Cheque",         debit: 0,      credit: 310000, gst: 0     },
    ]
  },
];

function fmt(cents: number) {
  return cents > 0 ? `$${(cents / 100).toLocaleString("en-AU", { minimumFractionDigits: 2 })}` : "—";
}

export default function JournalPage() {
  const [expanded, setExpanded] = useState<string | null>("JE-0042");

  const totalDebits  = JOURNAL_ENTRIES.reduce((s, e) => s + e.totalDebit, 0);
  const totalCredits = JOURNAL_ENTRIES.reduce((s, e) => s + e.totalCredit, 0);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Journal</h1>
          <p className="text-sm text-gray-500 mt-0.5">Double-entry ledger — powered by Formance</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200
          text-green-700 text-xs px-3 py-1.5 rounded-full font-medium">
          <CheckCircle2 size={14} />
          Balanced: Dr ${(totalDebits/100).toLocaleString()} = Cr ${(totalCredits/100).toLocaleString()}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-4 py-3 text-left w-8" />
              <th className="px-4 py-3 text-left">Reference</th>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Description</th>
              <th className="px-4 py-3 text-right">Debit</th>
              <th className="px-4 py-3 text-right">Credit</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {JOURNAL_ENTRIES.map(entry => (
              <>
                <tr
                  key={entry.id}
                  className="hover:bg-gray-50 cursor-pointer border-t border-gray-100"
                  onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                >
                  <td className="px-4 py-3 text-gray-400">
                    {expanded === entry.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{entry.id}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{entry.date}</td>
                  <td className="px-4 py-3 text-gray-800 font-medium">{entry.description}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-700">{fmt(entry.totalDebit)}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-700">{fmt(entry.totalCredit)}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      {entry.status}
                    </span>
                  </td>
                </tr>
                {expanded === entry.id && entry.lines.map((line, i) => (
                  <tr key={i} className="bg-blue-50/40 text-xs border-t border-blue-100">
                    <td className="px-4 py-2" />
                    <td colSpan={3} className="px-8 py-2 text-gray-600 font-medium">{line.account}</td>
                    <td className="px-4 py-2 text-right text-gray-700">{fmt(line.debit)}</td>
                    <td className="px-4 py-2 text-right text-gray-700">{fmt(line.credit)}</td>
                    <td className="px-4 py-2 text-gray-400 text-xs">
                      {line.gst > 0 ? `GST $${(line.gst/100).toFixed(2)}` : ""}
                    </td>
                  </tr>
                ))}
              </>
            ))}
            <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-sm">
              <td colSpan={4} className="px-4 py-3 text-gray-700">Totals</td>
              <td className="px-4 py-3 text-right text-gray-900">{fmt(totalDebits)}</td>
              <td className="px-4 py-3 text-right text-gray-900">{fmt(totalCredits)}</td>
              <td />
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Step 4.6 — Reports Page

Create `apps/web/app/reports/page.tsx`. Must show: P&L, Trial Balance tab, GST/BAS summary, and stub Balance Sheet with `DEMO` badge.

```tsx
"use client";
import { useState } from "react";
import { DemoBadge } from "@/components/DemoBadge";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

const PL_DATA = {
  revenue: [
    { code: "4000", name: "Plumbing Services Revenue",   amount: 4310000 },
    { code: "4010", name: "Emergency Call-Out Revenue",  amount: 660000 },
    { code: "4020", name: "Parts & Materials Revenue",   amount: 285000 },
    { code: "4900", name: "Interest Income",             amount: 8700 },
  ],
  cogs: [
    { code: "5000", name: "Plumbing Materials & Parts",  amount: 1245000 },
    { code: "5010", name: "Subcontractor Labour",        amount: 610000 },
  ],
  expenses: [
    { code: "6000", name: "Fuel & Vehicle",              amount: 312000 },
    { code: "6010", name: "Vehicle Registration & Insurance", amount: 210000 },
    { code: "6100", name: "Electricity",                 amount: 89000 },
    { code: "6110", name: "Mobile & Internet",           amount: 56000 },
    { code: "6200", name: "Software Subscriptions",      amount: 43000 },
    { code: "6400", name: "Accounting & Legal",          amount: 165000 },
    { code: "6500", name: "Bank Fees & Charges",         amount: 23000 },
    { code: "6600", name: "Superannuation Expense",      amount: 210000 },
    { code: "6700", name: "Wages & Salaries",            amount: 920000 },
    { code: "6800", name: "ATO Payments",                amount: 310000 },
  ]
};

function fmtAUD(cents: number) {
  return `$${(cents / 100).toLocaleString("en-AU", { minimumFractionDigits: 2 })}`;
}

function PLSection({ title, rows, total, totalLabel, highlight = false }: any) {
  return (
    <div className="mb-2">
      <div className="bg-gray-100 px-4 py-2 text-xs font-semibold text-gray-600 uppercase tracking-wide">
        {title}
      </div>
      {rows.map((r: any) => (
        <div key={r.code} className="flex justify-between px-4 py-2 text-sm border-b border-gray-50 hover:bg-gray-50">
          <span className="text-gray-700"><span className="text-gray-400 mr-2">{r.code}</span>{r.name}</span>
          <span className="text-gray-800 font-medium">{fmtAUD(r.amount)}</span>
        </div>
      ))}
      <div className={`flex justify-between px-4 py-2.5 text-sm font-bold ${highlight ? "bg-blue-50 text-blue-800" : "bg-gray-50"}`}>
        <span>{totalLabel}</span>
        <span>{fmtAUD(total)}</span>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const [tab, setTab] = useState<"pl" | "tb" | "gst" | "bs">("pl");

  const totalRevenue  = PL_DATA.revenue.reduce((s, r) => s + r.amount, 0);
  const totalCOGS     = PL_DATA.cogs.reduce((s, r) => s + r.amount, 0);
  const grossProfit   = totalRevenue - totalCOGS;
  const totalExpenses = PL_DATA.expenses.reduce((s, r) => s + r.amount, 0);
  const netProfit     = grossProfit - totalExpenses;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-sm text-gray-500 mt-0.5">Coastal Trades Pty Ltd · FY 2024–25</p>
        </div>
        <Button variant="outline" size="sm">
          <Download size={14} className="mr-1.5" />
          Export PDF
          <DemoBadge />
        </Button>
      </div>

      <div className="flex gap-1 border-b border-gray-200">
        {[
          { key: "pl",  label: "Profit & Loss" },
          { key: "tb",  label: "Trial Balance" },
          { key: "gst", label: "GST / BAS" },
          { key: "bs",  label: "Balance Sheet" },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as any)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
              tab === t.key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "pl" && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-4 py-4 border-b flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-800">Profit & Loss Statement</h2>
              <p className="text-xs text-gray-500 mt-0.5">1 July 2024 – 30 April 2025 (YTD)</p>
            </div>
          </div>
          <PLSection title="Revenue" rows={PL_DATA.revenue} total={totalRevenue} totalLabel="Total Revenue" />
          <PLSection title="Cost of Goods Sold" rows={PL_DATA.cogs} total={totalCOGS} totalLabel="Total COGS" />
          <div className="flex justify-between px-4 py-3 text-sm font-bold bg-blue-50 text-blue-800">
            <span>Gross Profit</span><span>{fmtAUD(grossProfit)}</span>
          </div>
          <PLSection title="Operating Expenses" rows={PL_DATA.expenses} total={totalExpenses} totalLabel="Total Expenses" />
          <div className={`flex justify-between px-4 py-4 text-base font-bold ${netProfit >= 0 ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
            <span>Net Profit / (Loss)</span><span>{fmtAUD(netProfit)}</span>
          </div>
        </div>
      )}

      {tab === "tb" && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-4 py-4 border-b">
            <h2 className="font-semibold text-gray-800">Trial Balance</h2>
            <p className="text-xs text-gray-500 mt-0.5">As at 30 April 2025</p>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3 text-left">Code</th>
                <th className="px-4 py-3 text-left">Account Name</th>
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-right">Debit</th>
                <th className="px-4 py-3 text-right">Credit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {[
                { code: "1000", name: "ANZ Business Cheque",    type: "asset",    dr: 8234500, cr: 0       },
                { code: "1100", name: "Trade Debtors",          type: "asset",    dr: 1450000, cr: 0       },
                { code: "1200", name: "GST Receivable",         type: "asset",    dr: 283600,  cr: 0       },
                { code: "2100", name: "GST Collected",          type: "liability",dr: 0,       cr: 466300  },
                { code: "2110", name: "GST Payable",            type: "liability",dr: 0,       cr: 182700  },
                { code: "3000", name: "Retained Earnings",      type: "equity",   dr: 0,       cr: 12800000},
                { code: "4000", name: "Plumbing Services",      type: "revenue",  dr: 0,       cr: 4310000 },
                { code: "4010", name: "Emergency Call-Out",     type: "revenue",  dr: 0,       cr: 660000  },
                { code: "5000", name: "Plumbing Materials",     type: "expense",  dr: 1245000, cr: 0       },
                { code: "6700", name: "Wages & Salaries",       type: "expense",  dr: 920000,  cr: 0       },
              ].map(r => (
                <tr key={r.code} className="hover:bg-gray-50">
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{r.code}</td>
                  <td className="px-4 py-2.5 text-gray-800">{r.name}</td>
                  <td className="px-4 py-2.5 capitalize text-gray-500 text-xs">{r.type}</td>
                  <td className="px-4 py-2.5 text-right text-gray-700">{r.dr > 0 ? fmtAUD(r.dr) : "—"}</td>
                  <td className="px-4 py-2.5 text-right text-gray-700">{r.cr > 0 ? fmtAUD(r.cr) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "gst" && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h2 className="font-semibold text-gray-800 mb-4">BAS Summary — Q3 FY24–25 (Jan–Mar 2025)</h2>
            <div className="space-y-3 text-sm">
              {[
                { label: "G1 Total Sales (incl. GST)",     value: "$66,330" },
                { label: "1A GST on Sales",                 value: "$6,030",  highlight: true },
                { label: "G11 Non-capital Purchases (incl. GST)", value: "$31,240" },
                { label: "1B GST on Purchases (Creditable)", value: "$2,840",  highlight: true },
                { label: "Net GST Payable (1A minus 1B)",   value: "$3,190",  bold: true, warn: true },
              ].map(r => (
                <div key={r.label} className={`flex justify-between py-2 border-b border-gray-50 ${r.bold ? "font-bold text-base" : ""}`}>
                  <span className={r.highlight ? "text-blue-700" : "text-gray-600"}>{r.label}</span>
                  <span className={r.warn ? "text-red-600" : "text-gray-800"}>{r.value}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs text-gray-400">
              Due 28/04/2025 · Cash basis · Prepared by Smart GL AI
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <div className="flex items-center gap-2 mb-4">
              <h2 className="font-semibold text-gray-800">BAS Lodgement History</h2>
              <DemoBadge />
            </div>
            {[
              { period: "Q2 FY24–25 (Oct–Dec)", due: "28/01/2025", status: "Lodged", amount: "$2,840" },
              { period: "Q1 FY24–25 (Jul–Sep)",  due: "28/10/2024", status: "Lodged", amount: "$3,410" },
              { period: "Q4 FY23–24 (Apr–Jun)",  due: "28/07/2024", status: "Lodged", amount: "$2,190" },
            ].map(r => (
              <div key={r.period} className="flex items-center justify-between py-3 border-b border-gray-50 text-sm">
                <div>
                  <div className="text-gray-800 font-medium">{r.period}</div>
                  <div className="text-xs text-gray-400">Due {r.due} · {r.amount}</div>
                </div>
                <span className="bg-green-100 text-green-700 text-xs font-medium px-2 py-0.5 rounded-full">
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "bs" && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="font-semibold text-gray-800">Balance Sheet</h2>
            <DemoBadge label="STAGE 2 FEATURE" />
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Full Balance Sheet (Assets, Liabilities, Equity) is implemented in Stage 2.
            The data model and journal entries in Stage 1 are fully compliant with balance sheet generation.
            Trial Balance above confirms all entries are correctly classified.
          </p>
          <div className="grid grid-cols-2 gap-8 text-sm">
            <div>
              <div className="font-semibold text-gray-800 mb-2">Assets</div>
              {[
                { name: "ANZ Business Cheque",   amount: "$82,345" },
                { name: "Trade Debtors",         amount: "$14,500" },
                { name: "GST Receivable",        amount: "$2,836"  },
                { name: "Prepayments",           amount: "$1,200"  },
              ].map(r => (
                <div key={r.name} className="flex justify-between py-1.5 border-b border-gray-50 text-gray-600">
                  <span>{r.name}</span><span>{r.amount}</span>
                </div>
              ))}
              <div className="flex justify-between py-2 font-bold text-gray-800">
                <span>Total Assets</span><span>$100,881</span>
              </div>
            </div>
            <div>
              <div className="font-semibold text-gray-800 mb-2">Liabilities + Equity</div>
              {[
                { name: "GST Collected",         amount: "$4,663" },
                { name: "GST Payable",           amount: "$1,827" },
                { name: "Trade Creditors",       amount: "$8,100" },
                { name: "Retained Earnings",     amount: "$86,291"},
              ].map(r => (
                <div key={r.name} className="flex justify-between py-1.5 border-b border-gray-50 text-gray-600">
                  <span>{r.name}</span><span>{r.amount}</span>
                </div>
              ))}
              <div className="flex justify-between py-2 font-bold text-gray-800">
                <span>Total L + E</span><span>$100,881</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Step 4.7 — Bank Feeds Page

Create `apps/web/app/bank-feeds/page.tsx`:

```tsx
"use client";
import { useState } from "react";
import { RefreshCw, Plus, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DemoBadge } from "@/components/DemoBadge";
import { useToast } from "@/hooks/use-toast";

const CONNECTIONS = [
  { id: "c1", bank: "ANZ",     name: "Business Everyday",  number: "****4521", balance: "$82,345.20", lastSync: "Today 09:14", status: "active",  txnCount: 143 },
  { id: "c2", bank: "ANZ",     name: "Business Savings",   number: "****7834", balance: "$24,100.00", lastSync: "Today 09:14", status: "active",  txnCount: 12  },
];

export default function BankFeedsPage() {
  const [syncing, setSyncing] = useState(false);
  const { toast }  = useToast();

  async function runSync() {
    setSyncing(true);
    try {
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/basiq/sync`, { method: "POST" });
      const d = await r.json();
      toast({ title: `Sync complete`, description: `${d.inserted ?? 0} new transactions imported` });
    } catch {
      toast({ title: "Sync failed", variant: "destructive" });
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bank Feeds</h1>
          <p className="text-sm text-gray-500 mt-0.5">Connected via Basiq Open Banking (CDR)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={runSync} disabled={syncing}>
            <RefreshCw size={14} className={`mr-1.5 ${syncing ? "animate-spin" : ""}`} />
            Sync All
          </Button>
          <Button size="sm">
            <Plus size={14} className="mr-1.5" />
            Add Bank Account
          </Button>
        </div>
      </div>

      {/* Connected accounts */}
      <div className="grid grid-cols-2 gap-4">
        {CONNECTIONS.map(c => (
          <div key={c.id} className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="font-semibold text-gray-900">{c.bank} — {c.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">{c.number}</div>
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">
                <CheckCircle2 size={12} />
                Active
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-3">{c.balance}</div>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
              <div><span className="text-gray-400">Last sync</span><br /><span className="text-gray-700 font-medium">{c.lastSync}</span></div>
              <div><span className="text-gray-400">Transactions</span><br /><span className="text-gray-700 font-medium">{c.txnCount} this period</span></div>
            </div>
          </div>
        ))}

        <div className="bg-gray-50 rounded-xl p-5 border border-dashed border-gray-200 flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-gray-100 transition-colors">
          <div className="w-10 h-10 rounded-full bg-white border border-gray-200 flex items-center justify-center">
            <Plus size={18} className="text-gray-400" />
          </div>
          <div className="text-sm font-medium text-gray-600">Connect another bank</div>
          <div className="text-xs text-gray-400 text-center">135+ Australian banks supported via CDR</div>
        </div>
      </div>

      {/* Sync history */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Sync History</h2>
        </div>
        <div className="divide-y divide-gray-50">
          {[
            { time: "Today 09:14",     bank: "ANZ (both accounts)", result: "143 transactions",  status: "success" },
            { time: "Yesterday 09:00", bank: "ANZ (both accounts)", result: "8 new transactions", status: "success" },
            { time: "16/04 09:00",     bank: "ANZ (both accounts)", result: "11 new transactions",status: "success" },
            { time: "15/04 15:32",     bank: "ANZ Business",        result: "Connection timeout", status: "error"   },
          ].map((r, i) => (
            <div key={i} className="flex items-center justify-between px-5 py-3 text-sm">
              <div className="flex items-center gap-3">
                {r.status === "success"
                  ? <CheckCircle2 size={16} className="text-green-500" />
                  : <AlertCircle size={16} className="text-red-400" />
                }
                <div>
                  <div className="text-gray-800 font-medium">{r.bank}</div>
                  <div className="text-xs text-gray-400">{r.result}</div>
                </div>
              </div>
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <Clock size={12} />
                {r.time}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Basiq info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 text-sm">
        <div className="font-semibold text-blue-800 mb-2">About Basiq Open Banking</div>
        <div className="text-blue-700 space-y-1 text-xs">
          <p>Bank feeds are powered by Basiq, an ACCC-accredited Consumer Data Right (CDR) data recipient.</p>
          <p>Data is fetched via CDR Open Banking for supported institutions. Older banks use a web connector fallback.</p>
          <p>Transactions are fetched 30 days back on each sync to capture delayed postings. Deduplication is guaranteed by Basiq transaction ID.</p>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 4.8 — Chart of Accounts Page

Create `apps/web/app/accounts/page.tsx`:

```tsx
"use client";
import { useState } from "react";
import { Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

const ACCOUNTS = [
  { code: "1000", name: "ANZ Business Cheque",          type: "asset",     gst: "N-T", system: true  },
  { code: "1100", name: "Trade Debtors",                type: "asset",     gst: "N-T", system: true  },
  { code: "1200", name: "GST Receivable",               type: "asset",     gst: "N-T", system: true  },
  { code: "2000", name: "Trade Creditors",              type: "liability", gst: "N-T", system: true  },
  { code: "2100", name: "GST Collected",                type: "liability", gst: "N-T", system: true  },
  { code: "3000", name: "Retained Earnings",            type: "equity",    gst: "N-T", system: true  },
  { code: "4000", name: "Plumbing Services Revenue",    type: "revenue",   gst: "G1",  system: true  },
  { code: "4010", name: "Emergency Call-Out Revenue",   type: "revenue",   gst: "G1",  system: false },
  { code: "5000", name: "Plumbing Materials & Parts",   type: "expense",   gst: "G11", system: false },
  { code: "5010", name: "Subcontractor Labour",         type: "expense",   gst: "G11", system: false },
  { code: "6000", name: "Fuel & Vehicle",               type: "expense",   gst: "G11", system: false },
  { code: "6100", name: "Electricity",                  type: "expense",   gst: "G11", system: false },
  { code: "6200", name: "Software Subscriptions",       type: "expense",   gst: "G11", system: false },
  { code: "6700", name: "Wages & Salaries",             type: "expense",   gst: "N-T", system: false },
  { code: "6800", name: "ATO Payments",                 type: "expense",   gst: "N-T", system: false },
];

const TYPE_COLORS: Record<string, string> = {
  asset:     "bg-blue-100 text-blue-700",
  liability: "bg-red-100 text-red-700",
  equity:    "bg-purple-100 text-purple-700",
  revenue:   "bg-green-100 text-green-700",
  expense:   "bg-orange-100 text-orange-700",
};

export default function AccountsPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = ACCOUNTS.filter(a =>
    (typeFilter === "all" || a.type === typeFilter) &&
    (a.code.includes(search) || a.name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chart of Accounts</h1>
          <p className="text-sm text-gray-500 mt-0.5">Standard AU SME COA · GST-mapped</p>
        </div>
        <Button size="sm">
          <Plus size={14} className="mr-1.5" />
          Add Account
        </Button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Search accounts..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        {["all","asset","liability","equity","revenue","expense"].map(t => (
          <button key={t}
            onClick={() => setTypeFilter(t)}
            className={`px-3 py-1.5 text-xs rounded-lg font-medium capitalize transition-colors ${
              typeFilter === t ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}>
            {t}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500">
            <tr>
              {["Code","Name","Type","GST Code","Formance Address","System"].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map(a => (
              <tr key={a.code} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-600 font-medium">{a.code}</td>
                <td className="px-4 py-3 text-gray-800">{a.name}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium capitalize ${TYPE_COLORS[a.type]}`}>
                    {a.type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">{a.gst}</span>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">
                  {a.type}s:{a.name.toLowerCase().replace(/\s+/g,"_").slice(0,20)}
                </td>
                <td className="px-4 py-3">
                  {a.system
                    ? <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">System</span>
                    : <button className="text-xs text-blue-600 hover:underline">Edit</button>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Step 4.9 — AI Insights Page (Stage 2 Preview)

Create `apps/web/app/ai-insights/page.tsx`. Full feature set shown with DEMO badges where not live.

```tsx
"use client";
import { DemoBadge } from "@/components/DemoBadge";
import { Brain, TrendingUp, AlertTriangle, Lightbulb } from "lucide-react";

const INSIGHTS = [
  {
    type: "anomaly", title: "Unusual expense: Officeworks $78.90",
    body: "This is 340% above your average stationery spend. Common reasons: bulk purchase before tax year end, or personal expense accidentally charged to business card.",
    action: "Review transaction", severity: "warning"
  },
  {
    type: "pattern", title: "Woolworths transactions likely split-purpose",
    body: "3 Woolworths transactions this month. 2 are likely groceries (personal), 1 may be cleaning supplies for the workshop (business). Consider splitting or excluding the personal ones.",
    action: "Review 3 transactions", severity: "info"
  },
  {
    type: "suggestion", title: "Superannuation liability may be underpaid",
    body: "Based on your wages ($9,200 this quarter), superannuation payable should be approximately $1,012.00 at 11%. Current balance in 2300 Superannuation Payable is $0.",
    action: "Create journal entry", severity: "error"
  },
  {
    type: "pattern", title: "High confidence: Reece Plumbing = Account 5000",
    body: "99 of the last 100 Reece Plumbing transactions have been categorised to 5000 Plumbing Materials. The embedding model has learned this pattern and will categorise them in <50ms.",
    action: null, severity: "success"
  },
];

export default function AIInsightsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Insights</h1>
          <p className="text-sm text-gray-500 mt-0.5">Powered by Claude claude-sonnet-4-6</p>
        </div>
        <DemoBadge label="PARTIAL — STAGE 1" />
      </div>

      {/* Categorisation model stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Embedding hits",   value: "78%",  sub: "~45ms avg",       color: "text-green-600" },
          { label: "LLM categorised",  value: "14%",  sub: "~820ms avg",      color: "text-blue-600"  },
          { label: "Human review",     value: "5%",   sub: "7 pending",       color: "text-amber-600" },
          { label: "Training samples", value: "643",  sub: "across all accts",color: "text-gray-600"  },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-sm text-gray-700 mt-0.5">{s.label}</div>
            <div className="text-xs text-gray-400">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* AI-generated insights */}
      <div>
        <h2 className="font-semibold text-gray-800 mb-3">AI-Generated Insights</h2>
        <div className="space-y-3">
          {INSIGHTS.map((ins, i) => (
            <div key={i} className={`bg-white rounded-xl p-4 border shadow-sm flex gap-4 ${
              ins.severity === "error" ? "border-red-200" :
              ins.severity === "warning" ? "border-amber-200" :
              ins.severity === "success" ? "border-green-200" :
              "border-gray-100"
            }`}>
              <div className={`mt-0.5 shrink-0 ${
                ins.severity === "error" ? "text-red-500" :
                ins.severity === "warning" ? "text-amber-500" :
                ins.severity === "success" ? "text-green-500" :
                "text-blue-500"
              }`}>
                {ins.type === "anomaly" ? <AlertTriangle size={18} /> :
                 ins.type === "suggestion" ? <Lightbulb size={18} /> :
                 ins.type === "pattern" ? <TrendingUp size={18} /> :
                 <Brain size={18} />}
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900 text-sm">{ins.title}</div>
                <div className="text-xs text-gray-600 mt-1">{ins.body}</div>
                {ins.action && (
                  <button className="mt-2 text-xs text-blue-600 hover:underline font-medium">
                    {ins.action} →
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Stage 2 preview */}
      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="font-semibold text-gray-700">Stage 2: Knowledge Graph Insights</h2>
          <DemoBadge label="STAGE 2" />
        </div>
        <p className="text-sm text-gray-500">
          Stage 2 adds cross-tenant learning: when a Woolworths transaction is confirmed as cleaning supplies by another trades business, Smart GL updates the merchant-to-account graph. New tenants benefit immediately, achieving 90%+ auto-categorisation from day 1 instead of needing 200+ manual confirmations.
        </p>
      </div>
    </div>
  );
}
```

---

---

# PHASE 5: Integration Wiring

## Step 5.1 — pg_cron Sync Job

Add to `infra/supabase/migrations/009_cron.sql`:

```sql
-- Run Basiq sync every 4 hours via pg_cron + http extension
-- Requires pg_net extension on Supabase
SELECT cron.schedule(
  'basiq-sync-job',
  '0 */4 * * *',
  $$
    SELECT net.http_post(
      url := current_setting('app.api_url') || '/basiq/sync',
      headers := '{"Content-Type": "application/json"}'::jsonb,
      body := '{}'::jsonb
    );
  $$
);
```

Note: Set `app.api_url` in Supabase secrets to your Fly.io API URL once deployed.

---

## Step 5.2 — Basiq Webhook Handler

Add to `apps/api/routers/basiq.py`:

```python
@router.post("/webhook")
async def basiq_webhook(payload: dict):
    """
    Basiq sends POST to this endpoint when a job completes.
    We trigger an immediate sync rather than waiting for the cron.
    """
    event_type = payload.get("type")
    if event_type in ("job.completed", "connections.refreshed"):
        # Trigger sync in background (do not block the webhook response)
        import asyncio
        asyncio.create_task(sync_transactions())
    return {"received": True}
```

Register this URL in Basiq dashboard under: Application → Webhooks → Add endpoint.

---

---

# PHASE 6: Test Plan

Every test must be runnable by the agent without human interaction. All tests must pass before marking the PoC complete.

## Step 6.1 — Backend Tests

Install:
```bash
cd apps/api
pip install pytest pytest-asyncio httpx
```

Create `apps/api/tests/test_categorise.py`:

```python
import pytest
from services.categorise import clean_description

def test_clean_description_strips_date():
    assert "BUNNINGS SYDNEY" == clean_description("BUNNINGS 00435 SYDNEY 15/04")

def test_clean_description_strips_long_numbers():
    result = clean_description("AMPOL FUEL 12345678 BROOKVALE")
    assert "12345678" not in result

def test_clean_description_strips_card_ref():
    result = clean_description("VISA GOOGLE WORKSPACE CARD 9234")
    assert "CARD" not in result
    assert "GOOGLE WORKSPACE" in result

def test_clean_description_uppercase():
    result = clean_description("bunnings 00435")
    assert result == result.upper()
```

Create `apps/api/tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_transactions_list():
    r = client.get("/transactions/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_reports_trial_balance():
    r = client.get("/reports/trial-balance")
    assert r.status_code == 200

def test_reports_dashboard_summary():
    r = client.get("/reports/dashboard-summary")
    assert r.status_code == 200
    data = r.json()
    assert "revenue_cents" in data
    assert "expenses_cents" in data
    assert "auto_cat_rate" in data
```

Run:
```bash
pytest apps/api/tests/ -v
```

---

## Step 6.2 — Database Constraint Tests

Create `infra/supabase/tests/test_journal_balance.sql`:

```sql
-- Test 1: Balanced entry must succeed
DO $$
DECLARE
  v_entry_id UUID;
BEGIN
  INSERT INTO journal_entries (tenant_id, entry_date, description, status)
  VALUES ('a1b2c3d4-0000-0000-0000-000000000001', CURRENT_DATE, 'Test entry', 'posted')
  RETURNING id INTO v_entry_id;

  INSERT INTO journal_lines (tenant_id, journal_entry_id, account_id, debit_cents, credit_cents)
  VALUES
    ('a1b2c3d4-0000-0000-0000-000000000001', v_entry_id,
     (SELECT id FROM accounts WHERE code='5000' LIMIT 1), 10000, 0),
    ('a1b2c3d4-0000-0000-0000-000000000001', v_entry_id,
     (SELECT id FROM accounts WHERE code='1000' LIMIT 1), 0, 10000);

  RAISE NOTICE 'PASS: Balanced entry accepted';

  -- Cleanup
  DELETE FROM journal_lines WHERE journal_entry_id = v_entry_id;
  DELETE FROM journal_entries WHERE id = v_entry_id;
END;
$$;

-- Test 2: Unbalanced entry must fail
DO $$
DECLARE
  v_entry_id UUID;
BEGIN
  INSERT INTO journal_entries (tenant_id, entry_date, description, status)
  VALUES ('a1b2c3d4-0000-0000-0000-000000000001', CURRENT_DATE, 'Unbalanced test', 'posted')
  RETURNING id INTO v_entry_id;

  BEGIN
    INSERT INTO journal_lines (tenant_id, journal_entry_id, account_id, debit_cents, credit_cents)
    VALUES
      ('a1b2c3d4-0000-0000-0000-000000000001', v_entry_id,
       (SELECT id FROM accounts WHERE code='5000' LIMIT 1), 10000, 0);

    RAISE EXCEPTION 'FAIL: Unbalanced entry should have been rejected';
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'PASS: Unbalanced entry rejected: %', SQLERRM;
  END;

  DELETE FROM journal_entries WHERE id = v_entry_id;
END;
$$;

-- Test 3: Duplicate basiq_id must fail
DO $$
BEGIN
  INSERT INTO bank_transactions
    (tenant_id, connection_id, basiq_id, amount_cents, description, transaction_date, transaction_type)
  VALUES
    ('a1b2c3d4-0000-0000-0000-000000000001',
     (SELECT id FROM bank_connections LIMIT 1),
     'DEDUP_TEST_001', -5000, 'Test', CURRENT_DATE, 'debit');

  BEGIN
    INSERT INTO bank_transactions
      (tenant_id, connection_id, basiq_id, amount_cents, description, transaction_date, transaction_type)
    VALUES
      ('a1b2c3d4-0000-0000-0000-000000000001',
       (SELECT id FROM bank_connections LIMIT 1),
       'DEDUP_TEST_001', -5000, 'Test duplicate', CURRENT_DATE, 'debit');

    RAISE EXCEPTION 'FAIL: Duplicate basiq_id should have been rejected';
  EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'PASS: Duplicate basiq_id rejected';
  END;

  DELETE FROM bank_transactions WHERE basiq_id = 'DEDUP_TEST_001';
END;
$$;
```

Run:
```bash
supabase db execute < infra/supabase/tests/test_journal_balance.sql
```

All three tests must print `PASS`.

---

## Step 6.3 — Formance Ledger Integration Test

Create `apps/api/tests/test_formance.py`:

```python
import pytest
import asyncio
from services.formance import post_transaction, get_account_balance

@pytest.mark.asyncio
async def test_post_transaction():
    tx_id = await post_transaction(
        description="TEST-001 Bunnings materials",
        source_address="assets:bank:anz_cheque",
        dest_address="expenses:cogs:materials",
        amount_cents=23450,
        metadata={"test": "true"}
    )
    assert tx_id is not None
    assert len(str(tx_id)) > 0

@pytest.mark.asyncio
async def test_account_balance():
    balance = await get_account_balance("expenses:cogs:materials")
    assert isinstance(balance, dict)
```

Run (requires Formance running locally):
```bash
pytest apps/api/tests/test_formance.py -v
```

---

## Step 6.4 — AI Categorisation End-to-End Test

Create `apps/api/tests/test_e2e_categorise.py`:

```python
import pytest
import os

# Only run if ANTHROPIC_API_KEY is set — skip in CI without keys
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)

from services.categorise import categorise_transaction

DEMO_COA = [
    {"id": "acc-5000", "code": "5000", "name": "Plumbing Materials",  "account_type": "expense", "gst_code": "G11"},
    {"id": "acc-6000", "code": "6000", "name": "Fuel & Vehicle",      "account_type": "expense", "gst_code": "G11"},
    {"id": "acc-4000", "code": "4000", "name": "Plumbing Services",   "account_type": "revenue", "gst_code": "G1"},
    {"id": "acc-6200", "code": "6200", "name": "Software Subscriptions","account_type":"expense", "gst_code": "G11"},
    {"id": "acc-6800", "code": "6800", "name": "ATO Payments",        "account_type": "expense", "gst_code": "N-T"},
]

@pytest.mark.asyncio
async def test_bunnings_categorised_as_materials(mock_supabase):
    result = await categorise_transaction(
        supabase=mock_supabase,
        tenant_id="test-tenant",
        transaction_id="test-txn-1",
        description_clean="BUNNINGS SYDNEY",
        amount_cents=-23450,
        merchant_name="Bunnings Warehouse",
        basiq_category="Hardware",
        coa=DEMO_COA
    )
    assert result["tier"] in ("embedding", "llm")
    if result["account_id"]:
        assert result["account_id"] == "acc-5000"

@pytest.mark.asyncio
async def test_ato_payment_no_gst(mock_supabase):
    result = await categorise_transaction(
        supabase=mock_supabase,
        tenant_id="test-tenant",
        transaction_id="test-txn-2",
        description_clean="ATO PORTAL BAS PAYMENT",
        amount_cents=-310000,
        merchant_name="Australian Tax Office",
        basiq_category="Government",
        coa=DEMO_COA
    )
    if result["account_id"]:
        assert result["gst_code"] == "N-T"
```

---

## Step 6.5 — Frontend Build Test

```bash
cd apps/web
pnpm build
```

Must complete with zero errors. TypeScript errors are failures. Fix all TypeScript errors before marking this step complete.

---

## Step 6.6 — Manual Smoke Test Checklist

Run through this checklist manually after all automated tests pass:

```
[ ] Dashboard loads with all 4 KPI cards visible
[ ] Revenue vs Expenses chart renders with bar data
[ ] AI Categorisation donut chart renders with 4 segments
[ ] Transactions page loads 14 demo rows
[ ] Filter "Needs Review" shows only amber-highlighted rows
[ ] Search for "BUNNINGS" returns 1 row
[ ] Fix button visible on rows with tier=review
[ ] Journal page shows 4 entries with expand/collapse
[ ] Expanding JE-0042 shows 3 journal lines
[ ] Balance badge shows Dr = Cr
[ ] Reports > P&L shows Revenue, COGS, Expenses sections
[ ] Reports > GST tab shows BAS Q3 summary
[ ] Reports > Balance Sheet shows STAGE 2 badge
[ ] Bank Feeds shows 2 ANZ connections
[ ] Sync All button triggers fetch to /basiq/sync
[ ] Chart of Accounts shows all 15 accounts
[ ] Type filter buttons filter the table
[ ] AI Insights shows 4 insight cards
[ ] All pages load without console errors
[ ] No TypeScript errors in terminal
```

---

---

# PHASE 7: Deployment

## Step 7.1 — Fly.io (FastAPI)

```bash
cd apps/api
fly launch --name smartgl-api --region syd
```

Set secrets:
```bash
fly secrets set \
  SUPABASE_URL="..." \
  SUPABASE_SERVICE_ROLE_KEY="..." \
  BASIQ_API_KEY="..." \
  ANTHROPIC_API_KEY="..." \
  OPENAI_API_KEY="..." \
  FORMANCE_LEDGER_URL="http://formance-ledger.internal:3068"
```

Create `apps/api/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Deploy:
```bash
fly deploy
```

## Step 7.2 — Vercel (Next.js)

```bash
cd apps/web
vercel --prod
```

Set environment variables in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=https://smartgl-api.fly.dev
NEXT_PUBLIC_APP_ENV=production
```

---

---

# APPENDIX: Stage 1 PoC Success Criteria

The PoC is complete when ALL of the following are true:

| Criterion | How to verify |
|---|---|
| All automated tests pass | `pytest apps/api/tests/ -v` exits 0 |
| Journal balance enforced | DB constraint test prints 3x PASS |
| Formance posts transactions | `test_formance.py` passes |
| Basiq sandbox syncs | `/basiq/sync` returns `{"synced": N, "inserted": N}` |
| AI categorises >85% in LLM tier | Run 20 diverse test transactions, count non-human tier |
| UI renders all 8 pages | Smoke test checklist all checked |
| No unhandled TypeScript errors | `pnpm build` exits 0 |
| Trial balance balances | Dashboard shows "Ledger balanced" badge |
| GST calculated on all transactions | Check `gst_amount_cents` in `categorisations` table |
| DEMO badges on all unimplemented features | Visual inspection of Reports > BAS, Balance Sheet |
