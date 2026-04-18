from fastapi import APIRouter
from db import get_supabase, set_tenant

router = APIRouter()
DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"


@router.get("/trial-balance")
async def trial_balance():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = (
        supabase.from_("v_trial_balance")
        .select("*")
        .eq("tenant_id", DEMO_TENANT_ID)
        .execute()
    )
    return result.data


@router.get("/profit-loss")
async def profit_loss():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = (
        supabase.from_("v_profit_loss")
        .select("*")
        .eq("tenant_id", DEMO_TENANT_ID)
        .execute()
    )
    return result.data


@router.get("/dashboard-summary")
async def dashboard_summary():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    pl = (
        supabase.from_("v_profit_loss")
        .select("*")
        .eq("tenant_id", DEMO_TENANT_ID)
        .execute()
    )

    revenue = sum(r["amount_cents"] for r in pl.data if r["account_type"] == "revenue")
    expenses = sum(r["amount_cents"] for r in pl.data if r["account_type"] == "expense")

    pending = (
        supabase.table("bank_transactions")
        .select("id", count="exact")
        .eq("tenant_id", DEMO_TENANT_ID)
        .eq("status", "pending")
        .is_("deleted_at", None)
        .execute()
    )

    categorised = (
        supabase.table("bank_transactions")
        .select("id", count="exact")
        .eq("tenant_id", DEMO_TENANT_ID)
        .neq("status", "pending")
        .is_("deleted_at", None)
        .execute()
    )

    total = (pending.count or 0) + (categorised.count or 0)
    auto_rate = round(categorised.count / total * 100, 1) if total > 0 else 0

    return {
        "revenue_cents": revenue,
        "expenses_cents": expenses,
        "net_profit_cents": revenue - expenses,
        "auto_cat_rate": auto_rate,
        "pending_count": pending.count or 0,
        "total_count": total,
    }
