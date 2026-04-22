import os
import re
import math
import anthropic
from openai import AsyncOpenAI
from supabase import Client
from typing import Optional

from services.llm_categoriser import (
    LLMCategoriser,
    LLMCategoriserInput,
    ChartOfAccountsEntry,
)

# Use mock values when env vars not set (for testing)
_ant_key = os.environ.get("ANTHROPIC_API_KEY", "mock-key-for-testing")
_openai_key = os.environ.get("OPENAI_API_KEY", "sk-mock-key-for-testing")

try:
    anthropic_client = anthropic.Anthropic(api_key=_ant_key)
except Exception:
    anthropic_client = None

try:
    openai_client = AsyncOpenAI(api_key=_openai_key)
except Exception:
    openai_client = None

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
SIMILARITY_THRESHOLD = 0.80
MATCH_COUNT = 3
LLM_THRESHOLD = 0.80
FEEDBACK_PRIORITY_THRESHOLD = 0.80

MERCHANT_HEURISTICS = {
    "bunnings": ("6000", "G1"),
    "ammers": ("6000", "G1"),
    "mitre 10": ("6000", "G1"),
    "homebase": ("6000", "G1"),
    "ampol": ("6100", "G1"),
    "bp": ("6100", "G1"),
    "shell": ("6100", "G1"),
    "caltex": ("6100", "G1"),
    "mobil": ("6100", "G1"),
    "petrol": ("6100", "G1"),
    "uber": ("6100", "G1"),
    "didi": ("6100", "G1"),
    "oy": ("6100", "G1"),
    "qantas": ("6100", "G1"),
    "virgin": ("6100", "G1"),
    "jetstar": ("6100", "G1"),
    "taxi": ("6100", "G1"),
    "telstra": ("6200", "G1"),
    "optus": ("6200", "G1"),
    "vodafone": ("6200", "G1"),
    "origin energy": ("6200", "G1"),
    "agl": ("6200", "G1"),
    "ausgrid": ("6200", "G1"),
    "citipower": ("6200", "G1"),
    "google": ("6300", "G1"),
    "aws": ("6300", "G1"),
    "microsoft": ("6300", "G1"),
    "xero": ("6300", "G1"),
    "myob": ("6300", "G1"),
    "adobe": ("6300", "G1"),
    "dropbox": ("6300", "G1"),
    "slack": ("6300", "G1"),
    "zoom": ("6300", "G1"),
    "atlassian": ("6300", "G1"),
    "github": ("6300", "G1"),
    "notion": ("6300", "G1"),
    "figma": ("6300", "G1"),
    "canva": ("6300", "G1"),
    "hubspot": ("6300", "G1"),
    "salesforce": ("6300", "G1"),
    "zapier": ("6300", "G1"),
    "airtable": ("6300", "G1"),
    "netflix": ("6300", "G9"),
    "spotify": ("6300", "G9"),
    "disney": ("6300", "G9"),
    "stan": ("6300", "G9"),
    "bank fees": ("6400", "G1"),
    "merchant fees": ("6400", "G1"),
    "transaction fee": ("6400", "G1"),
    "westpac": ("6400", "G1"),
    "anz": ("6400", "G1"),
    "nab": ("6400", "G1"),
    "commonwealth bank": ("6400", "G1"),
    "bendigo bank": ("6400", "G1"),
    "insurance": ("6500", "G1"),
    "qbe": ("6500", "G1"),
    "suncorp": ("6500", "G1"),
    "rent": ("6600", "G1"),
    "chemist": ("6700", "G1"),
    "priceline": ("6700", "G1"),
    "bonds": ("6800", "G1"),
    "kmart": ("6800", "G1"),
    "target": ("6800", "G1"),
    "accountant": ("6900", "G1"),
    "solicitor": ("6900", "G1"),
    "law": ("6900", "G1"),
    "legal": ("6900", "G1"),
    "austpost": ("6900", "G1"),
    "australia post": ("6900", "G1"),
}


