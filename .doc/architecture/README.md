# Smart GL Architecture

## High-Level Diagram

```mermaid
graph TB
    subgraph "Client"
        Web[Next.js Frontend]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Backend]
    end
    
    subgraph "Data Layer"
        Supabase[(Supabase PostgreSQL)]
        Formance[Formance Ledger]
    end
    
    subgraph "External Services"
        Basiq[Basiq Bank API]
        Anthropic[Anthropic Claude]
        OpenAI[OpenAI Embeddings]
    end
    
    Web -->|HTTP| FastAPI
    FastAPI -->|SQL| Supabase
    FastAPI -->|Ledger API| Formance
    FastAPI -->|Bank Data| Basiq
    FastAPI -->|AI Categorisation| Anthropic
    FastAPI -->|Embeddings| OpenAI
```

## Component Overview

### Frontend (apps/web)
- **Framework**: Next.js 15 with App Router
- **UI**: React 18, Tailwind CSS, shadcn/ui
- **Charts**: Recharts
- **Port**: 3000

### Backend (apps/api)
- **Framework**: FastAPI (Python 3.12)
- **Database**: Supabase (PostgreSQL + pgvector + RLS)
- **Ledger**: Formance Ledger v2
- **Port**: 8000

### Routers

| Router | Path | Description |
|--------|-----|-------------|
| transactions | /transactions | Transaction CRUD |
| journal | /journal | Journal entries |
| reports | /reports | Financial reports |
| accounts | /accounts | Chart of accounts |
| basiq | /basiq | Bank feed integration |

### Services

| Service | Purpose |
|---------|---------|
| categorise.py | AI transaction categorization |
| basiq.py | Basiq API integration |
| formance.py | Formance Ledger interface |

## Database Schema

### Core Tables

- `tenants` - Multi-tenant isolation
- `accounts` - Chart of accounts
- `transactions` - Bank transactions
- `categorisations` - AI categorisation results
- `journal_entries` - Double-entry records

### Key Conventions

- **Monetary values**: Stored as cents (integers)
- **Time zone**: UTC in DB, Australia/Sydney for display
- **Soft deletes**: `deleted_at` field
- **Tenant isolation**: RLS + `app.current_tenant_id`

## Data Flow

### Transaction Categorisation

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Basiq
    participant OpenAI
    participant Anthropic
    participant Supabase
    
    User->>API: Fetch transactions
    API->>Basiq: Get bank data
    Basiq->>API: Transaction list
    API->>OpenAI: Generate embeddings
    OpenAI->>API: Embeddings
    API->>Anthropic: Categorise with Claude
    Anthropic->>API: Category suggestions
    API->>Supabase: Save categorisations
    API->>User: Display results
```

## Security

- **Tenant isolation**: Row-level security (RLS)
- **API keys**: Environment variables only
- **Authentication**: Bearer tokens (future: Supabase Auth)

## Deployment

| Component | Platform |
|-----------|-----------|
| Frontend | Vercel |
| Backend | Fly.io |
| Database | Supabase |
| Ledger | Docker (self-hosted) |