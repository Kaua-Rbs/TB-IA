# TB-IA

Planning, documentation, and implementation workspace for an intelligent
tuberculosis public health decision-support platform.

The product concept focuses on helping primary care and municipal surveillance teams identify priority territories, missed screening opportunities, patient follow-up risks, and operational strategies for tuberculosis control. The current application code implements the first public-data territorial intelligence slice for MVP 1 and a synthetic, pseudonymized municipal operations slice for MVP 2.

The backend is implemented in Python. The active stack includes public-data ingestion, synthetic local municipal CSV ingestion, canonical SQLite storage, transparent indicator/scenario/alert logic, FastAPI APIs, and a dedicated React/Vite frontend served by FastAPI after build.

## Key Documents

- `descricao_do_projeto.md`: product vision, scope, MVP assumptions, data sources, and LGPD constraints.
- `frentes_de_desenvolvimento.md`: workstreams for product, evidence, data, rules, interface, architecture, and validation.
- `proximos_passos.md`: canonical prioritized roadmap, capability statuses, dependencies, and Biochallenge completion work.
- `referencias.md`: related systems, papers, and design references for public health surveillance and TB decision support.
- `especificacao_tecnica_do_sistema.md`: engineering-oriented specification for MVP scope, data contracts, architecture, workflows, governance, and validation.
- `mvp2_municipal_contracts.md`: synthetic municipal CSV contracts, privacy rules, alert rules, and demo workflow for the MVP 2 starter slice.
- `documentos/`: source PDFs and supporting reference documents used during project formulation.
- `notebooks/`: exploratory notebooks and scripts for public-data loading and visualization.
- `src/tbia/`: Python package for ingestion, domain logic, storage, CLI, APIs, and fallback dashboards.
- `AGENTS.md`: project-specific instructions for future Codex sessions.
- `CONTRIBUTING.md`: setup and quality command reference.

## Setup

Use Python 3.11 or newer. The current Vite workspace requires Node.js
`^20.19.0` or `>=22.12.0`.

```bash
python -m pip install -r requirements-dev.txt
make frontend-install
```

## Complete Demonstration

Prepare the data for the complete CE/2023 demonstration in one cache-aware
command:

```bash
make demo
# equivalent to
python -m tbia prepare-demo
```

Build the current React product and start the integrated local application:

```bash
make frontend-build
python -m tbia serve
```

FastAPI then serves the territorial workbench at `/` and `/territorios`, the
synthetic municipal operations queue at `/acompanhamento`, and the API
documentation at `/docs`. `make demo` prepares data but does not start the
server.

`prepare-demo` downloads only missing public DATASUS files, uses all 12 SIH/SUS
months by default, runs the territorial pipeline, regenerates the seven
deterministic synthetic municipal CSVs, and builds operational alerts in the
same database. It safely replaces the selected scope/year and preserves other
years and UFs. Use `--sih-january-only` for a faster partial SIH/SUS
demonstration. Partial or coverage-unknown SIH/SUS aggregates remain available
for audit but are excluded from annual hospitalization indicators and rankings.
Pass the same `--database-url` to `prepare-demo` and `serve` when using a
non-default database.

The individual commands remain available for source-specific debugging:

```bash
python -m tbia download-datasus-samples --uf CE --year 2023 --sih-all-months
python -m tbia ingest --uf CE --year 2023
python -m tbia validate-sinan-mappings --uf CE --year 2023
python -m tbia compute-indicators --uf CE --year 2023
python -m tbia build-scenarios --uf CE --year 2023
python -m tbia serve
```

`download-datasus-samples` stores public DATASUS DBC files under `data/raw/public_sources/datasus_samples/`; use `--sih-all-months` for the full SIH/SUS hospitalization year. `--uf-code` is inferred from `--uf` when omitted. Use `--uf BR` to orchestrate all 27 UFs: SINAN-TB Brasil is downloaded/read once, while SIM, SIH/SUS, CNES, IBGE Localidades, population denominators, and IBGE Malhas are handled by UF. MVP 1 CE/2023 uses 2022 IBGE Census resident population as the default denominator, so rates are explicitly caveated as 2023 events over 2022 Census population. `ingest` also caches simplified municipality GeoJSON from IBGE Malhas under `data/raw/public_sources/ibge_malhas/` for the dashboard choropleth map. `validate-sinan-mappings` writes a technical audit under `data/processed/mvp1/validation/`; it does not replace domain review against official SINAN-TB dictionaries and indicator handbooks. `compute-indicators` writes `indicator_validation_<scope>_<year>.json` in the same validation directory and records scope-aware `indicator_validation` source freshness; a failed status means mechanical invariants such as bounded proportions need review, while warning-only zero denominators document expected missingness and suppressed public values remain `null`. Legacy import history without scope metadata is preserved but excluded from scoped readiness until data is re-ingested. Manual CSV fallbacks are read from `data/raw/public_sources/manual/`.

