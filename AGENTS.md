# Agent Instructions - smart-GL

## ⚠️ READ FIRST: Org-Wide Agent Guide

This repo follows Sensible Analytics org-wide standards.

**Fetch and follow the org-wide AGENTS.md:**
1. **Local (preferred)**: `~/Business/sensibleAnalytics/.github/AGENTS.md`
2. **Remote**: `https://github.com/Sensible-Analytics/.github/blob/main/AGENTS.md`

The org-wide guide contains:
- Branch protection rules
- Workflow instructions
- Skill mapping
- Testing standards

## 📋 Repo-Specific Notes

Smart GL is an AI-powered accounting application for Australian small businesses.

### Tech Stack

- Backend: Python (FastAPI)
- AI: OpenAI embeddings + Anthropic Claude
- Database: Supabase (PostgreSQL + vector search)
- Payments: Formance Ledger

### Key Commands

```bash
# API
cd apps/api && uvicorn main:app --reload

# Tests
cd apps/api && pytest

# Lint
ruff check apps/api/
```

### Project Structure

```
apps/api/
├── services/      # Business logic
├── routers/       # API endpoints
├── tests/         # Unit tests
└── main.py        # Entry point
```

---

*For full org-wide rules, see: ~/Business/sensibleAnalytics/.github/AGENTS.md*