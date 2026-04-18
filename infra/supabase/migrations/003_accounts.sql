CREATE TABLE accounts (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id),
  code          TEXT NOT NULL,
  name          TEXT NOT NULL,
  account_type  TEXT NOT NULL
                CHECK (account_type IN ('asset','liability','equity','revenue','expense')),
  gst_code      TEXT NOT NULL DEFAULT 'G1'
                CHECK (gst_code IN ('G1','G2','G3','G4','G9','G11','N-T')),
  is_system     BOOLEAN NOT NULL DEFAULT FALSE,
  parent_id     UUID REFERENCES accounts(id),
  formance_address TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at    TIMESTAMPTZ,
  UNIQUE(tenant_id, code)
);

CREATE INDEX idx_accounts_tenant ON accounts(tenant_id) WHERE deleted_at IS NULL;

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY account_tenant_isolation ON accounts
  USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));