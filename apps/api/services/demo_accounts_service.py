import os
import asyncpg
from typing import List, Optional
from pydantic import BaseModel

NEON_DSN = os.environ.get(
    "NEON_CONNECTION",
    "postgresql://neondb_owner:npg_0sSKnLJZUeW4@ep-morning-water-antdyysm-pooler.c-6.us-east-1.aws.neon.tech/neondb"
)

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=NEON_DSN, min_size=1, max_size=10)
    return _pool


class DemoAccount(BaseModel):
    id: str
    name: str
    account_no: str
    balance: float
    type: str
    institution: str


async def get_demo_accounts() -> List[DemoAccount]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, account_no, balance, type, institution FROM demo_accounts"
        )
        return [
            DemoAccount(
                id=str(row["id"]),
                name=row["name"],
                account_no=row["account_no"],
                balance=float(row["balance"]),
                type=row["type"],
                institution=row["institution"],
            )
            for row in rows
        ]


async def get_demo_account_by_id(account_id: str) -> Optional[DemoAccount]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, account_no, balance, type, institution FROM demo_accounts WHERE id = $1",
            account_id,
        )
        if not row:
            return None
        return DemoAccount(
            id=str(row["id"]),
            name=row["name"],
            account_no=row["account_no"],
            balance=float(row["balance"]),
            type=row["type"],
            institution=row["institution"],
        )