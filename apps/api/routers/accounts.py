from fastapi import APIRouter
from db import get_supabase, set_tenant

router = APIRouter()
DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"


@router.get("/")
async def list_accounts():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = (
        supabase.table("accounts")
        .select("*")
        .eq("tenant_id", DEMO_TENANT_ID)
        .is_("deleted_at", None)
        .order("code")
    )
    return result.data


@router.get("/{account_id}")
async def get_account(account_id: str):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = (
        supabase.table("accounts").select("*").eq("id", account_id).single().execute()
    )
    return result.data
