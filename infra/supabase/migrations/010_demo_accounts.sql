-- Demo accounts table for pre-populated demo data
CREATE TABLE demo_accounts (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  demo_name         TEXT NOT NULL UNIQUE,
  basiq_user_id     TEXT,
  tenant_id         UUID REFERENCES tenants(id),
  institution_name  TEXT NOT NULL DEFAULT 'Hooli Bank',
  account_holder    TEXT,
  status            TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','syncing','error','disconnected')),
  last_synced_at    TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_demo_accounts_name ON demo_accounts(demo_name);

-- Demo transactions table
CREATE TABLE demo_transactions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  demo_account_id  UUID NOT NULL REFERENCES demo_accounts(id),
  basiq_id          TEXT NOT NULL,
  amount_cents      BIGINT NOT NULL,
  currency          CHAR(3) NOT NULL DEFAULT 'AUD',
  description       TEXT NOT NULL,
  merchant_name     TEXT,
  merchant_category TEXT,
  category_code     TEXT,
  transaction_date  DATE NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(demo_account_id, basiq_id)
);

CREATE INDEX idx_demo_txn_date ON demo_transactions(demo_account_id, transaction_date DESC);