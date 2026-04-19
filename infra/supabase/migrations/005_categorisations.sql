CREATE TABLE categorisations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  transaction_id    UUID NOT NULL REFERENCES bank_transactions(id),
  account_id        UUID NOT NULL REFERENCES accounts(id),
  gst_code          TEXT NOT NULL DEFAULT 'G1',
  gst_amount_cents  BIGINT NOT NULL DEFAULT 0,
  confidence        NUMERIC(5,4),
  tier              TEXT NOT NULL
                    CHECK (tier IN ('embedding','llm','human')),
  is_confirmed      BOOLEAN NOT NULL DEFAULT FALSE,
  confirmed_by      UUID,
  confirmed_at      TIMESTAMPTZ,
  llm_reasoning     TEXT,
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


-- pgvector requires Supabase Pro - commented out
-- CREATE TABLE categorisation_embeddings (
--   id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   tenant_id         UUID NOT NULL REFERENCES tenants(id),
--   description_clean TEXT NOT NULL,
--   account_id        UUID NOT NULL REFERENCES accounts(id),
--   embedding         vector(1536),
--   sample_count      INT NOT NULL DEFAULT 1,
--   created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--   updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--   UNIQUE(tenant_id, description_clean, account_id)
-- );

-- CREATE INDEX idx_embedding_tenant ON categorisation_embeddings(tenant_id);
-- CREATE INDEX idx_embedding_vector ON categorisation_embeddings
--   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- ALTER TABLE categorisation_embeddings ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY embedding_tenant_isolation ON categorisation_embeddings
--   USING (tenant_id::TEXT = current_setting('app.current_tenant_id', TRUE));