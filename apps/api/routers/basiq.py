from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from db import get_supabase, set_tenant
from services.basiq import (
    get_access_token,
    create_basiq_user,
    get_auth_link,
    fetch_transactions,
)
from services.categorise import clean_description

router = APIRouter()
DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"


class ConnectRequest(BaseModel):
    email: str
    mobile: str


@router.post("/connect")
async def connect_bank(body: ConnectRequest):
    token = await get_access_token()
    basiq_user_id = await create_basiq_user(token, body.email, body.mobile)

    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    supabase.table("tenants").update({"basiq_user_id": basiq_user_id}).eq(
        "id", DEMO_TENANT_ID
    ).execute()

    auth_link = await get_auth_link(token, basiq_user_id)
    return {"consent_url": auth_link, "basiq_user_id": basiq_user_id}


@router.post("/sync")
async def sync_transactions():
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    tenant = (
        supabase.table("tenants")
        .select("basiq_user_id")
        .eq("id", DEMO_TENANT_ID)
        .single()
        .execute()
    )
    if not tenant.data or not tenant.data.get("basiq_user_id"):
        raise HTTPException(
            status_code=400, detail="No Basiq connection. Call /basiq/connect first."
        )

    token = await get_access_token()
    raw_txns = await fetch_transactions(token, tenant.data["basiq_user_id"])

    conn = (
        supabase.table("bank_connections")
        .select("id")
        .eq("tenant_id", DEMO_TENANT_ID)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )
    if not conn.data:
        raise HTTPException(status_code=400, detail="No bank_connection record found.")
    connection_id = conn.data[0]["id"]

    inserted = 0
    for t in raw_txns:
        amount_cents = int(float(t.get("amount", 0)) * 100)
        row = {
            "tenant_id": DEMO_TENANT_ID,
            "connection_id": connection_id,
            "basiq_id": t["id"],
            "amount_cents": amount_cents,
            "currency": t.get("currency", "AUD"),
            "description": t.get("description", ""),
            "description_clean": clean_description(t.get("description", "")),
            "merchant_name": t.get("enrich", {})
            .get("merchant", {})
            .get("businessName"),
            "merchant_category": t.get("enrich", {}).get("category"),
            "transaction_date": t.get("postDate", t.get("transactionDate")),
            "transaction_type": "credit" if amount_cents > 0 else "debit",
            "status": "pending",
            "raw_payload": t,
        }
        result = (
            supabase.table("bank_transactions")
            .upsert(row, on_conflict="basiq_id", ignore_duplicates=True)
            .execute()
        )
        if result.data:
            inserted += len(result.data)

    supabase.table("bank_connections").update({"last_synced_at": "NOW()"}).eq(
        "id", connection_id
    ).execute()

    return {"synced": len(raw_txns), "inserted": inserted}


@router.post("/webhook")
async def basiq_webhook(payload: dict, background_tasks: BackgroundTasks):
    event_type = payload.get("type")
    if event_type in ("job.completed", "connections.refreshed"):
        background_tasks.add_task(sync_transactions)
    return {"received": True}
