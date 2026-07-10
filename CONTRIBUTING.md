# Contributing

## Current Repository State

This repository contains product/planning documentation, the public-data Python backend, the synthetic municipal operational pilot, and a dedicated React/Vite frontend for a tuberculosis public health decision-support platform.

The active quality setup checks the MVP package in `src/tbia/`, lightweight repository tooling in `scripts/`, and tests in `tests/`.

## Setup

Install Python 3.11 or newer, then install development and application dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

## Standard Check

Run the same fast checks used by CI:

```bash
make check
```

`make check` runs:

- Documentation hygiene checks.
- Ruff linting for `src/`, `scripts/`, and `tests/`.
- Ruff and mdformat formatting checks.
- mypy type checking for `src/`, `scripts/`, and `tests/`.
- pytest tests for repository documentation rules and MVP 1 behavior.

## Commit Messages

Use Conventional Commit subjects for all commits, such as `feat(mvp1): add map validation`, `fix(api): return 404 for missing territories`, or `docs: update setup notes`. Keep the subject concise and use a scope when it clarifies the affected area.

## Additional Quality Commands

```bash
make coverage
make complexity
make deps
make mutation
```

- `make coverage` runs tests with coverage thresholds for repository tooling and critical MVP 1 logic.
- `make complexity` reports large files and Python complexity metrics.
- `make deps` checks the current local Python import graph for cycles, including `src/` layout imports.
- `make mutation` is outside the default gate until a mutation tool is configured for critical application logic.

## Frontend Commands

The frontend is intentionally separate from the Python fast gate while the project transitions to a dedicated UI stack. Run these commands when changing `frontend/`:

```bash
make frontend-install
make frontend-check
make frontend-build
```

For local development, run FastAPI on port 8000 and Vite on port 5173:

```bash
python -m tbia serve --host 127.0.0.1 --port 8000
make frontend-dev
```

After `make frontend-build`, FastAPI serves the compiled SPA on `/`, `/territorios`, and `/acompanhamento`. Without `frontend/dist`, the Jinja templates remain the fallback.

## MVP 1 Commands

For a complete default CE/2023 demonstration, including the synthetic municipal
operations layer:

```bash
make demo
python -m tbia serve
```

The workflow is cache-aware, uses the full SIH/SUS year, and upserts only the
selected scope/year. Existing files under `data/raw/municipal_demo` are
regenerated as deterministic synthetic samples. Use the individual commands
below when debugging a specific stage:

```bash
python -m tbia download-datasus-samples --uf CE --year 2023 --sih-all-months
python -m tbia ingest --uf CE --uf-code 23 --year 2023
python -m tbia validate-sinan-mappings --uf CE --uf-code 23 --year 2023
python -m tbia compute-indicators --uf CE --year 2023
python -m tbia build-scenarios --uf CE --year 2023
python -m tbia serve
```

The implementation must keep ingestion, domain indicator logic, scenario rules, storage, and presentation separated. Patient-level data and clinical decision automation remain out of scope for MVP 1.

## MVP 2 Synthetic Municipal Demo

```bash
python -m tbia generate-mvp2-sample-data --output-dir data/raw/municipal_demo
python -m tbia ingest-local --raw-dir data/raw/municipal_demo --year 2023
python -m tbia build-operational-alerts --year 2023 --reference-date 2026-06-29
python -m tbia serve
```

MVP 2 currently accepts only synthetic or already pseudonymized municipal CSVs. Do not add CPF, CNS, person names, addresses, phone numbers, patient-level maps, task assignment, authentication, or clinical automation unless a future task explicitly changes the governed scope. The operational dashboard is `/mvp2`; the CSV schemas and alert rules are documented in `mvp2_municipal_contracts.md`.

## Definition Of Done

A change is ready when relevant tests exist, `make check` passes, coverage is not materially reduced, and the final handoff explains changed files, commands run, passed checks, and any skipped checks.