def _match_merchant_heuristic(
    description: str, merchant_name: str | None, coa: list[dict]
) -> dict | None:
    search_text = f"{description} {merchant_name or ''}".lower()
    for pattern, (account_code, gst_code) in MERCHANT_HEURISTICS.items():
        if pattern in search_text:
            for account in coa:
                if account.get("code") == account_code:
                    return {
                        "account_id": account["id"],
                        "gst_code": gst_code,
                        "confidence": 0.95,
                        "tier": "heuristic",
                        "reasoning": f"Known merchant: {pattern}",
                    }
    return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


async def match_feedback_embeddings(
    supabase: Client,
    tenant_id: str,
    query_embedding: list[float],
    match_threshold: float = SIMILARITY_THRESHOLD,
    match_count: int = 3,
) -> list[dict]:
    embeddings = (
        supabase.table("categorisation_embeddings")
        .select("id, description_clean, account_id, gst_code, embedding, sample_count")
        .eq("tenant_id", tenant_id)
        .is_("deleted_at", None)
        .execute()
    ).data

    if not embeddings:
        return []

    similarities = []
    for emb in embeddings:
        stored_vector = emb.get("embedding")
        if stored_vector is None:
            continue
        sim = cosine_similarity(query_embedding, stored_vector)
        if sim >= match_threshold:
            similarities.append({
                "id": emb["id"],
                "description_clean": emb["description_clean"],
                "account_id": emb["account_id"],
                "gst_code": emb["gst_code"],
                "similarity": sim,
                "sample_count": emb.get("sample_count", 1),
            })

    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return similarities[:match_count]


async def match_categorisation_embeddings(
    supabase: Client,
    tenant_id: str,
    query_embedding: list[float],
    match_threshold: float = SIMILARITY_THRESHOLD,
    match_count: int = 3,
) -> list[dict]:
    embeddings = (
        supabase.table("categorisation_embeddings")
        .select("id, description_clean, account_id, gst_code, embedding, sample_count")
        .eq("tenant_id", tenant_id)
        .is_("deleted_at", None)
        .execute()
    ).data

    if not embeddings:
        return []

    similarities = []
    for emb in embeddings:
        stored_vector = emb.get("embedding")
        if stored_vector is None:
            continue
        sim = cosine_similarity(query_embedding, stored_vector)
        if sim >= match_threshold:
            similarities.append({
                "id": emb["id"],
                "description_clean": emb["description_clean"],
                "account_id": emb["account_id"],
                "gst_code": emb["gst_code"],
                "similarity": sim,
                "sample_count": emb.get("sample_count", 1),
            })

    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return similarities[:match_count]


def clean_description(raw: str) -> str:
    text = raw.upper()
    text = re.sub(r"\b\d{2}/\d{2}(/\d{2,4})?\b", "", text)
    text = re.sub(r"\b\d{4,}\b", "", text)
    text = re.sub(r"\bCARD\s+\d+\b", "", text)
    text = re.sub(
        r"\bDIRECT\s+DEBIT\b|\bDD\b|\bPOS\b|\bEFTPOS\b|\bVISA\b|\bMC\b", "", text
    )
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


async def get_embedding(text: str) -> list[float]:
    resp = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL, input=text, dimensions=EMBEDDING_DIM
    )
    return resp.data[0].embedding


