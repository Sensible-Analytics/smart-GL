-- Migration: 009_cron.sql
-- Auto-categorisation job using pg_cron
-- NOTE: Requires Supabase Pro plan (pg_cron not available on free tier)

-- Enable pg_cron extension (requires Supabase Pro)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Function to auto-categorise unconfirmed transactions
CREATE OR REPLACE FUNCTION cron.auto_categorise_transactions()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    rec RECORD;
    v_tenant_id UUID;
    v_transaction_id UUID;
    v_description_clean TEXT;
    v_amount_cents INTEGER;
    v_merchant_name TEXT;
    v_merchant_category TEXT;
    v_coa JSON;
    v_result JSON;
    v_account_id UUID;
    v_gst_code TEXT;
    v_confidence NUMERIC;
    v_tier TEXT;
BEGIN
    -- Process each tenant
    FOR rec IN
        SELECT id FROM tenants WHERE deleted_at IS NULL
    LOOP
        v_tenant_id := rec.id;

        -- Get Chart of Accounts as JSON
        SELECT json_agg(json_build_object(
            'id', id,
            'code', code,
            'name', name,
            'account_type', account_type,
            'gst_code', gst_code
        )) INTO v_coa
        FROM accounts
        WHERE tenant_id = v_tenant_id AND deleted_at IS NULL;

        -- Process pending transactions (limit 50 per run to manage costs)
        FOR v_transaction_id, v_description_clean, v_amount_cents, v_merchant_name, v_merchant_category IN
            SELECT id, description_clean, amount_cents, merchant_name, merchant_category
            FROM bank_transactions
            WHERE tenant_id = v_tenant_id
              AND status = 'pending'
              AND description_clean IS NOT NULL
              AND deleted_at IS NULL
            ORDER BY transaction_date DESC
            LIMIT 50
        LOOP
            -- Call categorisation logic (simplified for SQL - uses embedding match only)
            BEGIN
                -- Embedding-based matching happens in app layer
                -- This function marks transactions as needing review
                UPDATE bank_transactions
                SET status = 'needs_review'
                WHERE id = v_transaction_id;
            EXCEPTION WHEN OTHERS THEN
                -- Continue on error
                NULL;
            END;
        END LOOP;
    END LOOP;
END;
$$;

-- Schedule job to run every hour
-- NOTE: Uncomment after upgrading to Supabase Pro
-- SELECT cron.schedule(
--     'auto-categorise-job',
--     '0 * * * *',  -- Every hour at minute 0
--     'SELECT cron.auto_categorise_transactions()'
-- );