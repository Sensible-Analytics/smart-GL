import os
import base64
import asyncio
from typing import Any, Optional
import httpx

BASIQ_BASE_URL = os.environ.get("BASIQ_BASE_URL", "https://au-api.basiq.io")


class BasiqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    async def get_token(self) -> str:
        credentials = base64.b64encode(f"{self.api_key}:".encode()).decode()
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
            data = resp.json()
            self.access_token = data["access_token"]
            return self.access_token

    async def create_user(self, email: str, mobile: str) -> str:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASIQ_BASE_URL}/users",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
                json={"email": email, "mobile": mobile},
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def get_user(self, user_id: str) -> dict:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASIQ_BASE_URL}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_user(self, user_id: str) -> bool:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BASIQ_BASE_URL}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
            )
            return resp.status_code == 204

    async def create_connection(self, user_id: str, institution_id: str, login_id: str, password: str) -> dict:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASIQ_BASE_URL}/users/{user_id}/connections",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
                json={"institutionId": institution_id, "loginId": login_id, "password": password},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_connections(self, user_id: str) -> list:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASIQ_BASE_URL}/users/{user_id}/connections",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
            )
            resp.raise_for_status()
            return resp.json().get("data", [])

    async def delete_connection(self, user_id: str, connection_id: str) -> bool:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BASIQ_BASE_URL}/users/{user_id}/connections/{connection_id}",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
            )
            return resp.status_code == 204

    async def get_accounts(self, user_id: str) -> list:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASIQ_BASE_URL}/users/{user_id}/accounts",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
            )
            resp.raise_for_status()
            return resp.json().get("data", [])

    async def get_transactions(
        self, user_id: str, from_date: Optional[str] = None, limit: int = 500
    ) -> list:
        if not self.access_token:
            await self.get_token()
        from datetime import date, timedelta
        if not from_date:
            from_date = (date.today() - timedelta(days=30)).isoformat()
        params = {"filter": f"transaction.postDate.gte:{from_date}", "limit": limit}
        transactions = []
        url = f"{BASIQ_BASE_URL}/users/{user_id}/transactions"
        async with httpx.AsyncClient() as client:
            while url:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                transactions.extend(data.get("data", []))
                url = data.get("links", {}).get("next")
                params = None
        return transactions

    async def get_identity(self, user_id: str) -> dict:
        if not self.access_token:
            await self.get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASIQ_BASE_URL}/users/{user_id}/identity",
                headers={"Authorization": f"Bearer {self.access_token}", "basiq-version": "3.0"},
            )
            resp.raise_for_status()
            return resp.json()


if __name__ == "__main__":
    import asyncio

    async def main():
        client = BasiqClient(os.environ["BASIQ_API_KEY"])
        user_id = await client.create_user("test@example.com", "+61412345678")
        print("User:", user_id)
        accounts = await client.get_accounts(user_id)
        print("Accounts:", accounts)
        transactions = await client.get_transactions(user_id)
        print("Transactions:", len(transactions))

    asyncio.run(main())