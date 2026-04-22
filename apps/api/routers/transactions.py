from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from db import get_supabase, set_tenant
from services.categorise import (
    clean_description,
    categorise_transaction,
    store_embedding_feedback,
)

router = APIRouter()

DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"
AUTO_CONFIRM_CONFIDENCE_THRESHOLD = 0.85


class ConfirmCategoryRequest(BaseModel):
    account_id: str
    gst_code: str
    correction_reason: Optional[str] = None


class BatchCategoriseResponse(BaseModel):
    total: int
    auto_categorised: int
    needs_review: int
    results: List[dict]


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


@router.post("/batch/categorise")
async def batch_categorise(limit: int = Query(50, le=200)) -> BatchCategoriseResponse:
    """Auto-categorise uncategorised transactions above confidence threshold."""
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    # Get uncategorised transactions
    uncategorised = (
        supabase.table("bank_transactions")
        .select("id, description, amount_cents, merchant_name, merchant_category, transaction_date")
        .is_("deleted_at", None)
        .eq("status", "pending")
        .order("transaction_date", desc=True)
        .limit(limit)
        .execute()
    )

    if not uncategorised.data:
        return BatchCategoriseResponse(total=0, auto_categorised=0, needs_review=0, results=[])

    # Get Chart of Accounts
    coa = (
        supabase.table("accounts")
        .select("id, code, name, account_type, gst_code")
        .eq("tenant_id", DEMO_TENANT_ID)
        .is_("deleted_at", None)
        .execute()
        .data
    )

    if not coa:
        raise HTTPException(status_code=400, detail="No chart of accounts configured")

    results = []
    auto_categorised = 0
    needs_review = 0

    for txn in uncategorised.data:
        clean = clean_description(txn["description"])
        result = await categorise_transaction(
            supabase=supabase,
            tenant_id=DEMO_TENANT_ID,
            transaction_id=txn["id"],
            description_clean=clean,
            amount_cents=txn["amount_cents"],
            merchant_name=txn.get("merchant_name"),
            basiq_category=txn.get("merchant_category"),
            coa=coa,
        )

        if result["account_id"]:
            # Determine if auto-confirmed
            auto_confirm = (
                result["tier"] in ("embedding", "heuristic")
                or result["confidence"] >= AUTO_CONFIRM_CONFIDENCE_THRESHOLD
            )

            gst_cents = (
                abs(txn["amount_cents"]) * 10 // 110
                if result["gst_code"] not in ("N-T", "G9")
                else 0
            )

            supabase.table("bank_transactions").update(
                {"description_clean": clean, "status": "pending_review" if not auto_confirm else "categorised"}
            ).eq("id", txn["id"]).execute()

            supabase.table("categorisations").insert(
                {
                    "tenant_id": DEMO_TENANT_ID,
                    "transaction_id": txn["id"],
                    "account_id": result["account_id"],
                    "gst_code": result["gst_code"],
                    "gst_amount_cents": gst_cents,
                    "confidence": result["confidence"],
                    "tier": result["tier"],
                    "llm_reasoning": result.get("reasoning"),
                    "is_confirmed": auto_confirm,
                }
            ).execute()

            if auto_confirm:
                # Store embedding feedback for embedding-tier categorisations
                if result["tier"] == "embedding":
                    await store_embedding_feedback(
                        supabase,
                        DEMO_TENANT_ID,
                        clean,
                        result["account_id"],
                        result["gst_code"],
                    )
                auto_categorised += 1
            else:
                needs_review += 1

            results.append({
                "transaction_id": txn["id"],
                "account_id": result["account_id"],
                "confidence": result["confidence"],
                "tier": result["tier"],
                "auto_confirmed": auto_confirm,
            })
        else:
            needs_review += 1
            results.append({
                "transaction_id": txn["id"],
                "account_id": None,
                "confidence": 0,
                "tier": None,
                "auto_confirmed": False,
            })

    return BatchCategoriseResponse(
        total=len(uncategorised.data),
        auto_categorised=auto_categorised,
        needs_review=needs_review,
        results=results,
    )


