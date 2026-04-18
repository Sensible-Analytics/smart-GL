import os
import re
import anthropic
from openai import AsyncOpenAI
from supabase import Client
from typing import Optional

from services.llm_categoriser import (
    LLMCategoriser,
    LLMCategoriserInput,
    ChartOfAccountsEntry,
)

anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
SIMILARITY_THRESHOLD = 0.88
LLM_THRESHOLD = 0.70


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
    embedding = await get_embedding(description_clean)

    similar = supabase.rpc(
        "match_embeddings",
        {
            "query_embedding": embedding,
            "tenant_id": tenant_id,
            "match_threshold": SIMILARITY_THRESHOLD,
            "match_count": 1,
        },
    ).execute()

    if similar.data and len(similar.data) > 0:
        top = similar.data[0]
        if top["similarity"] >= SIMILARITY_THRESHOLD:
            return {
                "account_id": top["account_id"],
                "gst_code": top["gst_code"],
                "confidence": float(top["similarity"]),
                "tier": "embedding",
                "reasoning": None,
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
