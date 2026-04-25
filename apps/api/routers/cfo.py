"""
CFO Assistant API Router
Smart Q&A, Anomaly Detection, Month-End Briefings, Cash Flow, Benchmarks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/cfo", tags=["cfo"])

DEMO_TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"


# Request/Response Models

class QueryRequest(BaseModel):
    question: str
    period: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    follow_up_questions: List[str]


class AnomalyResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    detected_at: str
    status: str
    transaction_id: Optional[str] = None


class AnomalyListResponse(BaseModel):
    total: int
    high: int
    medium: int
    low: int
    anomalies: List[AnomalyResponse]


class BriefingMetrics(BaseModel):
    revenue_cents: int
    expenses_cents: int
    profit_cents: int
    revenue_change_pct: float
    expense_change_pct: float
    profit_change_pct: float
    burn_rate_cents: int
    runway_months: Optional[float] = None


class InsightItem(BaseModel):
    title: str
    description: str
    severity: Optional[str] = None


class TrendItem(BaseModel):
    metric: str
    direction: str
    change_pct: float


class BriefingInsights(BaseModel):
    items_to_investigate: List[InsightItem]
    positive_items: List[InsightItem]
    trends: List[TrendItem]


class BriefingResponse(BaseModel):
    month_year: str
    metrics: BriefingMetrics
    insights: BriefingInsights
    generated_at: str
    is_draft: bool = True


class CashFlowSnapshot(BaseModel):
    month_year: str
    opening_cents: int
    inflows_cents: int
    outflows_cents: int
    closing_cents: int
    risk_flags: List[str]


class CashFlowForecast(BaseModel):
    current: CashFlowSnapshot
    forecast_7_days: Optional[CashFlowSnapshot] = None
    forecast_14_days: Optional[CashFlowSnapshot] = None
    forecast_30_days: Optional[CashFlowSnapshot] = None
    runway_status: str
    runway_months: Optional[float] = None


class BenchmarkMetric(BaseModel):
    metric_name: str
    tenant_value: float
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    percentile: int


class BenchmarkResponse(BaseModel):
    industry_code: str
    industry_name: str
    period: str
    metrics: List[BenchmarkMetric]
    overall_percentile: Optional[int] = None


# Mock Data

MOCK_ANOMALIES = [
    {
        "id": "ano-001",
        "type": "duplicate",
        "severity": "high",
        "title": "Duplicate payment detected",
        "description": "Same vendor ($4,250) paid twice in March",
        "detected_at": "2026-04-15T10:30:00Z",
        "status": "open",
        "transaction_id": "txn-8942",
    },
    {
        "id": "ano-002",
        "type": "unusual_vendor",
        "severity": "medium",
        "title": "Unusual vendor transaction",
        "description": "First payment to new vendor: $12,000",
        "detected_at": "2026-04-14T08:15:00Z",
        "status": "investigating",
    },
    {
        "id": "ano-003",
        "type": "missing_receipt",
        "severity": "low",
        "title": "Missing receipt",
        "description": "12 transactions over $500 missing receipts",
        "detected_at": "2026-04-10T14:00:00Z",
        "status": "open",
    },
]

MOCK_BRIEFING = {
    "month_year": "2026-03",
    "metrics": {
        "revenue_cents": 12750000,
        "expenses_cents": 8920000,
        "profit_cents": 3830000,
        "revenue_change_pct": 12.5,
        "expense_change_pct": 8.2,
        "profit_change_pct": 22.1,
        "burn_rate_cents": 297333,
        "runway_months": 8.5,
    },
    "insights": {
        "items_to_investigate": [
            {
                "title": "Rising marketing spend",
                "description": "Marketing expenses up 45% vs last quarter - verify campaign ROI",
                "severity": "medium",
            },
            {
                "title": "Unmatched receipts batch",
                "description": "12 transactions over $500 missing receipts in March",
                "severity": "low",
            },
            {
                "title": "Contractor vs employee review",
                "description": "3 contractors approaching FTE threshold - review tax implications",
                "severity": "high",
            },
        ],
        "positive_items": [
            {
                "title": "Strong revenue growth",
                "description": "March revenue 12.5% above forecast",
            },
            {
                "title": "Gross margin improvement",
                "description": "Margin expanded 2.1pp to 38.2%",
            },
        ],
        "trends": [
            {"metric": "Revenue", "direction": "up", "change_pct": 12.5},
            {"metric": "Expenses", "direction": "up", "change_pct": 8.2},
            {"metric": "Profit", "direction": "up", "change_pct": 22.1},
        ],
    },
    "generated_at": "2026-04-01T08:00:00Z",
    "is_draft": False,
}

MOCK_CASH_FLOW = {
    "current": {
        "month_year": "2026-04",
        "opening_cents": 2450000,
        "inflows_cents": 4200000,
        "outflows_cents": 3800000,
        "closing_cents": 2850000,
        "risk_flags": [],
    },
    "forecast_7_days": {
        "month_year": "2026-04",
        "opening_cents": 2850000,
        "inflows_cents": 850000,
        "outflows_cents": 1200000,
        "closing_cents": 2500000,
        "risk_flags": ["BAS payment due"],
    },
    "forecast_14_days": {
        "month_year": "2026-04",
        "opening_cents": 2500000,
        "inflows_cents": 1100000,
        "outflows_cents": 1500000,
        "closing_cents": 2100000,
        "risk_flags": ["BAS payment due", "Low cash buffer"],
    },
    "forecast_30_days": {
        "month_year": "2026-04",
        "opening_cents": 2100000,
        "inflows_cents": 3200000,
        "outflows_cents": 4100000,
        "closing_cents": 1200000,
        "risk_flags": ["BAS payment due", "Low cash buffer", "Consider invoice financing"],
    },
    "runway_status": "watch",
    "runway_months": 4.2,
}

MOCK_BENCHMARKS = {
    "industry_code": "services",
    "industry_name": "Professional Services",
    "period": "2026-03",
    "metrics": [
        {"metric_name": "gross_margin", "tenant_value": 48.5, "p10": 35.0, "p25": 42.0, "p50": 52.0, "p75": 60.0, "p90": 68.0, "percentile": 42},
        {"metric_name": "net_profit", "tenant_value": 12.1, "p10": 2.5, "p25": 5.0, "p50": 8.5, "p75": 12.0, "p90": 16.0, "percentile": 68},
        {"metric_name": "opex_ratio", "tenant_value": 62.0, "p10": 45.0, "p25": 52.0, "p50": 58.0, "p65": 65.0, "p90": 75.0, "percentile": 58},
    ],
    "overall_percentile": 48,
}


# Routes

@router.post("/query", response_model=QueryResponse)
async def smart_query(req: QueryRequest):
    """Smart Q&A - ask questions about your finances."""
    question_lower = req.question.lower()
    
    if "revenue" in question_lower or "sales" in question_lower:
        answer = f"March revenue was ${MOCK_BRIEFING['metrics']['revenue_cents']/100:,.2f}, up {MOCK_BRIEFING['metrics']['revenue_change_pct']}% from February. This was driven by new customer acquisitions in the first quarter."
    elif "expense" in question_lower or "spent" in question_lower:
        answer = f"March expenses were ${MOCK_BRIEFING['metrics']['expenses_cents']/100:,.2f}, up {MOCK_BRIEFING['metrics']['expense_change_pct']}% from February. The increase was primarily due to marketing spend (up 45%)."
    elif "profit" in question_lower or "margin" in question_lower:
        answer = f"March profit was ${MOCK_BRIEFING['metrics']['profit_cents']/100:,.2f}, up {MOCK_BRIEFING['metrics']['profit_change_pct']}% from February. Gross margin expanded to 38.2%."
    elif "cash" in question_lower or "runway" in question_lower:
        answer = f"Current cash position is ${MOCK_CASH_FLOW['current']['closing_cents']/100:,.2f}. With current burn rate, you have {MOCK_CASH_FLOW['runway_months']:.1f} months of runway. Watch for the BAS payment due in 14 days."
    elif "anomal" in question_lower or "issue" in question_lower or "problem" in question_lower:
        count = len(MOCK_ANOMALIES)
        high = sum(1 for a in MOCK_ANOMALIES if a["severity"] == "high")
        answer = f"Found {count} anomalies: {high} high severity, {sum(1 for a in MOCK_ANOMALIES if a['severity'] == 'medium')} medium, {sum(1 for a in MOCK_ANOMALIES if a['severity'] == 'low')} low. Most urgent: Duplicate payment of $4,250 detected."
    else:
        answer = f"I can help with revenue, expenses, profit, cash flow, or anomaly analysis. You have ${MOCK_CASH_FLOW['current']['closing_cents']/100:,.2f} in cash with {MOCK_CASH_FLOW['runway_months']:.1f} months runway. March profit was ${MOCK_BRIEFING['metrics']['profit_cents']/100:,.2f}."
    
    follow_ups = [
        "What drove the revenue change?",
        "What are the top expenses?",
        "What's the cash forecast?",
    ]
    
    return QueryResponse(
        answer=answer,
        sources=[{"type": "mock", "date": "2026-03"}],
        follow_up_questions=follow_ups,
    )


@router.get("/anomalies", response_model=AnomalyListResponse)
async def get_anomalies(limit: int = 10):
    """Get financial anomalies detected."""
    anomalies = [AnomalyResponse(**a) for a in MOCK_ANOMALIES[:limit]]
    return AnomalyListResponse(
        total=len(MOCK_ANOMALIES),
        high=sum(1 for a in MOCK_ANOMALIES if a["severity"] == "high"),
        medium=sum(1 for a in MOCK_ANOMALIES if a["severity"] == "medium"),
        low=sum(1 for a in MOCK_ANOMALIES if a["severity"] == "low"),
        anomalies=anomalies,
    )


@router.get("/briefing/{period}", response_model=BriefingResponse)
async def get_briefing(period: str):
    """Get month-end briefing for specified period."""
    if MOCK_BRIEFING["month_year"] != period:
        raise HTTPException(
            status_code=404,
            detail=f"Briefing not found for period {period}. Available: 2026-03",
        )
    
    return BriefingResponse(
        month_year=MOCK_BRIEFING["month_year"],
        metrics=BriefingMetrics(**MOCK_BRIEFING["metrics"]),
        insights=BriefingInsights(
            items_to_investigate=[InsightItem(**i) for i in MOCK_BRIEFING["insights"]["items_to_investigate"]],
            positive_items=[InsightItem(**i) for i in MOCK_BRIEFING["insights"]["positive_items"]],
            trends=[TrendItem(**i) for i in MOCK_BRIEFING["insights"]["trends"]],
        ),
        generated_at=MOCK_BRIEFING["generated_at"],
        is_draft=MOCK_BRIEFING["is_draft"],
    )


@router.get("/briefing", response_model=List[BriefingResponse])
async def list_briefings(_limit: int = 12):
    """List available month-end briefings."""
    return [
        BriefingResponse(
            month_year=MOCK_BRIEFING["month_year"],
            metrics=BriefingMetrics(**MOCK_BRIEFING["metrics"]),
            insights=BriefingInsights(
                items_to_investigate=[InsightItem(**i) for i in MOCK_BRIEFING["insights"]["items_to_investigate"]],
                positive_items=[InsightItem(**i) for i in MOCK_BRIEFING["insights"]["positive_items"]],
                trends=[TrendItem(**i) for i in MOCK_BRIEFING["insights"]["trends"]],
            ),
            generated_at=MOCK_BRIEFING["generated_at"],
            is_draft=MOCK_BRIEFING["is_draft"],
        )
    ]


@router.get("/cash-flow", response_model=CashFlowForecast)
async def get_cash_flow():
    """Get current cash position and forecast."""
    return CashFlowForecast(
        current=CashFlowSnapshot(**MOCK_CASH_FLOW["current"]),
        forecast_7_days=CashFlowSnapshot(**MOCK_CASH_FLOW["forecast_7_days"]),
        forecast_14_days=CashFlowSnapshot(**MOCK_CASH_FLOW["forecast_14_days"]),
        forecast_30_days=CashFlowSnapshot(**MOCK_CASH_FLOW["forecast_30_days"]),
        runway_status=MOCK_CASH_FLOW["runway_status"],
        runway_months=MOCK_CASH_FLOW["runway_months"],
    )


@router.get("/benchmarks", response_model=BenchmarkResponse)
async def get_benchmarks(industry: Optional[str] = None):
    """Get benchmark comparison for tenant."""
    return BenchmarkResponse(
        industry_code=MOCK_BENCHMARKS["industry_code"],
        industry_name=MOCK_BENCHMARKS["industry_name"],
        period=MOCK_BENCHMARKS["period"],
        metrics=[BenchmarkMetric(**m) for m in MOCK_BENCHMARKS["metrics"]],
        overall_percentile=MOCK_BENCHMARKS["overall_percentile"],
    )


@router.post("/anomalies/{id}/dismiss")
async def dismiss_anomaly(id: str):
    """Dismiss an anomaly."""
    for a in MOCK_ANOMALIES:
        if a["id"] == id:
            a["status"] = "dismissed"
            return {"status": "dismissed", "id": id}
    raise HTTPException(status_code=404, detail=f"Anomaly {id} not found")


@router.post("/anomalies/{id}/resolve")
async def resolve_anomaly(id: str):
    """Resolve an anomaly."""
    for a in MOCK_ANOMALIES:
        if a["id"] == id:
            a["status"] = "resolved"
            return {"status": "resolved", "id": id}
    raise HTTPException(status_code=404, detail=f"Anomaly {id} not found")