# Codex Project Instructions

## Project Overview

This repository is a planning, documentation, and implementation workspace for a tuberculosis public health decision-support platform. The product goal is to support primary care and municipal surveillance teams with territorial analysis, operational indicators, triage support, treatment follow-up risk signals, and tuberculosis resistance vigilance.

The backend is implemented in Python. The current application includes public-data ingestion, canonical SQLite storage, transparent indicator/scenario logic, recommendations, synthetic municipal operational alerts, FastAPI APIs, a CLI, Jinja fallback dashboards, and a React/Vite product frontend.

## Repository Structure

- `descricao_do_projeto.md`: product vision, public health scope, data assumptions, LGPD boundaries, and MVP constraints.
- `frentes_de_desenvolvimento.md`: workstreams for scope, users, evidence, data, rules, product, architecture, governance, and validation.
- `proximos_passos.md`: canonical prioritized roadmap, capability statuses, dependencies, and remaining Biochallenge deliverables.
- `referencias.md`: related systems, papers, and design references for public health surveillance and TB decision support.
- `guia_validacao_de_dominio.md`: plain-language clinical and epidemiological
  validation guide, evidence summary, and reviewer decision record.
- `especificacao_tecnica_do_sistema.md`: engineering-oriented specification for MVP scope, data contracts, architecture, workflows, governance, and validation.
- `mvp2_municipal_contracts.md`: synthetic municipal CSV contracts, privacy rules, and operational alert behavior.
- `documentos/`: source PDFs and supporting reference documents used during project formulation.
- `notebooks/`: exploratory notebooks and scripts for public-data loading and visualization.
- `src/tbia/`: Python package for ingestion, indicators, scenarios, recommendations, storage, CLI, APIs, and fallback dashboards.
- `frontend/`: React/Vite/TypeScript product interface for territorial analysis and synthetic municipal operations.
- `AGENTS.md`: instructions for future Codex sessions.
- `CONTRIBUTING.md`: local setup and quality command reference.
- `README.md`: project overview and command summary.
- `scripts/`: lightweight Python repository quality scripts.
- `tests/`: tests for repository tooling and application behavior.
- `pyproject.toml`: Python tool configuration for linting, typing, tests, and coverage.
- `requirements-app.txt`: MVP 1 runtime dependencies.
- `requirements-dev.txt`: development tooling dependencies, including runtime dependencies for checks.
- `requirements-notebook.txt`: optional dependencies for exploratory notebooks.
- `.github/workflows/ci.yml`: GitHub Actions workflow for the standard checks.

The selected local MVP stack is Python, FastAPI, SQLAlchemy, SQLite, React, Vite, TypeScript, and MapLibre GL. Preserve this stack unless an explicit task or product decision changes it. No production deployment architecture has been selected.

The canonical product routes are `/` and `/territorios` for public territorial
analysis and `/acompanhamento` for synthetic municipal operations. Product
frontend code uses `/api/territorial/*` and `/api/operations/*`; older map and
MVP 2 routes are compatibility surfaces.

## Setup Commands

Use Python 3.11 or newer for the current documentation/tooling quality gates.

```bash
python -m pip install -r requirements-dev.txt
```

The development requirements include the runtime stack through `requirements-app.txt`.

Frontend work requires Node.js `^20.19.0` or `>=22.12.0`. CI uses Node.js 22.

## Development Commands

```bash
make check
make lint
make format
make format-check
make test
make coverage
make complexity
make deps
make mutation
make frontend-install
make frontend-dev
make frontend-check
make frontend-build
make demo
```

The standard Python command for Codex and developers is:

```bash
make check
```

Run `make frontend-check` when changing `frontend/` or frontend build integration.

## Test Commands

- `make test`: runs the Python test suite for repository tooling and application behavior.
- `make coverage`: runs the same tests with coverage thresholds.
- `make frontend-check`: runs frontend linting, type checking, tests, and a production build.

Add focused tests for behavior changes and keep `make check` as the stable Python fast gate.

## Quality Gates

Current Python fast gate:

- Python linting through Ruff.
- Markdown formatting checks through mdformat.
- Python formatting checks through Ruff.
- Python type checking through mypy.
- Repository tooling and application tests through pytest.

Frontend gate:

- ESLint.
- TypeScript type checking.
- Vitest component and workflow tests.
- Vite production build.

Additional reporting gates:

- `make coverage`: coverage for current automated tests.
- `make complexity`: largest source/documentation files plus Radon complexity reporting for tooling scripts.
- `make deps`: local Python import cycle detection for repository tooling and application code.
- `make mutation`: intentionally skipped until critical application logic exists.

Coverage and dependency checks now include the MVP 1 package. Do not add fake mutation targets; configure a real mutation tool only when it is useful for critical domain logic.

## Architecture Rules

- Keep project documentation aligned with the MVP premise: public and official aggregate data first; local micro-assistance data only when integration, authorization, and governance exist.
- Preserve the health-safety boundary: the platform supports decision-making and operations; it must not claim to diagnose, prescribe, or replace professional judgment.
- Treat LGPD and data minimization as architectural constraints, not optional copy.
- Do not put business logic into frontend-only modules.
- Keep domain rules, epidemiological indicators, data ingestion, persistence, and presentation separated.
- Avoid circular imports and broad shared utility modules.
- Prefer cohesive modules over adding more code to very large files.
- Keep `guia_validacao_de_dominio.md` aligned with provisional health-domain rules and their generated evidence.

## Definition Of Done

A task is complete only when:

1. Relevant tests were added or updated for behavior changes.
1. `make check` passes, or skipped checks are explained with the concrete reason.
1. `make frontend-check` passes when frontend behavior or build integration changes.
1. Coverage does not materially decrease once application coverage exists.
1. No new lint errors are introduced.
1. No new type errors are introduced where type checking is configured.
1. No obvious architectural boundary violations are introduced.
1. The final response states what changed.
1. The final response lists files changed.
1. The final response lists commands run.
1. The final response states which checks passed.
1. The final response states which checks were skipped and why.

## Rules For Future Codex Sessions

- Inspect relevant files before editing.
- Prefer small, localized changes.
- Preserve public APIs and documented product assumptions unless explicitly asked to change them.
- Add or update tests for behavior changes.
- Run `make check` before finishing whenever dependencies are available.
- Run `make frontend-check` for frontend behavior or build-integration changes.
- Do not weaken tests, lint rules, type checks, or health-safety language just to make checks pass.
- Do not refactor unrelated code just because it is imperfect.
- Do not expand beyond the selected MVP stack, add real patient-level data, or introduce AI models without a task that asks for it.
- Treat `proximos_passos.md` as the canonical implementation order. Update its status and review date in the same change that starts or completes a listed capability, and document the reason for any reprioritization.
- For health-domain behavior, keep recommendations transparent, auditable, and subject to human validation.
- Explain skipped checks clearly.
- Summarize changed files and commands run in the final response.
