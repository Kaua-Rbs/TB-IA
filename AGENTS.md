# Codex Project Instructions

## Project Overview

This repository is currently a planning and documentation workspace for a tuberculosis public health decision-support platform. The product goal is to support primary care and municipal surveillance teams with territorial analysis, operational indicators, triage support, treatment follow-up risk signals, and tuberculosis resistance vigilance.

The product implementation language is expected to be Python. The repository does not yet contain production application code. Quality gates are therefore Python-based but documentation-first today, with explicit commands reserved for future application testing, coverage, dependency architecture, complexity, and mutation testing once source code is added.

## Repository Structure

- `descricao_do_projeto.md`: product vision, public health scope, data assumptions, LGPD boundaries, and MVP constraints.
- `frentes_de_desenvolvimento.md`: workstreams for scope, users, evidence, data, rules, product, architecture, governance, and validation.
- `AGENTS.md`: instructions for future Codex sessions.
- `CONTRIBUTING.md`: local setup and quality command reference.
- `README.md`: project overview and command summary.
- `scripts/`: lightweight Python repository quality scripts.
- `tests/`: tests for the repository quality scripts.
- `pyproject.toml`: Python tool configuration for linting, typing, tests, and coverage.
- `requirements-dev.txt`: development tooling dependencies.
- `.github/workflows/ci.yml`: GitHub Actions workflow for the standard checks.

No backend, frontend, database, API, package, or deployment architecture has been selected yet. Do not invent one without an explicit task or supporting product decision.

## Setup Commands

Use Python 3.11 or newer for the current documentation/tooling quality gates.

```bash
python -m pip install -r requirements-dev.txt
```

If the project later adds an application stack, add stack-specific setup commands here and in `CONTRIBUTING.md`.

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
```

The standard local command for Codex and developers is:

```bash
make check
```

## Test Commands

- `make test`: runs the Python test suite for the repository quality scripts.
- `make coverage`: runs the same tests with coverage thresholds.

When application code is added, add focused tests for behavior changes and keep `make check` as the stable fast gate.

## Quality Gates

Current fast gate:

- Python linting through Ruff.
- Markdown formatting checks through mdformat.
- Python formatting checks through Ruff.
- Python type checking through mypy.
- Repository documentation tests through pytest.

Additional reporting gates:

- `make coverage`: coverage for current automated tests.
- `make complexity`: largest source/documentation files plus Radon complexity reporting for tooling scripts.
- `make deps`: local Python import cycle detection for repository tooling.
- `make mutation`: intentionally skipped until critical application logic exists.

Because this repo has no application source yet, do not add fake coverage, fake dependency layers, or fake mutation targets. Add real Python package-specific rules when the backend, data pipeline, or model logic is created.

## Architecture Rules

- Keep project documentation aligned with the MVP premise: public and official aggregate data first; local micro-assistance data only when integration, authorization, and governance exist.
- Preserve the health-safety boundary: the platform supports decision-making and operations; it must not claim to diagnose, prescribe, or replace professional judgment.
- Treat LGPD and data minimization as architectural constraints, not optional copy.
- Do not put business logic into UI-only modules once a frontend exists.
- Keep domain rules, epidemiological indicators, data ingestion, persistence, and presentation separated once source code is introduced.
- Avoid circular imports and broad shared utility modules.
- Prefer cohesive modules over adding more code to very large files.

## Definition Of Done

A task is complete only when:

1. Relevant tests were added or updated for behavior changes.
1. `make check` passes, or skipped checks are explained with the concrete reason.
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
- Do not weaken tests, lint rules, type checks, or health-safety language just to make checks pass.
- Do not refactor unrelated code just because it is imperfect.
- Do not add a backend, frontend, database, AI model, or deployment stack without a task that asks for it.
- For health-domain behavior, keep recommendations transparent, auditable, and subject to human validation.
- Explain skipped checks clearly.
- Summarize changed files and commands run in the final response.
