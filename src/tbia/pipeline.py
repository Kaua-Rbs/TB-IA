from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from sqlalchemy.orm import Session

from tbia.domain.indicators import INDICATOR_DEFINITIONS, compute_indicator_values
from tbia.domain.models import ImportRun
from tbia.domain.recommendations import STRATEGIES, build_recommendations
from tbia.domain.scenarios import DEFAULT_SCENARIO_RULES, build_territory_scenarios
from tbia.ingest.contracts import SOURCE_CONTRACTS
from tbia.ingest.readers import (
    fetch_json,
    read_case_aggregates_csv,
    read_facilities_csv,
    read_hospitalization_aggregates_csv,
    read_ibge_municipalities,
    read_mortality_aggregates_csv,
    read_population_csv,
    read_sidra_population_payload,
)
from tbia.storage import (
    load_cases,
    load_hospitalizations,
    load_indicator_values,
    load_mortalities,
    load_populations,
    save_case_aggregates,
    save_data_sources,
    save_facilities,
    save_hospitalizations,
    save_import_run,
    save_indicator_definitions,
    save_indicator_values,
    save_mortalities,
    save_populations,
    save_recommendations,
    save_scenario_rules,
    save_strategies,
    save_territories,
    save_territory_scenarios,
)

T = TypeVar("T")


@dataclass(frozen=True)
class Mvp1Config:
    uf: str = "CE"
    uf_code: str = "23"
    year: int = 2023
    raw_dir: Path = Path("data/raw/public_sources")
    processed_dir: Path = Path("data/processed/mvp1")
    minimum_count: int = 5

    @property
    def manual_dir(self) -> Path:
        return self.raw_dir / "manual"

    def manual_csv(self, filename: str) -> Path:
        return self.manual_dir / filename


def seed_reference_data(session: Session) -> None:
    save_data_sources(session, (contract.as_data_source() for contract in SOURCE_CONTRACTS))
    save_indicator_definitions(session, INDICATOR_DEFINITIONS)
    save_scenario_rules(session, DEFAULT_SCENARIO_RULES)
    save_strategies(session, STRATEGIES)


def ingest_public_data(session: Session, config: Mvp1Config) -> None:
    seed_reference_data(session)
    ingest_ibge_territories(session, config)
    ingest_ibge_population(session, config)
    ingest_optional_csv_sources(session, config)


def ingest_ibge_territories(session: Session, config: Mvp1Config) -> None:
    started_at = datetime.now(UTC)
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{config.uf_code}/municipios"
    try:
        payload = fetch_json(url)
        territories = read_ibge_municipalities(payload, config.uf)
        save_territories(session, territories)
        save_import_run(
            session,
            ImportRun(
                source_id="ibge_localidades",
                status="success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=len(territories),
                message=url,
            ),
        )
    except Exception as exc:
        save_import_run(
            session,
            ImportRun(
                source_id="ibge_localidades",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=str(exc),
            ),
        )


def ingest_ibge_population(session: Session, config: Mvp1Config) -> None:
    if config.manual_csv("population_denominators.csv").exists():
        return

    started_at = datetime.now(UTC)
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/"
        f"{config.year}/variaveis/9324?localidades=N6[N3[{config.uf_code}]]"
    )
    try:
        payload = fetch_json(url)
        populations = read_sidra_population_payload(payload, config.year)
        save_populations(session, populations)
        save_import_run(
            session,
            ImportRun(
                source_id="ibge_population",
                status="success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=len(populations),
                message=url,
            ),
        )
    except Exception as exc:
        save_import_run(
            session,
            ImportRun(
                source_id="ibge_population",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=str(exc),
            ),
        )


def ingest_optional_csv_sources(session: Session, config: Mvp1Config) -> None:
    load_optional_csv_source(
        session,
        config,
        "ibge_population",
        "population_denominators.csv",
        read_population_csv,
        save_populations,
    )
    load_optional_csv_source(
        session,
        config,
        "sinan_tb",
        "case_aggregates.csv",
        read_case_aggregates_csv,
        save_case_aggregates,
    )
    load_optional_csv_source(
        session,
        config,
        "sim",
        "mortality_aggregates.csv",
        read_mortality_aggregates_csv,
        save_mortalities,
    )
    load_optional_csv_source(
        session,
        config,
        "sih_sus",
        "hospitalization_aggregates.csv",
        read_hospitalization_aggregates_csv,
        save_hospitalizations,
    )
    load_optional_csv_source(
        session,
        config,
        "cnes",
        "facilities.csv",
        read_facilities_csv,
        save_facilities,
    )


def load_optional_csv_source(
    session: Session,
    config: Mvp1Config,
    source_id: str,
    filename: str,
    reader: Callable[[Path], Sequence[T]],
    saver: Callable[[Session, Sequence[T]], None],
) -> None:
    path = config.manual_csv(filename)
    started_at = datetime.now(UTC)
    if not path.exists():
        save_import_run(
            session,
            ImportRun(
                source_id=source_id,
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"manual CSV not found: {path}",
            ),
        )
        return

    rows = reader(path)
    saver(session, rows)
    save_import_run(
        session,
        ImportRun(
            source_id=source_id,
            status="success",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=len(rows),
            message=f"loaded manual CSV: {path}",
        ),
    )


def compute_and_store_indicators(session: Session, config: Mvp1Config) -> int:
    values = compute_indicator_values(
        load_populations(session, config.year),
        load_cases(session, config.year),
        load_mortalities(session, config.year),
        load_hospitalizations(session, config.year),
        year=config.year,
        minimum_count=config.minimum_count,
    )
    save_indicator_values(session, values, config.year)
    return len(values)


def build_and_store_scenarios(session: Session, config: Mvp1Config) -> tuple[int, int]:
    scenarios = build_territory_scenarios(load_indicator_values(session, config.year))
    recommendations = build_recommendations(scenarios)
    save_territory_scenarios(session, scenarios, config.year)
    save_recommendations(session, recommendations, config.year)
    return len(scenarios), len(recommendations)
