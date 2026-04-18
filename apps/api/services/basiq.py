import os
import base64
import httpx
from typing import Any

BASIQ_BASE_URL = os.environ.get("BASIQ_BASE_URL", "https://au-api.basiq.io")


async def get_access_token() -> str:
    api_key = os.environ["BASIQ_API_KEY"]
    credentials = base64.b64encode(f"{api_key}:".encode()).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASIQ_BASE_URL}/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "basiq-version": "3.0",
            },
            data={"scope": "SERVER_ACCESS"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def create_basiq_user(token: str, email: str, mobile: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASIQ_BASE_URL}/users",
            headers={"Authorization": f"Bearer {token}", "basiq-version": "3.0"},
            json={"email": email, "mobile": mobile},
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def get_auth_link(token: str, basiq_user_id: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASIQ_BASE_URL}/auth/links",
            headers={"Authorization": f"Bearer {token}", "basiq-version": "3.0"},
            json={"userId": basiq_user_id},
        )
        resp.raise_for_status()
        return resp.json()["links"]["public"]


async def fetch_transactions(
    token: str, basiq_user_id: str, from_date: str = None, limit: int = 500
) -> list[dict[str, Any]]:
    from datetime import date, timedelta

    if not from_date:
        from_date = (date.today() - timedelta(days=30)).isoformat()

    params = {"filter": f"transaction.postDate.gte:{from_date}", "limit": limit}
    transactions = []
    url = f"{BASIQ_BASE_URL}/users/{basiq_user_id}/transactions"

    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}", "basiq-version": "3.0"},
                params=params
                if url == f"{BASIQ_BASE_URL}/users/{basiq_user_id}/transactions"
                else None,
            )
            resp.raise_for_status()
            data = resp.json()
            transactions.extend(data.get("data", []))
            next_link = data.get("links", {}).get("next")
            url = next_link if next_link else None
            params = None

    return transactions
