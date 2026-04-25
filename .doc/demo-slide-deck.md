# Smart GL - AI-Powered Accounting for SMB

## For Practitioners Who Know The Ropes

---

## The Problem You've Seen Before

You've been here before: every EOFY, every BAS, every quarter.

A client hands you a shoebox of receipts. Or a CSV with 500 transactions, none categorised. Or "the bookkeeper" stopped showing up in March, and now it's July.

**The work isn't the accounting. It's the data entry.**

Bank feeds exist. But they give you a transaction dump, not a finished set of books. Someone still has to map every description to an account code. Someone still has to split GST. Someone still has to balance.

What if that someone wasn't you?

---

## How It Works

### 1. Bank Connection (Basiq API)

We connect to 135+ Australian financial institutions via Basiq's Open Banking API. Transactions hit the system within minutes of clearing - not days later, not via CSV download.

### 2. AI Categorisation (Claude Sonnet 4)

Each transaction hits a classification model trained on:
- Merchant category codes (MCC)
- Historical patterns from this specific business
- User corrections (learns from you)

**What's actually happening:** The model looks at the description, amount, timing, and sequence - then picks the most likely account code. 80-89% auto-categorise. The unsure ones flag for your review.

### 3. Double-Entry Recording (Formance Ledger)

Every transaction creates two postings - debit and credit. Enforced at the API level. No manual balance checking. No "does this add up?" questions.

### 4. Real-Time Reports

P&L, Balance Sheet, GST summary - all computed from live data. No "as at" date. No exporting to Excel to fix.

---

## What Makes This Different

| Traditional Bookkeeping | Smart GL |
|----------------------|---------|
| Transactions received in batch | Real-time stream |
| Manual account mapping | 80-89% auto-categorised |
| You find the errors | System flags anomalies |
| Month-end reconciliation | Continuous |
| Fixed account codes | Learns from your corrections |

**The value proposition for you:**
- Less time on categorisation, more time on advisory
- Fewer adjustments at EOFY
- Cleaner trails for BAS audit
- Clients who actually know their numbers

---

## The AI Question

You're a sceptic. Good.

**What the AI is doing:**
- Pattern matching on transaction descriptions
- NOT making accounting judgments
- NOT generating financial advice
- Flagging uncertain items for human review

**What you control:**
- Account code mapping rules
- Auto-approve thresholds
- Override any classification
- Set review workflows

---

## Integration Points

- **Bank feeds**: Basiq (CDR Open Banking)
- **Ledger**: Formance Ledger v2 (double-entry)
- **AI**: Claude Sonnet 4 (classification)
- **Database**: Supabase (PostgreSQL + vector)

All standard Australian- compatible. Your existing software can import via API.

---

## Try It

**Live Demo**: https://smart-1m1jc7yf5-sensibleanalytic-4114s-prods-projects.vercel.app

1. Connect bank (BPAY demo available)
2. Watch transactions flow
3. Try the classification
4. Run a report

---

## You're In Control

| Task | What You Do | What AI Does |
|------|------------|-------------|
| Categorise tricky items | ✅ You decide | Flag for review |
| Set account rules | ✅ You configure | Apply consistently |
| Review anomalies | ✅ You approve | Detect deviation |
| File BAS | ✅ You certify | Report ready |