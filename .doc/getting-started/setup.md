# Smart GL Getting Started

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 18+ | Frontend runtime |
| Python | 3.12+ | Backend runtime |
| pnpm | 9.0+ | Package manager |
| Docker | Latest | Formance Ledger |
| Git | Latest | Version control |

## Environment Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-org/smart-GL.git
cd smart-GL
```

### 2. Install dependencies
```bash
pnpm install
```

### 3. Environment variables

Copy `.env.example` to `.env.local` and fill in:

```bash
cp .env.example .env.local
```

Required variables:
| Variable | Description | How to get |
|----------|-------------|-------------|
| `SUPABASE_URL` | Database URL | Supabase dashboard |
| `SUPABASE_SERVICE_KEY` | Service role key | Supabase dashboard |
| `ANTHROPIC_API_KEY` | Claude API key | Anthropic console |
| `OPENAI_API_KEY` | OpenAI API key | OpenAI platform |
| `BASIQ_API_KEY` | Basiq API key | Basiq dashboard |

**Security**: Never commit `.env.local` - it's in `.gitignore`

### 4. Start Formance Ledger
```bash
docker compose -f infra/docker-compose.yml up -d
```

### 5. Run the application
```bash
# Development (both frontend + backend)
pnpm dev

# Or individually:
cd apps/web && pnpm dev   # http://localhost:3000
cd apps/api && pnpm dev   # http://localhost:8000
```

## Verification

### Build check
```bash
pnpm build
```

### Type check
```bash
pnpm type-check
```

### Lint
```bash
pnpm lint
```

### Run tests
```bash
cd apps/api && pytest
```

## Common Issues

### Port already in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database connection failed
- Verify `SUPABASE_URL` is correct
- Check network/firewall allows connection
- Ensure Supabase project is not paused

### Import errors
```bash
# Clear caches
rm -rf apps/*/node_modules
pnpm install
```