@router.get("/stats/automation")
async def get_automation_stats():
    """Get automation statistics for categorised transactions."""
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    # Total categorised transactions
    total = (
        supabase.table("categorisations")
        .select("id", count="exact")
        .is_("deleted_at", None)
        .execute()
    )

    # Auto-confirmed (embedding tier OR high confidence LLM)
    auto_confirmed = (
        supabase.table("categorisations")
        .select("id", count="exact")
        .is_("deleted_at", None)
        .eq("is_confirmed", True)
        .execute()
    )

    # Pending review count
    pending = (
        supabase.table("bank_transactions")
        .select("id", count="exact")
        .is_("deleted_at", None)
        .eq("status", "pending_review")
        .execute()
    )

    total_count = total.count or 0
    auto_count = auto_confirmed.count or 0
    automation_pct = (auto_count / total_count * 100) if total_count > 0 else 0

    return {
        "total_categorised": total_count,
        "auto_confirmed": auto_count,
        "pending_review": pending.count or 0,
        "automation_percentage": round(automation_pct, 1),
    }


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

    original_account_id = cat.data.get("account_id")
    was_corrected = original_account_id != body.account_id

    gst_cents = (
        abs(txn.data["amount_cents"]) * 10 // 110
        if body.gst_code not in ("N-T", "G9")
        else 0
    )

    update_data = {
        "account_id": body.account_id,
        "gst_code": body.gst_code,
        "gst_amount_cents": gst_cents,
        "is_confirmed": True,
        "tier": "human",
    }

    changed_fields = []
    if was_corrected:
        update_data["original_account_id"] = original_account_id
        update_data["corrected_by"] = DEMO_TENANT_ID
        update_data["corrected_at"] = "now()"
        changed_fields.append("account_id")
    if cat.data.get("gst_code") != body.gst_code:
        changed_fields.append("gst_code")
    if body.correction_reason:
        update_data["correction_reason"] = body.correction_reason

    supabase.table("categorisations").update(update_data).eq("id", cat.data["id"]).execute()

    if was_corrected:
        supabase.table("categorisation_audit_log").insert({
            "tenant_id": DEMO_TENANT_ID,
            "categorisation_id": cat.data["id"],
            "transaction_id": transaction_id,
            "original_account_id": original_account_id,
            "new_account_id": body.account_id,
            "original_gst_code": cat.data.get("gst_code"),
            "new_gst_code": body.gst_code,
            "correction_reason": body.correction_reason,
            "changed_fields": changed_fields,
            "corrected_by": DEMO_TENANT_ID,
        }).execute()

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
    return {"ok": True, "was_corrected": was_corrected}


class BatchConfirmRequest(BaseModel):
    transaction_ids: List[str]
    account_id: str
    gst_code: str = "G1"


@router.post("/batch/confirm")
async def batch_confirm_categorisations(body: BatchConfirmRequest):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    confirmed = 0
    for txn_id in body.transaction_ids:
        txn = (
            supabase.table("bank_transactions")
            .select("id, amount_cents, description_clean")
            .eq("id", txn_id)
            .single()
            .execute()
        )
        if not txn.data:
            continue

        gst_cents = (
            abs(txn.data["amount_cents"]) * 10 // 110
            if body.gst_code not in ("N-T", "G9")
            else 0
        )

        supabase.table("categorisations").upsert(
            {
                "tenant_id": DEMO_TENANT_ID,
                "transaction_id": txn_id,
                "account_id": body.account_id,
                "gst_code": body.gst_code,
                "gst_amount_cents": gst_cents,
                "is_confirmed": True,
                "tier": "human",
            },
            on_conflict="tenant_id,transaction_id",
        ).execute()

        supabase.table("bank_transactions").update(
            {"status": "categorised"}
        ).eq("id", txn_id).execute()

        confirmed += 1

    return {"confirmed": confirmed, "total": len(body.transaction_ids)}


@router.get("/pending-review")
async def get_pending_review(
    limit: int = Query(20, le=100), offset: int = 0
):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    result = (
        supabase.table("bank_transactions")
        .select("*, categorisations(*, accounts(code, name))")
        .eq("tenant_id", DEMO_TENANT_ID)
        .eq("status", "pending_review")
        .is_("deleted_at", None)
        .order("transaction_date", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data


@router.get("/audit-log")
async def get_audit_log(
    limit: int = Query(50, le=200), offset: int = 0
):
    supabase = get_supabase()
    set_tenant(supabase, DEMO_TENANT_ID)

    result = (
        supabase.table("categorisation_audit_log")
        .select("""
            id,
            transaction_id,
            original_account_id,
            new_account_id,
            original_gst_code,
            new_gst_code,
            correction_reason,
            changed_fields,
            corrected_by,
            created_at
        """)
        .eq("tenant_id", DEMO_TENANT_ID)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data
