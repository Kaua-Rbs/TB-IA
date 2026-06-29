# Contributing

## Current Repository State

This repository contains product/planning documentation and the first MVP 1 Python implementation for a tuberculosis public health decision-support platform.

The active quality setup checks the MVP 1 package in `src/tbia/`, lightweight repository tooling in `scripts/`, and tests in `tests/`.

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

## MVP 1 Commands

```bash
python -m tbia download-datasus-samples --uf CE --year 2023 --sih-all-months
python -m tbia ingest --uf CE --uf-code 23 --year 2023
python -m tbia validate-sinan-mappings --uf CE --uf-code 23 --year 2023
python -m tbia compute-indicators --uf CE --year 2023
python -m tbia build-scenarios --uf CE --year 2023
python -m tbia serve
```

The implementation must keep ingestion, domain indicator logic, scenario rules, storage, and presentation separated. Patient-level data and clinical decision automation remain out of scope for MVP 1.

## Definition Of Done

A change is ready when relevant tests exist, `make check` passes, coverage is not materially reduced, and the final handoff explains changed files, commands run, passed checks, and any skipped checks.
