import os
import re
import anthropic
from openai import AsyncOpenAI
from supabase import Client
from typing import Optional

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

    coa_text = "\n".join(
        f"{a['code']} | {a['name']} | {a['account_type']} | GST:{a['gst_code']}"
        for a in coa
    )
    direction = "income/credit" if amount_cents > 0 else "expense/debit"
    amount_aud = abs(amount_cents) / 100

    prompt = f"""You are an Australian bookkeeper for a small plumbing and trades business.
Categorise the following bank transaction to the correct account in the Chart of Accounts.

Transaction details:
- Description: {description_clean}
- Amount: ${amount_aud:.2f} AUD ({direction})
- Merchant (if known): {merchant_name or "unknown"}
- Bank category (hint only): {basiq_category or "unknown"}

Chart of Accounts:
{coa_text}

Rules:
1. Return ONLY the account code number (e.g. "5000") and nothing else on the first line.
2. On the second line, return the GST code that applies (G1, G2, G3, G4, G9, G11, or N-T).
3. On the third line, return a confidence score between 0.00 and 1.00.
4. On the fourth line, give a one-sentence reason for your choice.

If you cannot determine the correct account with confidence above 0.70, return "REVIEW" on the first line."""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = message.content[0].text.strip()
    lines = response_text.split("\n")

    if lines[0].strip().upper() == "REVIEW" or len(lines) < 4:
        return {
            "account_id": None,
            "gst_code": None,
            "confidence": 0.0,
            "tier": "human",
            "reasoning": response_text,
        }

    code = lines[0].strip()
    gst_code = lines[1].strip()
    try:
        confidence = float(lines[2].strip())
    except ValueError:
        confidence = 0.5
    reasoning = lines[3].strip()

    if confidence < LLM_THRESHOLD:
        return {
            "account_id": None,
            "gst_code": None,
            "confidence": confidence,
            "tier": "human",
            "reasoning": reasoning,
        }

    matched_account = next((a for a in coa if a["code"] == code), None)
    if not matched_account:
        return {
            "account_id": None,
            "gst_code": None,
            "confidence": 0.0,
            "tier": "human",
            "reasoning": f"LLM returned unknown account code: {code}",
        }

    return {
        "account_id": matched_account["id"],
        "gst_code": gst_code,
        "confidence": confidence,
        "tier": "llm",
        "reasoning": reasoning,
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
