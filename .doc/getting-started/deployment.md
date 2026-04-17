# Deployment Guide

## Prerequisites

- Vercel account (frontend)
- Fly.io account (backend)
- Supabase account (database)

## Environment Variables

### Frontend (.env)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)
```
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_KEY=[service-key]
ANTHROPIC_API_KEY=[key]
OPENAI_API_KEY=[key]
BASIQ_API_KEY=[key]
```

## Deploy Frontend (Vercel)

```bash
cd apps/web
vercel --prod
```

## Deploy Backend (Fly.io)

```bash
cd apps/api
fly launch --name smartgl-api --region syd
fly deploy
```

## Database

Managed via Supabase dashboard - no deployment needed.

## Formance Ledger

Run via Docker on Fly.io or self-hosted:
```bash
docker compose -f infra/docker-compose.yml up -d
```

## Verification

After deployment, verify:
1. Frontend loads at Vercel URL
2. Backend health check: `curl https://[backend-url]/health`
3. API responds to requests