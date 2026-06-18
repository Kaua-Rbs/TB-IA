# Contributing

## Current Repository State

This repository currently contains product and planning documentation for a tuberculosis public health decision-support platform. It does not yet contain application source code.

The product implementation language is expected to be Python. The active quality setup is therefore Python-based but documentation-first, with lightweight repository tooling in `scripts/` and tests in `tests/`.

## Setup

Install Python 3.11 or newer, then install development dependencies:

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
- Ruff linting for repository tooling.
- Ruff and mdformat formatting checks.
- mypy type checking for repository tooling.
- pytest tests for repository documentation rules.

## Additional Quality Commands

```bash
make coverage
make complexity
make deps
make mutation
```

- `make coverage` runs tests with coverage thresholds for the current tooling.
- `make complexity` reports large files and Python complexity metrics.
- `make deps` checks the current local Python import graph for cycles.
- `make mutation` is intentionally a no-op until critical application logic exists.

## Adding Application Code

When a Python backend, data pipeline, or model component is added:

- Add stack-specific linting, formatting, type checking, tests, and coverage.
- Keep `make check` as the single fast local gate.
- Add dependency architecture rules that match the real module layout.
- Add mutation testing, such as mutmut, only for critical logic and keep it outside the default CI gate unless it is fast.
- Update `AGENTS.md`, `README.md`, and this file with the new commands.

## Definition Of Done

A change is ready when relevant tests exist, `make check` passes, coverage is not materially reduced, and the final handoff explains changed files, commands run, passed checks, and any skipped checks.
