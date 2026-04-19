import os
import httpx
from typing import Any, Dict, Optional

BASIQ_API_KEY = os.environ.get("BASIQ_API_KEY", "mock-key-for-testing")

async def get_transactions(
    access_token: str,
    account_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Basiq-Version": "2020-10-01",
    }
    params = {
        "accountId": account_id,
        "limit": limit,
    }
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.basiq.io/v2/transactions",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

async def get_accounts(access_token: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Basiq-Version": "2020-10-01",
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.basiq.io/v2/accounts",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()