async def categorise_transaction(
    supabase: Client,
    tenant_id: str,
    transaction_id: str,
    description_clean: str,
    amount_cents: int,
    merchant_name: Optional[str],
    basiq_category: Optional[str],
    coa: list[dict],
    ) -> dict:
    heuristic = _match_merchant_heuristic(description_clean, merchant_name, coa)
    if heuristic:
        return heuristic

    embedding = await get_embedding(description_clean)

    similar = await match_feedback_embeddings(
        supabase, tenant_id, embedding, SIMILARITY_THRESHOLD, MATCH_COUNT
    )

    if similar:
        if len(similar) > 1:
            account_votes: dict[str, tuple[str, float, int]] = {}  # type: ignore[index]
            for match in similar:
                acct_id = match["account_id"]
                if acct_id not in account_votes:
                    account_votes[acct_id] = (match["gst_code"], match["similarity"], match["sample_count"])
                else:
                    existing = account_votes[acct_id]
                    new_count = existing[2] + match["sample_count"]
                    avg_sim = (existing[1] * existing[2] + match["similarity"] * match["sample_count"]) / new_count
                    account_votes[acct_id] = (existing[0], avg_sim, new_count)
            winning_account = max(account_votes.items(), key=lambda x: (x[1][1], x[1][2]))
            final_gst_code, final_confidence, total_votes = winning_account[1]
            confidence_boost = min(0.1, total_votes * 0.02)
            final_confidence = min(0.99, final_confidence + confidence_boost)
            return {
                "account_id": winning_account[0],
                "gst_code": final_gst_code,
                "confidence": final_confidence,
                "tier": "embedding",
                "reasoning": f"Matched with {len(similar)} similar transactions ({total_votes} samples)",
            }
        top = similar[0]
        result_confidence = top["similarity"]
        if result_confidence < FEEDBACK_PRIORITY_THRESHOLD:
            fallback = await match_categorisation_embeddings(
                supabase, tenant_id, embedding, SIMILARITY_THRESHOLD - 0.1, MATCH_COUNT
            )
            if fallback and fallback[0]["similarity"] > result_confidence:
                fb = fallback[0]
                return {
                    "account_id": fb["account_id"],
                    "gst_code": fb["gst_code"],
                    "confidence": fb["similarity"],
                    "tier": "embedding",
                    "reasoning": "Fallback match from feedback store",
                }
        return {
            "account_id": top["account_id"],
            "gst_code": top["gst_code"],
            "confidence": result_confidence,
            "tier": "embedding",
            "reasoning": None,
        }

    fallback = await match_categorisation_embeddings(
        supabase, tenant_id, embedding, SIMILARITY_THRESHOLD - 0.1, MATCH_COUNT
    )
    if fallback:
        fb = fallback[0]
        return {
            "account_id": fb["account_id"],
            "gst_code": fb["gst_code"],
            "confidence": fb["similarity"],
            "tier": "embedding",
            "reasoning": "Fallback match from feedback store",
        }

    direction = "income" if amount_cents > 0 else "expense"
    amount_aud = abs(amount_cents) / 100

    coa_entries = [
        ChartOfAccountsEntry(
            code=a["code"],
            name=a["name"],
            account_type=a["account_type"],
            gst_code=a["gst_code"],
            id=a.get("id"),
        )
        for a in coa
    ]

    categoriser = LLMCategoriser(confidence_threshold=LLM_THRESHOLD)
    input_data = LLMCategoriserInput(
        description=description_clean,
        amount_aud=amount_aud,
        direction=direction,
        merchant_name=merchant_name,
        basiq_category=basiq_category,
        chart_of_accounts=coa_entries,
    )
    output = categoriser.forward(input_data)

    return {
        "account_id": output.account_id,
        "gst_code": output.gst_code,
        "confidence": output.confidence,
        "tier": output.tier,
        "reasoning": output.reasoning,
    }


async def store_embedding_feedback(
    supabase: Client,
    tenant_id: str,
    description_clean: str,
    account_id: str,
    gst_code: str,
) -> None:
    embedding = await get_embedding(description_clean)
    supabase.table("categorisation_embeddings").upsert(
        {
            "tenant_id": tenant_id,
            "description_clean": description_clean,
            "account_id": account_id,
            "gst_code": gst_code,
            "embedding": embedding,
            "sample_count": 1,
        },
        on_conflict="tenant_id,description_clean,account_id",
    ).execute()
