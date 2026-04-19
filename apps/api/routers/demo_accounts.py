from fastapi import APIRouter, HTTPException
from typing import List
from services.demo_accounts_service import get_demo_accounts, get_demo_account_by_id, DemoAccount

router = APIRouter()


@router.get("/demo-accounts", response_model=List[DemoAccount])
async def demo_accounts():
    return await get_demo_accounts()


@router.get("/demo-accounts/{account_id}", response_model=DemoAccount)
async def demo_account(account_id: str):
    account = await get_demo_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Demo account not found")
    return account