-- Bank connections (one per bank account linked via Basiq)
CREATE TABLE bank_connections (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  basiq_connection_id   TEXT NOT NULL,
  institution_name  TEXT NOT NULL,
  account_name      TEXT NOT NULL,
  account_number    TEXT,
  account_type      TEXT,
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
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  connection_id     UUID NOT NULL REFERENCES bank_connections(id),
  basiq_id          TEXT NOT NULL,
  amount_cents      BIGINT NOT NULL,
  currency          CHAR(3) NOT NULL DEFAULT 'AUD',
  description       TEXT NOT NULL,
  description_clean TEXT,
  merchant_name     TEXT,
  merchant_category TEXT,
  transaction_date  DATE NOT NULL,
  balance_cents     BIGINT,
  transaction_type  TEXT,
  status            TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','categorised','posted','excluded')),
  raw_payload       JSONB,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ,
  UNIQUE(basiq_id)
);

CREATE INDEX idx_bank_txn_tenant ON bank_transactions(tenant_id, transaction_date DESC)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_bank_txn_status ON bank_transactions(tenant_id, status)
  WHERE deleted_at IS NULL;
ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY bank_txn_tenant_isolation ON bank_transactions
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));