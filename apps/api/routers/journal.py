from fastapi import APIRouter
from db import get_supabase, set_tenant

router = APIRouter()
DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"


@router.get("/")
async def list_journal_entries(limit: int = 50, offset: int = 0):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = (
        supabase.table("journal_entries")
        .select("*, journal_lines(*, accounts(code, name))")
        .is_("deleted_at", None)
        .order("entry_date", desc=True)
        .range(offset, offset + limit - 1)
    )
    return result.data


@router.get("/{entry_id}")
async def get_journal_entry(entry_id: str):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    entry = (
        supabase.table("journal_entries")
        .select("*, journal_lines(*, accounts(code, name))")
        .eq("id", entry_id)
        .single()
        .execute()
    )
    return entry.data


@router.post("/")
async def create_journal_entry(entry: dict):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    result = (
        supabase.table("journal_entries")
        .insert(
            {
                "tenant_id": DEMO_TENANT_ID,
                "entry_date": entry["entry_date"],
                "description": entry["description"],
                "reference": entry.get("reference"),
                "status": entry.get("status", "draft"),
            }
        )
        .execute()
    )
    return result.data
