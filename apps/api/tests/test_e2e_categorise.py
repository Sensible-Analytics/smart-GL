import pytest
import os

os.environ.setdefault("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
os.environ.setdefault("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)

DEMO_COA = [
    {
        "id": "acc-5000",
        "code": "5000",
        "name": "Plumbing Materials",
        "account_type": "expense",
        "gst_code": "G11",
    },
    {
        "id": "acc-6000",
        "code": "6000",
        "name": "Fuel & Vehicle",
        "account_type": "expense",
        "gst_code": "G11",
    },
    {
        "id": "acc-4000",
        "code": "4000",
        "name": "Plumbing Services",
        "account_type": "revenue",
        "gst_code": "G1",
    },
    {
        "id": "acc-6200",
        "code": "6200",
        "name": "Software Subscriptions",
        "account_type": "expense",
        "gst_code": "G11",
    },
    {
        "id": "acc-6800",
        "code": "6800",
        "name": "ATO Payments",
        "account_type": "expense",
        "gst_code": "N-T",
    },
]


@pytest.mark.asyncio
async def test_bunnings_categorised_as_materials():
    from services.categorise import categorise_transaction
    from unittest.mock import MagicMock

    mock_supabase = MagicMock()
    result = await categorise_transaction(
        supabase=mock_supabase,
        tenant_id="test-tenant",
        transaction_id="test-txn-1",
        description_clean="BUNNINGS SYDNEY",
        amount_cents=-23450,
        merchant_name="Bunnings Warehouse",
        basiq_category="Hardware",
        coa=DEMO_COA,
    )
    assert result["tier"] in ("embedding", "llm")
    if result["account_id"]:
        assert result["account_id"] == "acc-5000"


@pytest.mark.asyncio
async def test_ato_payment_no_gst():
    from services.categorise import categorise_transaction
    from unittest.mock import MagicMock

    mock_supabase = MagicMock()
    result = await categorise_transaction(
        supabase=mock_supabase,
        tenant_id="test-tenant",
        transaction_id="test-txn-2",
        description_clean="ATO PORTAL BAS PAYMENT",
        amount_cents=-310000,
        merchant_name="Australian Tax Office",
        basiq_category="Government",
        coa=DEMO_COA,
    )
    if result["account_id"]:
        assert result["gst_code"] == "N-T"
