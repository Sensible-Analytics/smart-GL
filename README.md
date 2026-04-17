# Smart GL

AI-powered accounting software for Australian small businesses.

## Overview

Smart GL is a Stage 1 AI Accounting application that automates transaction categorisation using:
- **Basiq API** - Bank feed aggregation
- **Formance Ledger** - Double-entry bookkeeping
- **Claude Sonnet 4** - AI categorisation
- **Supabase** - PostgreSQL with RLS

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 15 + App Router | React UI |
| Backend | FastAPI (Python 3.12) | REST API |
| Database | Supabase (PostgreSQL) | Data storage |
| Ledger | Formance Ledger v2 | Double-entry accounting |
| Bank Feeds | Basiq API v3 | Bank aggregation |
| AI | Claude Sonnet 4 | Transaction categorisation |
| Embeddings | OpenAI | Semantic search |

## Project Structure

```
smart-GL/
├── .doc/                    # Documentation
│   ├── getting-started/     # Quick start guides
│   ├── architecture/       # Diagrams
│   ├── api/               # API reference
│   └── adr/               # Architecture decisions
├── apps/
│   ├── web/               # Next.js frontend
│   └── api/               # FastAPI backend
├── infra/
│   ├── supabase/          # Database migrations
│   └── docker-compose.yml # Formance Ledger
└── packages/              # Shared packages
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- pnpm 9.0+
- Supabase CLI (optional)
- Docker (for Formance Ledger)

### Setup

```bash
# Clone and install
pnpm install

# Start development
pnpm dev
```

Environment variables (see `.env.example`):
- `SUPABASE_URL` - Database URL
- `SUPABASE_SERVICE_KEY` - Service role key
- `ANTHROPIC_API_KEY` - Claude API key
- `OPENAI_API_KEY` - OpenAI API key
- `BASIQ_API_KEY` - Basiq API key

### Running Services

```bash
# Frontend (http://localhost:3000)
cd apps/web && pnpm dev

# Backend (http://localhost:8000)
cd apps/api && uvicorn main:app --reload

# Formance Ledger (Docker)
docker compose -f infra/docker-compose.yml up
```

## Features

- Dashboard with financial overview
- Transaction list with AI categorisation
- Journal entry double-entry view
- Financial reports (Balance Sheet, P&L)
- Bank feed management via Basiq
- Chart of Accounts
- AI Insights with categorization accuracy

## Documentation

- [Getting Started](./.doc/getting-started/setup.md)
- [Architecture](./.doc/architecture/README.md)
- [API Reference](./.doc/api/README.md)
- [Environment Registry](./.doc/environment-registry.md)

## Development

```bash
# Build all apps
pnpm build

# Lint all apps
pnpm lint

# Type-check all apps
pnpm type-check
```

## Testing

```bash
# API tests
cd apps/api && pytest
```

## Deployment

- Frontend: Vercel
- Backend: Fly.io
- Database: Supabase

See [Deployment Guide](./.doc/getting-started/deployment.md)

## License

Proprietary - All rights reserved