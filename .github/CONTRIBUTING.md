# Contributing to Smart-GL

This project follows the Sensible Analytics branching, PR, build & deployment standard.

## Quick Reference

Please refer to the full standard: [/tmp/branch_and_pr_standard.md](file:///tmp/branch_and_pr_standard.md)

### Branch Naming
- Use `type/short-description` (e.g., `feat/add-api`, `fix/graphql`)
- Keep branches short-lived off `main`

### PR Process
1. Create branch from `main`
2. Make changes, commit with conventional commit messages
3. Push branch and open PR against `main`
4. Add descriptive title and body; reference issue numbers
5. Request reviews from CODEOWNERS
6. Ensure all CI status checks pass before merge

### Build & Test
```bash
# Turbo monorepo
pnpm install
pnpm build
pnpm lint
```

### CI Requirements
- Lint: ESLint
- Build: API + Web