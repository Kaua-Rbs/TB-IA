# TB-IA

Documentation and MVP 1 implementation workspace for an intelligent tuberculosis public health decision-support platform.

The product concept focuses on helping primary care and municipal surveillance teams identify priority territories, missed screening opportunities, patient follow-up risks, and operational strategies for tuberculosis control. The current application code implements the first public-data territorial intelligence slice for MVP 1.

The application is implemented in Python. The active stack includes a public-data ingestion pipeline, canonical SQLite storage, transparent indicator/scenario logic, and a small local FastAPI dashboard.

## Key Documents

- `descricao_do_projeto.md`: product vision, scope, MVP assumptions, data sources, and LGPD constraints.
- `frentes_de_desenvolvimento.md`: workstreams for product, evidence, data, rules, interface, architecture, and validation.
- `referencias.md`: related systems, papers, and design references for public health surveillance and TB decision support.
- `especificacao_tecnica_do_sistema.md`: engineering-oriented specification for MVP scope, data contracts, architecture, workflows, governance, and validation.
- `documentos/`: source PDFs and supporting reference documents used during project formulation.
- `notebooks/`: exploratory notebooks and scripts for public-data loading and visualization.
- `src/tbia/`: MVP 1 Python package for ingestion, indicators, scenarios, storage, CLI, and dashboard.
- `AGENTS.md`: project-specific instructions for future Codex sessions.
- `CONTRIBUTING.md`: setup and quality command reference.

## Setup

```bash
python -m pip install -r requirements-dev.txt
```

## MVP 1 Application

```bash
python -m tbia download-datasus-samples --uf CE --year 2023 --sih-all-months
python -m tbia ingest --uf CE --uf-code 23 --year 2023
python -m tbia validate-sinan-mappings --uf CE --uf-code 23 --year 2023
python -m tbia compute-indicators --uf CE --year 2023
python -m tbia build-scenarios --uf CE --year 2023
python -m tbia serve
```

`download-datasus-samples` stores public DATASUS DBC files under `data/raw/public_sources/datasus_samples/`; use `--sih-all-months` for the full SIH/SUS hospitalization year. MVP 1 CE/2023 uses 2022 IBGE Census resident population as the default denominator, so rates are explicitly caveated as 2023 events over 2022 Census population. `validate-sinan-mappings` writes a technical audit under `data/processed/mvp1/validation/`; it does not replace domain review against official SINAN-TB dictionaries and indicator handbooks. Manual CSV fallbacks are read from `data/raw/public_sources/manual/`.

## Exploratory Notebooks

```bash
python -m pip install -r requirements-notebook.txt
jupyter lab notebooks/explorar_bases_publicas.ipynb
```

Notebook downloads and generated CSVs are written under `data/`, which is ignored by git.

## Quality Commands

```bash
make check
make coverage
make complexity
make deps
make mutation
```

`make check` is the standard fast gate for local development, CI, and future Codex sessions.

The standard checks now include the MVP 1 Python package. Mutation testing remains outside the default gate until a dedicated mutation tool is configured for critical domain rules.
