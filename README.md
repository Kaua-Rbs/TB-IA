# TB-IA

Documentation and MVP 1 implementation workspace for an intelligent tuberculosis public health decision-support platform.

The product concept focuses on helping primary care and municipal surveillance teams identify priority territories, missed screening opportunities, patient follow-up risks, and operational strategies for tuberculosis control. The current application code implements the first public-data territorial intelligence slice for MVP 1 and a synthetic, pseudonymized municipal operations slice for MVP 2.

The application is implemented in Python. The active stack includes public-data ingestion, synthetic local municipal CSV ingestion, canonical SQLite storage, transparent indicator/scenario/alert logic, and small local FastAPI dashboards.

## Key Documents

- `descricao_do_projeto.md`: product vision, scope, MVP assumptions, data sources, and LGPD constraints.
- `frentes_de_desenvolvimento.md`: workstreams for product, evidence, data, rules, interface, architecture, and validation.
- `referencias.md`: related systems, papers, and design references for public health surveillance and TB decision support.
- `especificacao_tecnica_do_sistema.md`: engineering-oriented specification for MVP scope, data contracts, architecture, workflows, governance, and validation.
- `mvp2_municipal_contracts.md`: synthetic municipal CSV contracts, privacy rules, alert rules, and demo workflow for the MVP 2 starter slice.
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

`download-datasus-samples` stores public DATASUS DBC files under `data/raw/public_sources/datasus_samples/`; use `--sih-all-months` for the full SIH/SUS hospitalization year. MVP 1 CE/2023 uses 2022 IBGE Census resident population as the default denominator, so rates are explicitly caveated as 2023 events over 2022 Census population. `ingest` also caches simplified municipality GeoJSON from IBGE Malhas under `data/raw/public_sources/ibge_malhas/` for the dashboard choropleth map. `validate-sinan-mappings` writes a technical audit under `data/processed/mvp1/validation/`; it does not replace domain review against official SINAN-TB dictionaries and indicator handbooks. `compute-indicators` writes `indicator_validation_<year>.json` in the same validation directory and records `indicator_validation` in source freshness; a failed status means mechanical invariants such as bounded proportions need review, while warning-only zero denominators document expected missingness and suppressed public values remain `null`. Manual CSV fallbacks are read from `data/raw/public_sources/manual/`.

The local dashboard at `/` includes a municipality-level public aggregate map, priority ranking, source freshness, and territory detail reports. The map does not use external tile providers and does not display patient-level, address-level, or MVP 2 operational alert locations. If the map panel is blank, first verify that `ingest` recorded a successful `ibge_malhas` run and that `/api/map/municipalities?uf=CE&year=2023` has non-null geometries; if geometries exist, check whether the browser can load the Leaflet CDN assets.

## MVP 2 Synthetic Municipal Demo

```bash
python -m tbia generate-mvp2-sample-data --output-dir data/raw/municipal_demo
python -m tbia ingest-local --raw-dir data/raw/municipal_demo --year 2023
python -m tbia build-operational-alerts --year 2023 --reference-date 2026-06-29
python -m tbia serve
```

The MVP 2 demo uses synthetic, pseudonymized local CSVs only. It rejects obvious identifiable columns in patient-level files and exposes operational alert queues at `/mvp2` plus `/api/mvp2/summary`, `/api/mvp2/alerts`, and `/api/mvp2/alerts/{alert_id}`. See `mvp2_municipal_contracts.md` for schemas and alert rules.

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
