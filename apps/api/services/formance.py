import os
import httpx
from typing import Any

FORMANCE_URL = os.environ.get("FORMANCE_LEDGER_URL", "http://localhost:3068")
LEDGER_NAME = "smartgl"


async def post_transaction(
    description: str,
    source_address: str,
    dest_address: str,
    amount_cents: int,
    currency: str = "AUD",
    metadata: dict[str, Any] = None,
) -> str:
    payload = {
        "postings": [
            {
                "source": source_address,
                "destination": dest_address,
                "amount": amount_cents,
                "asset": f"{currency}/2",
            }
        ],
        "metadata": metadata or {},
        "reference": description[:255],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FORMANCE_URL}/v2/{LEDGER_NAME}/transactions", json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data["data"][0]["id"])


async def get_account_balance(address: str) -> dict[str, int]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{FORMANCE_URL}/v2/{LEDGER_NAME}/accounts/{address}")
        resp.raise_for_status()
        account = resp.json()["data"]
        return account.get("volumes", {})
