import os
import anthropic
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ChartOfAccountsEntry(BaseModel):
    code: str
    name: str
    account_type: Literal["asset", "liability", "equity", "revenue", "expense"]
    gst_code: str
    id: Optional[str] = None


class LLMCategoriserInput(BaseModel):
    description: str
    amount_aud: float
    direction: Literal["income", "expense"]
    merchant_name: Optional[str] = None
    basiq_category: Optional[str] = None
    chart_of_accounts: List[ChartOfAccountsEntry]

    class Config:
        extra = "forbid"


class LLMCategoriserOutput(BaseModel):
    account_code: Optional[str] = None
    account_id: Optional[str] = None
    gst_code: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool
    reasoning: str = ""
    tier: Literal["llm", "human"] = "human"

    class Config:
        extra = "forbid"


VALID_GST_CODES = {"G1", "G2", "G3", "G4", "G9", "G11", "N-T"}


def validate_input(i: LLMCategoriserInput) -> List[str]:
    errors = []
    if not i.description or not i.description.strip():
        errors.append("empty description")
    if i.amount_aud < 0:
        errors.append("negative amount")
    if i.direction not in ("income", "expense"):
        errors.append(f"invalid direction: {i.direction}")
    if not i.chart_of_accounts:
        errors.append("empty chart_of_accounts")
    return errors


def validate_output(o: LLMCategoriserOutput) -> List[str]:
    errors = []
    if not (0.0 <= o.confidence <= 1.0):
        errors.append(f"invalid confidence: {o.confidence}")
    if not o.requires_review and o.account_code is None:
        errors.append("missing account_code")
    if o.gst_code and o.gst_code not in VALID_GST_CODES:
        errors.append(f"invalid gst_code: {o.gst_code}")
    return errors


class LLMCategoriser:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        confidence_threshold: float = 0.70,
        max_tokens: int = 150,
    ):
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.max_tokens = max_tokens
        self._client: Optional[anthropic.Anthropic] = None
        self._coa: List[ChartOfAccountsEntry] = []

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self._client = anthropic.Anthropic(api_key=key)
        return self._client

    def _prompt(self, inp: LLMCategoriserInput) -> str:
        coa_text = "\n".join(
            f"{a.code} | {a.name} | {a.account_type} | GST:{a.gst_code}"
            for a in inp.chart_of_accounts
        )
        direction = "income/credit" if inp.direction == "income" else "expense/debit"

        return f"""You are an Australian bookkeeper for a small plumbing and trades business.
Categorise the following bank transaction to the correct account in the Chart of Accounts.

Transaction details:
- Description: {inp.description}
- Amount: ${inp.amount_aud:.2f} AUD ({direction})
- Merchant: {inp.merchant_name or "unknown"}
- Bank category: {inp.basiq_category or "unknown"}

Chart of Accounts:
{coa_text}

Rules:
1. Return ONLY the account code number (e.g. "5000") on the first line.
2. Return the GST code (G1, G2, G3, G4, G9, G11, or N-T) on the second line.
3. Return a confidence score between 0.00 and 1.00 on the third line.
4. Give a one-sentence reason on the fourth line.

If confidence below {self.confidence_threshold:.2f}, return "REVIEW" on the first line."""

    def _parse(self, text: str) -> LLMCategoriserOutput:
        lines = [line.strip() for line in text.strip().split("\n")]

        if not lines or lines[0].upper() == "REVIEW":
            return LLMCategoriserOutput(
                account_code=None,
                account_id=None,
                gst_code=None,
                confidence=0.0,
                requires_review=True,
                reasoning="LLM requested review",
                tier="human",
            )

        if len(lines) < 4:
            return LLMCategoriserOutput(
                account_code=None,
                account_id=None,
                gst_code=None,
                confidence=0.0,
                requires_review=True,
                reasoning=f"Incomplete: {text[:100]}",
                tier="human",
            )

        code, gst_code = lines[0].strip(), lines[1].strip()

        try:
            confidence = float(lines[2].strip())
        except (ValueError, IndexError):
            confidence = 0.5

        reasoning = lines[3].strip()
        requires_review = confidence < self.confidence_threshold

        matched = None
        for coa in self._coa:
            if coa.code == code:
                matched = coa
                break

        if not matched:
            return LLMCategoriserOutput(
                account_code=code,
                account_id=None,
                gst_code=gst_code if gst_code in VALID_GST_CODES else None,
                confidence=confidence,
                requires_review=True,
                reasoning=f"Unknown code: {code}. {reasoning}",
                tier="human",
            )

        return LLMCategoriserOutput(
            account_code=code,
            account_id=matched.id,
            gst_code=gst_code if gst_code in VALID_GST_CODES else matched.gst_code,
            confidence=confidence,
            requires_review=requires_review,
            reasoning=reasoning,
            tier="llm" if not requires_review else "human",
        )

    def forward(self, inp: LLMCategoriserInput) -> LLMCategoriserOutput:
        self._coa = inp.chart_of_accounts

        errs = validate_input(inp)
        if errs:
            return LLMCategoriserOutput(
                account_code=None,
                account_id=None,
                gst_code=None,
                confidence=0.0,
                requires_review=True,
                reasoning=f"Input error: {', '.join(errs)}",
                tier="human",
            )

        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": self._prompt(inp)}],
            )
            resp = msg.content[0].text.strip()
        except Exception as e:
            return LLMCategoriserOutput(
                account_code=None,
                account_id=None,
                gst_code=None,
                confidence=0.0,
                requires_review=True,
                reasoning=f"LLM error: {str(e)}",
                tier="human",
            )

        out = self._parse(resp)
        out_errs = validate_output(out)
        if out_errs:
            out.reasoning += f" | Validation: {', '.join(out_errs)}"

        return out


def create_llm_categoriser(
    model: Optional[str] = None, confidence_threshold: Optional[float] = None, **kwargs
) -> LLMCategoriser:
    return LLMCategoriser(
        model=model or "claude-sonnet-4-20250514",
        confidence_threshold=confidence_threshold or 0.70,
        max_tokens=kwargs.get("max_tokens", 150),
    )
