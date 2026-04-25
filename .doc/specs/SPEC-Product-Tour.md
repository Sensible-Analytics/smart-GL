# Spec: Interactive Product Tour for Smart-GL Demo

## Objective
Create an interactive, visual product tour for the Smart-GL demo that explains features through popups, hover tooltips, and guided walkthrough. Target audience: experienced CFO (30+ years Australian accounting).

## Context
- **Current state:** Demo app at https://web-pi-gold-xw8tkwu84n.vercel.app
- **Pages:** Dashboard, Transactions, Reports, Accounts, Bank Feeds, Journal, AI Insights, Settings
- **User:** Potential co-founder/CFO who evaluates for business viability

## Interaction Patterns

### 1. Hover Tooltips (i)
- Icon: ⓘ next to labels
- Trigger: Hover on icon
- Content: Plain-English explanation (1-2 sentences)
- Style: Dark tooltip with white text, max 200px width

### 2. Feature Popups (Click)
- Icon: "Learn More" link or info button
- Trigger: Click
- Content: Feature explanation + screenshot mockup
- Style: Modal overlay with close button

### 3. Product Tour (Guided)
- Trigger: "Start Tour" button on first visit
- Flow: Numbered steps highlighting UI elements
- Skip option: "Skip Tour" button
- Progress: "Step 3 of 7" indicator

## Page-by-Page Specification

### Dashboard Page

| Element | Interaction | Content |
|---------|------------|---------|
| Automation Rate card | Hover on % | "68% of transactions auto-categorised. Remaining 32% need human review. Target: 80%." |
| Revenue/Expenses cards | Hover | "Income from sales. Expenses are all business costs." |
| Pending Review badge | Click popup | "Transactions AI couldn't categorise. Click to review." |
| "Start Tour" button | Launch tour | 5-step guided tour |

**Tour Steps:**
1. Highlight "Automation Rate" → "This shows how much work the AI does for you"
2. Highlight Revenue → "Your income from all sources"
3. Highlight Expenses → "Your costs this period"
4. Highlight Pending → "Items needing your attention"
5. Highlight "Export BAS" → "One-click GST-ready CSV"

### Transactions Page

| Element | Interaction | Content |
|---------|------------|---------|
| Status badge (Pending/Review/Categorised) | Hover | "Pending = not yet categorised. Review = AI unsure. Categorised = done." |
| GST Code column | Hover | "Australian GST type (G1-G11, N-T). Determines your BAS." |
| "Run Auto-Categorise" button | Click popup | "AI categorises up to 50 transactions. Takes ~30 seconds." |
| Account column | Hover | "Account code maps to your Chart of Accounts." |

**Tour Steps:**
1. Show batch categorise button
2. Explain status badges
3. Show GST column purpose
4. Show confirm flow

### Reports Pages (Trial Balance, P&L, BAS Export)

| Element | Interaction | Content |
|---------|------------|---------|
| Date filters | Popout tip | "Filter transactions by date range" |
| "Export CSV" button | Hover | "Download for BAS. Format matches ATO requirements." |
| BAS Summary totals | Click popup | "G1= GST on sales, G2= GST on purchases, etc. See full table." |

**BAS Export Tour:**
1. Select date range
2. Explain GST categories
3. Show "Export" button format

### Accounts Page

| Element | Interaction | Content |
|---------|------------|---------|
| Account Code | Hover | "Unique code in your Chart of Accounts" |
| GST Code | Hover | "Default GST type for this account" |
| "Sync from Xero/MYOB" | Click popup | "Import your existing Chart of Accounts from Xero or MYOB. No manual entry needed." |

### Bank Feeds Page

| Element | Interaction | Content |
|---------|------------|---------|
| Connection status | Hover | "Live bank feed via Basiq. Shows transactions as they happen." |
| "Connect Bank" | Click popup | "Link your business bank account. Uses Basiq for secure connection." |

## Global Elements

### Help (?) Button (bottom-right)
- Opens: Full feature list modal
- Sections: Getting Started, Features, GST Codes, FAQ

### GST Quick Reference Modal
| Code | Description | Example |
|------|------------|----------|
| G1 | GST on income | Sales |
| G2 | GST on purchases | Equipment |
| G3 | Capital works | Building |
| G4 | GST-free inputs | Rent |
| G9 | No GST in/out | Subscriptions |
| G11 | Import GST | Overseas |
| N-T | No GST | School fees |

## Implementation Notes

### Tech Stack
- Next.js App Router
- shadcn/ui for components
- Tooltip, Popover, Dialog components
- react-joyride for product tour (or custom)

### Libraries
```bash
# Install for tour
npm install react-joyride
# Or use built-in shadcn
npx shadcn@latest add tooltip popover dialog
```

## Acceptance Criteria

- [ ] Hover tooltips appear on all data columns (Status, GST Code, Account)
- [ ] "Start Tour" button works on Dashboard
- [ ] GST Quick Reference accessible from Reports
- [ ] All explanations in plain English
- [ ] Works on mobile (touch-friendly popups)
- [ ] Tour can be skipped
- [ ] CFO can understand core value in <2 minutes

## Visual Mockup

```
┌─────────────────────────────────────────────┐
│  Smart-GL                      [?] [Start] │
├─────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Revenue  │ │Expenses  │ │Auto Cat │ │
│  │ $52,340  │ │ $31,200  │ │  68%  ⓘ│  │
│  └──────────┘ └──────────┘ └──────────┘  │  │  ⓘ Hover: 68% of transactions auto-   │  │         categorised. Target: 80%.        │
│                                             │
│  [Export BAS CSV]  [Start Tour]              │
└─────────────────────────────────────────────┘
```

## Commands

```bash
# Dev
cd apps/web && pnpm dev

# Build
cd apps/web && pnpm build

# Deploy
vercel deploy --prod
```

## Success Criteria

CFO can answer after tour:
1. "How much time does this save?" → "15+ hours/month"
2. "How does GST work?" → "Auto-mapped to G1-G11"
3. "What about my Xero?" → "Syncs from Xero/MYOB"
4. "Is it accurate?" → "80% auto, 20% human review"

---
*Target: First-time user understands value in 2 minutes*