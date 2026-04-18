import pytest
import asyncio
import os

os.environ.setdefault("FORMANCE_LEDGER_URL", "http://localhost:3068")

from services.formance import post_transaction, get_account_balance


@pytest.mark.asyncio
async def test_post_transaction():
    tx_id = await post_transaction(
        description="TEST-001 Bunnings materials",
        source_address="assets:bank:anz_cheque",
        dest_address="expenses:cogs:materials",
        amount_cents=23450,
        metadata={"test": "true"},
    )
    assert tx_id is not None
    assert len(str(tx_id)) > 0


@pytest.mark.asyncio
async def test_account_balance():
    balance = await get_account_balance("expenses:cogs:materials")
    assert isinstance(balance, dict)