The product frontend at `/` and `/territorios` is a responsive public aggregate
territorial workbench with Portuguese default UI text and optional English via
`?lang=en`. It exposes data readiness, UF/year/comparison controls,
municipality search, synchronized MapLibre map/ranking/dossier selection,
source freshness, and grouped territory reports. The map legend follows the
selected layer, reports values and units, and distinguishes available,
suppressed, and missing data. `uf=BR` shows a national municipality map using
national percentiles; a single UF can switch between the existing intra-UF
ranking (`comparison_scope=uf`) and national comparison
(`comparison_scope=national`). The ranking is built from the same enriched map
payload used by the choropleth, including `top_scenarios`, severity, priority
score, and data status. The map does not use external tile providers and does
not display patient-level, address-level, or operational alert locations. If
the map panel is blank, first verify that `ingest` recorded a successful
`ibge_malhas` run and that
`/api/territorial/map?uf=CE&year=2023&comparison_scope=uf` has non-null
geometries.

Public submunicipal map context is optional and contextual only. `ingest` scans normalized GeoJSON files under `data/raw/public_sources/ibge_intramunicipal/`; each FeatureCollection feature must provide `territory_id`, `name`, `territory_type`, `parent_id`, `uf_code`, and `uf_sigla`, with Polygon or MultiPolygon geometry. Current bairro records use `territory_type=neighborhood_reference` and `parent_id=<municipality_id>`. These polygons are public geographic references for drill-down only: TB indicators, scenarios, ranking, reports, and prioritization remain municipality-level. Convert public IBGE or municipal GPKG/SHP/KML sources to this normalized GeoJSON contract before ingestion; the MVP does not add GeoPandas/Fiona/Shapely parsing.

National MVP 1 example:

```bash
python -m tbia download-datasus-samples --uf BR --year 2023 --sih-all-months
python -m tbia ingest --uf BR --year 2023
python -m tbia compute-indicators --uf BR --year 2023
python -m tbia build-scenarios --uf BR --year 2023
python -m tbia serve
```

## MVP 2 Synthetic Municipal Demo

```bash
# Included automatically by prepare-demo; these commands remain available separately.
python -m tbia generate-mvp2-sample-data --output-dir data/raw/municipal_demo
python -m tbia ingest-local --raw-dir data/raw/municipal_demo --year 2023
python -m tbia build-operational-alerts --year 2023 --reference-date 2026-06-29
python -m tbia serve
```

The MVP 2 demo uses synthetic, pseudonymized local CSVs only and rejects
obvious identifiable columns in patient-level files. The product queue is
available at `/acompanhamento` and uses `/api/operations/summary`,
`/api/operations/alerts`, and `/api/operations/alerts/{alert_id}`. It provides
URL-backed type, severity, status, facility, and team filters; explicit overdue
and high-severity markers; a sticky desktop dossier; and expandable mobile
alert details. The synthetic/pseudonymized boundary remains visible in the
shared product shell, with Portuguese and English through `lang=pt` or
`lang=en`. The older `/api/mvp2/*` paths and the Jinja `/mvp2` route remain for
backend compatibility. See `mvp2_municipal_contracts.md` for schemas and alert
rules.

## Frontend Development

The dedicated product UI lives in `frontend/` and is built with React, Vite, TypeScript, and MapLibre GL. Use npm for the JavaScript workspace:

```bash
make frontend-install
python -m tbia serve --host 127.0.0.1 --port 8000
make frontend-dev
```

During development, Vite serves the UI on port 5173 and proxies `/api` to the FastAPI backend on port 8000. For the integrated local app, build the SPA and start FastAPI:

```bash
make frontend-build
python -m tbia serve --host 127.0.0.1 --port 8000
```

When `frontend/dist/index.html` exists, FastAPI serves the SPA for `/`, `/territorios`, and `/acompanhamento`, with static assets under `/static/app`. If the frontend build is absent, the existing Jinja templates remain as a fallback so the Python application can still run. Product-facing frontend code should call `/api/territorial/*` and `/api/operations/*`; the older `/api/map/*` and `/api/mvp2/*` routes remain available for compatibility.

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
