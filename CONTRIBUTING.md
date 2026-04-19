# Branching, PR, Build & Deployment Standard (Sensible Analytics)

## Branching Model
- Use short-lived feature/fix branches off `main`.
- Naming: `type/short-description` (e.g., `feat/add-logging`, `fix/zero-division`, `docs/update-readme`).
- For agency-wide standards, prefix with `std/` when updating shared configs (e.g., `std/ci-base`).
- Keep `main` protected: no direct pushes; all changes via PR.

## Pull Request (PR) Process
1. Create branch from `main`.
2. Make changes, commit with conventional commit messages.
3. Push branch and open PR against `main`.
4. Add descriptive title and body; reference issue numbers.
5. Request reviews from CODEOWNERS and required reviewers.
6. Ensure all status checks pass before merge.

## Commit Guidelines
- Use conventional commits: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
- Keep commits atomic; link PRs to commits.

## Build & Test Checks (per repo)
- Ensure a build script exists (npm `build`, or native/build equivalents).
- Run tests locally and via CI.
- CI must include at least: lint, unit tests, build.
- If no npm pipeline, adapt: Android (`./gradlew build`), Rust (`cargo build/test`), Python (`pytest`), Next.js (`next build`).
- Post-build, verify artifacts and run relevant test suites.

## Merge & Deploy Verification
- After PR merge, watch CI for post-merge workflows.
- Confirm deployment pipelines succeed (staging/prod as applicable).
- For web apps, run smoke checks: reach main page, key endpoints.
- For libraries, ensure version bump and publish if applicable.
- Record deploy logs and link PR in release notes.

## .docs Convention
- Repository-specific documentation may live in `.docs/` or `docs/`.
- Keep `README.md` and `AGENTS.md` in repository root (outside `.docs`).
- Architecture and design documents should be versioned and linked from README.

## Ownership & Reviews
- CODEOWNERS defines who reviews what.
- PRs must be approved by at least one owner for the changed paths.
- Use `@org/team` mentions for cross-team reviews.

## Enforcement
- Protect `main` with required status checks and required reviewers.
- Use branch creation rules to enforce naming and permissions.
- CI must be green before merge allowed.
- Use GitHub Actions/CI to gate merges automatically.

## Quick Checklist for Contributors
- [ ] Branch follows naming convention.
- [ ] Commits are conventional.
- [ ] Build passes locally and in CI.
- [ ] Tests pass.
- [ ] PR has reviewers and passes status checks.
- [ ] After merge, verify deployment and smoke tests.
- [ ] Update documentation in `.docs/` if needed; keep root README/AGENTS.md intact.
