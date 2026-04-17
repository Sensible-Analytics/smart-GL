# Environment Registry

This document tracks all external services, deployment URLs, and tech stack changes for Smart GL.

## Services

| Service | Type | URL | Credentials |
|---------|------|-----|-------------|
| Supabase | Database | https://[project].supabase.co | Service key |
| Formance Ledger | Accounting | http://localhost:5433 | None (local) |
| Basiq | Bank Feeds | https://api.basiq.io | API Key |
| Anthropic | AI | https://api.anthropic.com | API Key |
| OpenAI | Embeddings | https://api.openai.com | API Key |

## Deployment

| Component | Platform | URL | Status |
|-----------|----------|-----|--------|
| Frontend | Vercel | (not deployed) | - |
| Backend | Fly.io | (not deployed) | - |
| Database | Supabase | (managed) | - |

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | Next.js | 15.x |
| Frontend | React | 18.x |
| Frontend | TypeScript | 5.x |
| Frontend | Tailwind CSS | 3.x |
| Backend | FastAPI | 0.115.x |
| Backend | Python | 3.12 |
| Database | PostgreSQL | 15.x |
| Database | pgvector | 0.1.x |
| Package Manager | pnpm | 9.0.x |

## Last Updated

2024-01-15 (initial documentation)