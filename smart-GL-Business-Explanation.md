# Smart-GL: AI-Powered General Ledger for Australian Small Business

## Executive Summary for Business Sponsor

**What is Smart-GL?**
An AI-powered accounting system that automates transaction categorisation for Australian small businesses, saving bookkeepers 50-80% of manual data entry time while ensuring GST compliance.

**Who is this for?**
Australian small businesses (turnover $50K-$5M) using Xero or MYOB who want to reduce bookkeeping costs and speed up month-end closes.

---

## The Problem We Solve

### Current Pain Point
- Bookkeepers manually categorise every bank transaction
- Takes 20+ hours/month for a small business
- Human error leads to incorrect BAS reports
- Delays in knowing true profitability

### Our Solution
- AI automatically categorises 50-80% of transactions
- Human only reviews uncertain items
- Built-in Australian GST codes (G1-G11, N-T)
- Works with your existing Xero/MYOB

---

## Key Features (In Plain English)

### 1. Auto-Categorisation (The Core Feature)
**What it does:** When a bank transaction comes in, our AI looks at the description (e.g., "BP BURPENNINE") and automatically assigns the correct account code and GST type.

**Example:**
- Old way: Bookkeeper sees "BP BURPENNINE", researches, records as "Fuel - 6100 - G1"
- New way: System does this automatically. Bookkeeper reviews exceptions only.

**Time saved:** ~15 hours/month for average small business

### 2. GST-Ready Export
**What it does:** One-click CSV export formatted for your BAS return. No more manual GST calculations.

**Example:**
- Click "Export BAS"
- Get CSV with: Date, Description, Amount, GST Code, GST Amount, Account
- Upload directly to BAS portal

**GST Codes we support:**
| Code | Meaning | Example |
|------|--------|--------|
| G1 | GST on income | Sales |
| G2 | GST on purchases | Equipment |
| G3 | Capital works | Building fitout |
| G4 | GST-free inputs | Rent, insurance |
| G9 | No GST in / No GST out |Subscriptions |
| G11 | Import GST | Overseas purchases |
| N-T | No GST applicable | School fees |

### 3. Human Review Loop
**What it does:** Transactions the AI isn't confident about go to a review queue. Human confirms or corrects - corrections improve the AI.

**Why this matters:** The more you use it, the smarter it gets.

### 4. Xero & MYOB Integration
**What it does:** Sync your Chart of Accounts from Xero or MYOB. Works with your existing setup - no migration needed.

### 5. Dashboard & Reports
- Trial Balance
- Profit & Loss
- Dashboard showing automation rate (% auto-categorised)

---

## Technical Details (CFO-Friendly)

### Infrastructure
- **Database:** Neon (PostgreSQL) - Australian data residency available
- **AI:** Claude (Anthropic) for categorisation, OpenAI for embeddings
- **Hosting:** Vercel (web), Render (API)

### Security
- Row-level security per tenant
- Tenant isolation built into database
- No access to other businesses' data

### Data Flow
```
Bank Feed (Basiq) → Smart-GL AI → Categorised → Your Xero/MYOB
```

---

## Pricing & Value

### Value Calculation
| Business Size | Monthly Bookkeeping | @ $50/hr | Time Saved | Annual Savings |
|------------|-----------------|-----------|----------|------------|
| $500K turnover | 15 hours | $750 | 65% | $5,850 |
| $1M turnover | 25 hours | $1,250 | 70% | $10,500 |
| $2M turnover | 40 hours | $2,000 | 75% | $18,000 |

---

## Roadmap / What's Next

### Phase 1 (Complete - Demo Ready)
- ✅ 50% auto-categorisation
- ✅ BAS-ready CSV export
- ✅ Human review workflow

### Phase 2 (In Progress)
- ✅ Xero integration
- ✅ MYOB integration
- ⏳ 65-80% automation target

### Phase 3 (Planned)
- BAS-lite automatic preparation
- Aged creditor/debtor reports
- Cash flow projections
- Bank feed straight into Smart-GL (skip Xero/MYOB)

---

## Questions for Discussion

1. **Pricing model?** Monthly subscription per user or per business?
2. **Target market?** Pure Xero/MYOD users or direct bank feed option?
3. **Onboarding?** White-label for bookkeepers or direct to business?
4. **Integrations?** Add QuickBooks, Reckon?

---

## Contact & Next Steps

This demo shows the core functionality. Ready to discuss:
- Refined feature priorities
- Pricing structure
- Beta user program

**Demo URL:** https://smart-2gm1qnvba-sensibleanalytic-4114s-prod.vercel.app

---

*Prepared for [Business Sponsor Name]*
*Date: April 2026*