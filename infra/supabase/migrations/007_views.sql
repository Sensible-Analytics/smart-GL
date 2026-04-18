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