from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import get_supabase, set_tenant
from services.categorise import (
    clean_description,
    categorise_transaction,
    store_embedding_feedback,
)

router = APIRouter()

DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"


class ConfirmCategoryRequest(BaseModel):
    account_id: str
    gst_code: str


@router.get("/")
async def list_transactions(
    status: Optional[str] = None, limit: int = Query(50, le=200), offset: int = 0
):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)
    query = (
        supabase.table("bank_transactions")
        .select(
            "*, categorisations(*, accounts(code, name, gst_code)), bank_connections(institution_name, account_name)"
        )
        .is_("deleted_at", None)
        .order("transaction_date", desc=True)
        .range(offset, offset + limit - 1)
    )
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return result.data


@router.post("/{transaction_id}/categorise")
async def run_categorisation(transaction_id: str):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    txn = (
        supabase.table("bank_transactions")
        .select("*")
        .eq("id", transaction_id)
        .single()
        .execute()
    )
    if not txn.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    coa = (
        supabase.table("accounts")
        .select("id, code, name, account_type, gst_code")
        .eq("tenant_id", DEMO_TENANT_ID)
        .is_("deleted_at", None)
        .execute()
        .data
    )

    clean = clean_description(txn.data["description"])
    result = await categorise_transaction(
        supabase=supabase,
        tenant_id=DEMO_TENANT_ID,
        transaction_id=transaction_id,
        description_clean=clean,
        amount_cents=txn.data["amount_cents"],
        merchant_name=txn.data.get("merchant_name"),
        basiq_category=txn.data.get("merchant_category"),
        coa=coa,
    )

    if result["account_id"]:
        supabase.table("bank_transactions").update(
            {"description_clean": clean, "status": "categorised"}
        ).eq("id", transaction_id).execute()

        supabase.table("categorisations").insert(
            {
                "tenant_id": DEMO_TENANT_ID,
                "transaction_id": transaction_id,
                "account_id": result["account_id"],
                "gst_code": result["gst_code"],
                "gst_amount_cents": abs(txn.data["amount_cents"]) * 10 // 110
                if result["gst_code"] not in ("N-T", "G9")
                else 0,
                "confidence": result["confidence"],
                "tier": result["tier"],
                "llm_reasoning": result.get("reasoning"),
                "is_confirmed": result["tier"] == "embedding",
            }
        ).execute()

        if result["tier"] == "embedding":
            await store_embedding_feedback(
                supabase,
                DEMO_TENANT_ID,
                clean,
                result["account_id"],
                result["gst_code"],
            )

    return result


@router.post("/{transaction_id}/confirm")
async def confirm_categorisation(transaction_id: str, body: ConfirmCategoryRequest):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    cat = (
        supabase.table("categorisations")
        .select("*")
        .eq("transaction_id", transaction_id)
        .is_("deleted_at", None)
        .single()
        .execute()
    )
    if not cat.data:
        raise HTTPException(status_code=404, detail="Categorisation not found")

    txn = (
        supabase.table("bank_transactions")
        .select("description_clean, amount_cents")
        .eq("id", transaction_id)
        .single()
        .execute()
    )

    gst_cents = (
        abs(txn.data["amount_cents"]) * 10 // 110
        if body.gst_code not in ("N-T", "G9")
        else 0
    )

    supabase.table("categorisations").update(
        {
            "account_id": body.account_id,
            "gst_code": body.gst_code,
            "gst_amount_cents": gst_cents,
            "is_confirmed": True,
            "tier": "human",
        }
    ).eq("id", cat.data["id"]).execute()

    supabase.table("bank_transactions").update({"status": "categorised"}).eq(
        "id", transaction_id
    ).execute()

    await store_embedding_feedback(
        supabase,
        DEMO_TENANT_ID,
        txn.data["description_clean"],
        body.account_id,
        body.gst_code,
    )
    return {"ok": True}
