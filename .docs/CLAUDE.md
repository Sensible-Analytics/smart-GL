# CLAUDE.md - Sensible Analytics Code Standards

> **Purpose**: This document defines the code size limits and architecture guidelines for all Sensible Analytics repositories. All contributors and AI agents MUST adhere to these standards.

---

## Code Size Limits

| Metric | Limit | Rationale |
|--------|-------|-----------|
| **max-lines** | 200 | Files exceeding 200 lines should be split into modules |
| **max-lines-per-function** | 30 | Functions over 30 lines indicate multiple responsibilities |
| **complexity** | 8 | Cyclomatic complexity above 8 is hard to test and maintain |
| **max-depth** | 4 | Nesting deeper than 4 levels reduces readability |
| **max-params** | 3 | Functions with 4+ parameters should use config objects |

### Enforcement Guidelines

- **Files > 200 lines**: Extract related logic into separate modules or utilities
- **Functions > 30 lines**: Break into smaller, single-responsibility functions
- **Complexity > 8**: Simplify conditionals, extract branches into named functions
- **Depth > 4**: Use early returns, guard clauses, or extract nested logic
- **Params > 3**: Group related parameters into a single config/options object

---

## Architecture Guidelines

### 1. Single Responsibility
- Each file should have one clear purpose
- Each function should do one thing well
- Modules should encapsulate related functionality

### 2. Composition Over Inheritance
- Prefer function composition and module imports
- Avoid deep class hierarchies
- Use traits/interfaces for polymorphism (Rust) or composition (TypeScript/Python)

### 3. Explicit Over Implicit
- Favor explicit type annotations
- Avoid magic numbers — use named constants
- Make data flow visible and traceable

### 4. Testability
- Pure functions where possible
- Dependency injection for side effects
- Each public function should be independently testable

### 5. Error Handling
- Fail fast with descriptive error messages
- Use Result/Option types (Rust) or try/catch with typed errors (TS/Python)
- Never silently swallow errors

---

## Anti-Patterns

- ❌ God files (> 200 lines doing everything)
- ❌ God functions (> 30 lines, multiple responsibilities)
- ❌ Deeply nested conditionals (> 4 levels)
- ❌ Parameter soup (> 3 params without config object)
- ❌ Silent error swallowing
- ❌ Magic numbers and hardcoded values
- ❌ Circular dependencies between modules

---

## Related Documents

- **Agent Instructions**: `AGENTS.md`
- **Contributing Guide**: `CONTRIBUTORS.md`