CREATE TABLE journal_entries (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id),
  transaction_id    UUID REFERENCES bank_transactions(id),
  formance_tx_id    TEXT,
  entry_date        DATE NOT NULL,
  description       TEXT NOT NULL,
  reference         TEXT,
  status            TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','posted','voided')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE TABLE journal_lines (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE CONSTRAINT TRIGGER trg_journal_balance
  AFTER INSERT OR UPDATE OR DELETE ON journal_lines
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_journal_balance();