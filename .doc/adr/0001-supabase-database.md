# ADR 0001: Use Supabase for Database

## Status
Accepted

## Context
Smart GL needs a database for storing transactions, categorisations, journal entries, and chart of accounts. Need multi-tenant isolation and vector search for AI categorisation.

## Decision
Use Supabase (PostgreSQL + pgvector + RLS) as the database layer.

## Consequences
- **Positive**: Built-in RLS for tenant isolation, pgvector for embeddings, managed PostgreSQL
- **Negative**: Requires Supabase account, Pro plan for pg_cron

## Alternatives Considered
- **Neon**: No RLS support (would need manual tenant filtering)
- **Plain PostgreSQL**: Missing pgvector, no built-in auth