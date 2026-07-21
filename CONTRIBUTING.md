# Contributing

## Current Repository State

This repository contains product/planning documentation, the public-data Python backend, the synthetic municipal operational pilot, and a dedicated React/Vite frontend for a tuberculosis public health decision-support platform.

The active quality setup checks the MVP package in `src/tbia/`, lightweight repository tooling in `scripts/`, and tests in `tests/`.

## Setup

Install Python 3.11 or newer, then install development and application
dependencies. Frontend work additionally requires Node.js `^20.19.0` or
`>=22.12.0`.

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
- pytest tests for repository documentation rules and application behavior.

## Commit Messages

Use Conventional Commit subjects for all commits, such as `feat(mvp1): add map validation`, `fix(api): return 404 for missing territories`, or `docs: update setup notes`. Keep the subject concise and use a scope when it clarifies the affected area.

## Roadmap Maintenance

`proximos_passos.md` is the canonical prioritized roadmap. Update its status and
last-review date in the same commit that starts or completes a listed
capability. Do not reorder capabilities or mark one complete without recording
the reason and satisfying its documented exit criteria.

## Domain Validation

`guia_validacao_de_dominio.md` is the plain-language handoff for clinical and
epidemiological reviewers. Update it whenever a provisional health-domain rule
changes its universe, source-field interpretation, threshold, severity,
ranking dimension, recommendation, evidence, or review status.

Technical checks may prepare evidence, but they must not be recorded as
clinical approval. Keep provisional rules marked `pending_domain_review` until
the guide's decision record is completed by an appropriately qualified
reviewer and requested changes have passed the normal quality gates.

Regenerate the CAP-01 ranking comparison with
`python -m tbia validate-diagnostic-ranking --uf CE --year 2023`.

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

The active React/Vite frontend has a gate separate from the Python fast gate.
GitHub Actions validates it in an independent Node 22 job. Run these commands
when changing `frontend/`:

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

## Demonstration Commands

For a complete default CE/2023 demonstration, including the synthetic municipal
operations layer:

```bash
make demo
make frontend-build
python -m tbia serve
```

The workflow is cache-aware, uses the full SIH/SUS year, and upserts only the
selected scope/year. Existing files under `data/raw/municipal_demo` are
regenerated as deterministic synthetic samples. Use the individual commands
below when debugging a specific stage. Partial or coverage-unknown SIH/SUS
aggregates are retained for audit but do not contribute hospitalization
indicators or scenarios to annual rankings.

```bash
python -m tbia download-datasus-samples --uf CE --year 2023 --sih-all-months
python -m tbia ingest --uf CE --uf-code 23 --year 2023
python -m tbia validate-sinan-mappings --uf CE --uf-code 23 --year 2023
python -m tbia compute-indicators --uf CE --year 2023
python -m tbia build-scenarios --uf CE --year 2023
python -m tbia validate-diagnostic-ranking --uf CE --year 2023
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

MVP 2 currently accepts only synthetic or already pseudonymized municipal CSVs.
Do not add CPF, CNS, person names, addresses, phone numbers, patient-level maps,
task assignment, authentication, or clinical automation unless a future task
explicitly changes the governed scope. The canonical product dashboard is
`/acompanhamento` and uses `/api/operations/*`; the Jinja `/mvp2` route and
`/api/mvp2/*` remain for backend compatibility. The CSV schemas and alert rules
are documented in `mvp2_municipal_contracts.md`.

## Definition Of Done

A change is ready when relevant tests exist, `make check` passes, coverage is not materially reduced, and the final handoff explains changed files, commands run, passed checks, and any skipped checks.
