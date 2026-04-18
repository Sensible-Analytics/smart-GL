import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-dummy")

from services.llm_categoriser import (
    LLMCategoriser,
    LLMCategoriserInput,
    LLMCategoriserOutput,
    ChartOfAccountsEntry,
    validate_input,
    validate_output,
    VALID_GST_CODES,
    create_llm_categoriser,
)


@pytest.fixture
def sample_coa():
    return [
        ChartOfAccountsEntry(
            code="5000",
            name="Office Supplies",
            account_type="expense",
            gst_code="G1",
            id="uuid-1",
        ),
        ChartOfAccountsEntry(
            code="2000",
            name="Bank Account",
            account_type="asset",
            gst_code="G1",
            id="uuid-2",
        ),
        ChartOfAccountsEntry(
            code="4000",
            name="Sales Revenue",
            account_type="revenue",
            gst_code="G1",
            id="uuid-3",
        ),
    ]


class TestInputValidation:
    def test_empty_description_fails(self, sample_coa):
        inp = LLMCategoriserInput(
            description="",
            amount_aud=100.0,
            direction="expense",
            chart_of_accounts=sample_coa,
        )
        assert "empty description" in validate_input(inp)

    def test_negative_amount_fails(self, sample_coa):
        inp = LLMCategoriserInput(
            description="test",
            amount_aud=-10.0,
            direction="expense",
            chart_of_accounts=sample_coa,
        )
        assert "negative amount" in validate_input(inp)

    def test_invalid_direction_caught_by_pydantic(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LLMCategoriserInput(
                description="test",
                amount_aud=100.0,
                direction="invalid",
                chart_of_accounts=[],
            )

    def test_empty_coa_fails(self):
        inp = LLMCategoriserInput(
            description="test",
            amount_aud=100.0,
            direction="expense",
            chart_of_accounts=[],
        )
        assert "empty chart_of_accounts" in validate_input(inp)

    def test_valid_input_passes(self, sample_coa):
        inp = LLMCategoriserInput(
            description="Bunnings",
            amount_aud=150.0,
            direction="expense",
            chart_of_accounts=sample_coa,
        )
        assert validate_input(inp) == []


class TestOutputValidation:
    def test_confidence_out_of_range_caught_by_pydantic(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LLMCategoriserOutput(
                account_code="5000",
                confidence=1.5,
                requires_review=False,
                reasoning="test",
            )

    def test_missing_account_code_when_not_review_fails(self):
        out = LLMCategoriserOutput(
            account_code=None, confidence=0.9, requires_review=False, reasoning="test"
        )
        assert "missing account_code" in validate_output(out)

    def test_invalid_gst_code_caught_by_validation(self):
        out = LLMCategoriserOutput(
            account_code="5000",
            gst_code="INVALID",
            confidence=0.9,
            requires_review=False,
            reasoning="test",
        )
        errs = validate_output(out)
        assert any("invalid gst_code" in e for e in errs)

    def test_valid_output_passes(self, sample_coa):
        out = LLMCategoriserOutput(
            account_code="5000",
            account_id="uuid-1",
            gst_code="G1",
            confidence=0.85,
            requires_review=False,
            reasoning="test",
        )
        assert validate_output(out) == []


class TestLLMResponseParsing:
    def test_review_response(self):
        categoriser = LLMCategoriser()
        categoriser._coa = []

        out = categoriser._parse("REVIEW\nToo ambiguous")
        assert out.requires_review is True
        assert out.tier == "human"

    def test_valid_response_parses(self):
        categoriser = LLMCategoriser()
        categoriser._coa = [
            ChartOfAccountsEntry(
                code="5000",
                name="Office",
                account_type="expense",
                gst_code="G1",
                id="uuid-1",
            )
        ]

        out = categoriser._parse("5000\nG1\n0.85\nOffice supplies expense")
        assert out.account_code == "5000"
        assert out.gst_code == "G1"
        assert out.confidence == 0.85
        assert out.tier == "llm"

    def test_low_confidence_triggers_review(self):
        categoriser = LLMCategoriser(confidence_threshold=0.70)
        categoriser._coa = [
            ChartOfAccountsEntry(
                code="5000",
                name="Office",
                account_type="expense",
                gst_code="G1",
                id="uuid-1",
            )
        ]

        out = categoriser._parse("5000\nG1\n0.50\nNot sure")
        assert out.requires_review is True
        assert out.tier == "human"

    def test_unknown_account_code_triggers_review(self):
        categoriser = LLMCategoriser()
        categoriser._coa = [
            ChartOfAccountsEntry(
                code="5000",
                name="Office",
                account_type="expense",
                gst_code="G1",
                id="uuid-1",
            )
        ]

        out = categoriser._parse("9999\nG1\n0.85\nRandom")
        assert out.requires_review is True
        assert "Unknown code" in out.reasoning


class TestContractEnforcement:
    def test_input_signature_has_required_fields(self):
        required = ["description", "amount_aud", "direction", "chart_of_accounts"]
        for field in required:
            assert field in LLMCategoriserInput.__annotations__

    def test_output_signature_has_required_fields(self):
        required = ["account_code", "gst_code", "confidence", "requires_review"]
        for field in required:
            assert field in LLMCategoriserOutput.__annotations__

    def test_output_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            LLMCategoriserOutput(
                account_code="5000",
                confidence=0.9,
                requires_review=False,
                reasoning="test",
                extra_field="invalid",
            )

    def test_valid_gst_codes(self):
        assert VALID_GST_CODES == {"G1", "G2", "G3", "G4", "G9", "G11", "N-T"}


class TestEndToEnd:
    @patch.object(LLMCategoriser, "client")
    def test_full_categorisation_flow(self, mock_client, sample_coa):
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text="5000\nG1\n0.90\nOffice supplies for warehouse")
        ]
        mock_client.messages.create.return_value = mock_message

        categoriser = LLMCategoriser()
        inp = LLMCategoriserInput(
            description="BUNNINGS WAREHOUSE",
            amount_aud=250.00,
            direction="expense",
            merchant_name="Bunnings",
            chart_of_accounts=sample_coa,
        )

        out = categoriser.forward(inp)

        assert out.account_code == "5000"
        assert out.account_id == "uuid-1"
        assert out.gst_code == "G1"
        assert out.confidence == 0.90
        assert out.requires_review is False
        assert out.tier == "llm"

    @patch.object(LLMCategoriser, "client")
    def test_review_triggered_on_low_confidence(self, mock_client, sample_coa):
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="5000\nG1\n0.60\nMaybe office supplies")]
        mock_client.messages.create.return_value = mock_message

        categoriser = LLMCategoriser()
        inp = LLMCategoriserInput(
            description="UNKNOWN CHARGE",
            amount_aud=50.00,
            direction="expense",
            chart_of_accounts=sample_coa,
        )

        out = categoriser.forward(inp)

        assert out.requires_review is True
        assert out.tier == "human"


class TestFactory:
    def test_create_with_defaults(self):
        cat = create_llm_categoriser()
        assert cat.model == "claude-sonnet-4-20250514"
        assert cat.confidence_threshold == 0.70

    def test_create_with_overrides(self):
        cat = create_llm_categoriser(model="claude-3-5", confidence_threshold=0.80)
        assert cat.model == "claude-3-5"
        assert cat.confidence_threshold == 0.80
