# Contributing to Job Intelligent

Thanks for your interest in contributing! This document describes the conventions used in this repository.

## Development Setup

### Prerequisites

- Docker Desktop (Compose v2)
- Python 3.11+ (for local tooling)
- Node.js 20+ (for frontend dev)

### Bootstrap

```bash
git clone https://github.com/Ridadata/job-intelligent.git
cd job-intelligent
cp .env.example .env       # fill in values
docker compose up -d       # full stack (API, DB, Airflow, Redis, frontend)
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for the full walkthrough.

## Branch Model

- `main` — production-ready, protected. PRs only.
- `feature/<scope>-<topic>` — new work (e.g. `feature/api-rate-limit`).
- `fix/<scope>-<topic>` — bug fixes.
- `docs/<topic>` — documentation-only changes.

Always branch off `main`. Never commit directly to `main`.

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/).

Format:

```
<type>(<scope>): <short summary>

<optional body — list every file changed and what was done>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

Examples:

```
feat(api): add /candidates/{id}/skill-gap endpoint
fix(etl): handle empty descriptions in silver transform
docs(readme): update quick start instructions
```

Commit after every completed change — do not batch unrelated work into a single commit.

## Code Style

### Python

- Format: [Ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`).
- Type hints required for all public functions.
- Docstrings: Google style with Args / Returns / Raises sections.

```bash
ruff check .
ruff format .
```

### TypeScript

- Format: ESLint + Prettier.
- TypeScript strict mode — no `any` (use `unknown` + type guards).
- Functional components only.

```bash
cd frontend
npm run lint
npm run format
```

## Testing

```bash
# Backend
docker compose exec fastapi python -m pytest tests/ -v

# Frontend
cd frontend && npm test
```

Tests must be deterministic. Mock external APIs, the current time, and any random values.

## Pull Request Checklist

- [ ] Branch is up to date with `main`
- [ ] Commits follow Conventional Commits format
- [ ] Tests pass locally (`pytest`, `npm test`)
- [ ] Linters pass (`ruff check`, `npm run lint`)
- [ ] Documentation updated if behavior changed
- [ ] No hardcoded secrets or credentials
- [ ] PR description explains the *why*, not just the *what*

## Architecture Boundaries

Respect the layered structure:

- Backend: `routers → services → repositories → database`. Never skip a layer.
- ETL: Bronze → Silver → Gold. Layers are immutable boundaries.
- Frontend: Pages call hooks; hooks call services; services call the API client.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full breakdown.

## Reporting Issues

When reporting a bug, please include:

1. Steps to reproduce
2. Expected vs actual behavior
3. Environment (OS, Docker version, Node version)
4. Relevant logs (`docker compose logs <service>`)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
