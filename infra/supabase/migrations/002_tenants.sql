CREATE TABLE tenants (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              TEXT NOT NULL,
  abn               CHAR(11),
  gst_registered    BOOLEAN NOT NULL DEFAULT TRUE,
  gst_basis         TEXT NOT NULL DEFAULT 'cash'
                    CHECK (gst_basis IN ('cash', 'accrual')),
  financial_year_start  INT NOT NULL DEFAULT 7,
  timezone          TEXT NOT NULL DEFAULT 'Australia/Sydney',
  formance_ledger   TEXT NOT NULL DEFAULT 'smartgl',
  basiq_user_id     TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX idx_tenants_basiq_user_id ON tenants(basiq_user_id) WHERE deleted_at IS NULL;

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON tenants
  USING (id::TEXT = current_setting('app.current_tenant_id', TRUE));