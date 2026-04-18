# Deployment Guide

## Free Backend Options (2026)

| Platform | Free Tier | Best For |
|----------|-----------|----------|
| **Render** | 750 hrs/month | FastAPI/Flask (closest to Heroku) |
| **SnapDeploy** | 100 hrs (one-time) | Docker containers |
| **Deta Space** | Free forever | Microservices |

### Recommended: Render (Free Tier)

```bash
# 1. Connect GitHub to Render
# 2. Create new Web Service from your repo
# 3. Settings:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
#    - Free instance type
```

### Alternative: SnapDeploy

```bash
# 1. Sign up at snapdeploy.dev
# 2. Connect GitHub repository
# 3. Select apps/api as the Docker source
# 4. Auto-detects FastAPI, deploys with HTTPS
```

## Prerequisites

- Vercel account (frontend)
- Backend platform account (Render recommended)
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
# Or connect GitHub repo in Vercel dashboard
```

## Deploy Backend (Render - Recommended for Free)

```bash
# 1. Go to https://render.com
# 2. Connect your GitHub repo (Sensible-Analytics/smart-GL)
# 3. Create new Web Service:
#    - Repository: smart-GL
#    - Branch: main
#    - Build Command: pip install -r requirements.txt
#    - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
#    - Environment: Python 3.12
#    - Instance Type: Free
# 4. Add environment variables in Render dashboard
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