from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar, cast

from sqlalchemy.orm import Session

from tbia.domain.indicators import INDICATOR_DEFINITIONS, compute_indicator_values
from tbia.domain.models import ImportRun, PopulationDenominator
from tbia.domain.recommendations import STRATEGIES, build_recommendations
from tbia.domain.scenarios import DEFAULT_SCENARIO_RULES, build_territory_scenarios
from tbia.ingest.contracts import SOURCE_CONTRACTS
from tbia.ingest.datasus import read_datasus_records
from tbia.ingest.datasus_transforms import (
    build_datasus_municipality_map,
    transform_cnes_records,
    transform_sih_records,
    transform_sim_records,
    transform_sinan_tb_records,
)
from tbia.ingest.readers import (
    fetch_json,
    read_case_aggregates_csv,
    read_facilities_csv,
    read_hospitalization_aggregates_csv,
    read_ibge_municipalities,
    read_mortality_aggregates_csv,
    read_population_csv,
    read_sidra_population_payload,
    read_sidra_values_population_payload,
)
from tbia.ingest.sinan_validation import (
    build_sinan_mapping_report,
    write_sinan_mapping_report,
)
from tbia.storage import (
    load_cases,
    load_hospitalizations,
    load_indicator_values,
    load_mortalities,
    load_populations,
    load_territories,
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
DEFAULT_CENSUS_POPULATION_YEAR = 2022


@dataclass(frozen=True)
class Mvp1Config:
    uf: str = "CE"
    uf_code: str = "23"
    year: int = 2023
    raw_dir: Path = Path("data/raw/public_sources")
    processed_dir: Path = Path("data/processed/mvp1")
    minimum_count: int = 5
    population_source_year: int | None = None

    @property
    def manual_dir(self) -> Path:
        return self.raw_dir / "manual"

    @property
    def datasus_sample_dir(self) -> Path:
        return self.raw_dir / "datasus_samples"

    @property
    def validation_dir(self) -> Path:
        return self.processed_dir / "validation"

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
    loaded_sources: set[str] = set()
    if ingest_ibge_population(session, config):
        loaded_sources.add("ibge_population")
    loaded_sources.update(ingest_datasus_public_samples(session, config))
    record_sinan_validation_report(session, config)
    ingest_optional_csv_sources(session, config, skip_sources=loaded_sources)


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


def ingest_ibge_population(session: Session, config: Mvp1Config) -> bool:
    started_at = datetime.now(UTC)
    source_year = population_source_year(config)
    url = ibge_population_url(config.uf_code, source_year)
    try:
        payload = fetch_json(url)
        populations = read_ibge_population_payload(
            payload,
            source_year=source_year,
            analysis_year=config.year,
        )
    except Exception as exc:
        save_import_run(
            session,
            ImportRun(
                source_id="ibge_population",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"{url}: {exc}",
            ),
        )
        return False

    if not populations:
        save_import_run(
            session,
            ImportRun(
                source_id="ibge_population",
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"no IBGE population rows returned from {url}",
            ),
        )
        return False

    save_populations(session, populations)
    save_import_run(
        session,
        ImportRun(
            source_id="ibge_population",
            status="success",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=len(populations),
            message=population_import_message(source_year, config.year, url),
        ),
    )
    return True


def population_source_year(config: Mvp1Config) -> int:
    return config.population_source_year or DEFAULT_CENSUS_POPULATION_YEAR


def ibge_population_url(uf_code: str, source_year: int) -> str:
    if source_year == DEFAULT_CENSUS_POPULATION_YEAR:
        return (
            "https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%20"
            f"{uf_code}/v/93/p/{source_year}"
        )
    return (
        "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/"
        f"{source_year}/variaveis/9324?localidades=N6[N3[{uf_code}]]"
    )


def read_ibge_population_payload(
    payload: object,
    *,
    source_year: int,
    analysis_year: int,
) -> list[PopulationDenominator]:
    if source_year == DEFAULT_CENSUS_POPULATION_YEAR:
        populations = read_sidra_values_population_payload(
            cast(list[dict[str, str]], payload),
            analysis_year=analysis_year,
        )
    else:
        populations = normalize_population_year(
            read_sidra_population_payload(cast(list[dict[str, Any]], payload), source_year),
            analysis_year,
        )
    return populations


def population_import_message(source_year: int, analysis_year: int, url: str) -> str:
    if source_year == DEFAULT_CENSUS_POPULATION_YEAR:
        return (
            f"loaded IBGE Census {source_year} resident population as denominator for "
            f"analysis year {analysis_year}; rates are {analysis_year} events over "
            f"{source_year} Census population: {url}"
        )
    if source_year != analysis_year:
        return (
            f"loaded IBGE SIDRA population period {source_year} as denominator for "
            f"analysis year {analysis_year}; validate denominator year before official use: {url}"
        )
    return f"loaded IBGE SIDRA population period {source_year}: {url}"


def normalize_population_year(
    populations: Sequence[PopulationDenominator],
    analysis_year: int,
) -> list[PopulationDenominator]:
    return [
        PopulationDenominator(
            territory_id=population.territory_id,
            year=analysis_year,
            population=population.population,
            source_id=population.source_id,
            stratifier=population.stratifier,
        )
        for population in populations
    ]


def ingest_datasus_public_samples(session: Session, config: Mvp1Config) -> set[str]:
    territories = load_territories(session, config.uf)
    if not territories:
        return set()
    municipality_map = build_datasus_municipality_map(territories)
    loaded_sources: set[str] = set()

    if load_datasus_source(
        session,
        source_id="sinan_tb",
        paths=datasus_source_candidates(config, "sinan_tb"),
        transform=lambda records: transform_sinan_tb_records(
            records,
            municipality_map,
            year=config.year,
        ),
        saver=save_case_aggregates,
    ):
        loaded_sources.add("sinan_tb")

    if load_datasus_source(
        session,
        source_id="sim",
        paths=datasus_source_candidates(config, "sim"),
        transform=lambda records: transform_sim_records(
            records, municipality_map, year=config.year
        ),
        saver=save_mortalities,
    ):
        loaded_sources.add("sim")

    if load_datasus_source(
        session,
        source_id="sih_sus",
        paths=datasus_source_candidates(config, "sih_sus"),
        transform=lambda records: transform_sih_records(
            records, municipality_map, year=config.year
        ),
        saver=save_hospitalizations,
    ):
        loaded_sources.add("sih_sus")

    if load_datasus_source(
        session,
        source_id="cnes",
        paths=datasus_source_candidates(config, "cnes"),
        transform=lambda records: transform_cnes_records(records, municipality_map),
        saver=save_facilities,
    ):
        loaded_sources.add("cnes")

    return loaded_sources


def datasus_source_candidates(config: Mvp1Config, source_id: str) -> tuple[Path, ...]:
    uf = config.uf.lower()
    if source_id == "sinan_tb":
        return tuple(
            path
            for extension in ("dbf", "dbc")
            for path in (config.datasus_sample_dir / f"sinan_tb_br_{config.year}.{extension}",)
        )
    if source_id == "sim":
        return tuple(
            path
            for extension in ("dbf", "dbc")
            for path in (config.datasus_sample_dir / f"sim_{uf}_{config.year}.{extension}",)
        )
    if source_id == "sih_sus":
        return tuple(
            sorted(config.datasus_sample_dir.glob(f"sih_{uf}_{config.year}_*.dbf"))
        ) + tuple(sorted(config.datasus_sample_dir.glob(f"sih_{uf}_{config.year}_*.dbc")))
    if source_id == "cnes":
        return tuple(
            sorted(config.datasus_sample_dir.glob(f"cnes_*_{uf}_{config.year}_*.dbf"))
        ) + tuple(sorted(config.datasus_sample_dir.glob(f"cnes_*_{uf}_{config.year}_*.dbc")))
    return ()


def select_existing_datasus_paths(paths: Sequence[Path]) -> list[Path]:
    selected_by_stem: dict[str, Path] = {}
    for path in paths:
        if not path.exists():
            continue
        selected = selected_by_stem.get(path.stem)
        if selected is None or selected.suffix.lower() == ".dbc":
            selected_by_stem[path.stem] = path
    return list(selected_by_stem.values())


def load_datasus_source(
    session: Session,
    *,
    source_id: str,
    paths: Sequence[Path],
    transform: Callable[[Sequence[dict[str, object]]], Sequence[T]],
    saver: Callable[[Session, Sequence[T]], None],
) -> bool:
    started_at = datetime.now(UTC)
    existing_paths = select_existing_datasus_paths(paths)
    if not existing_paths:
        save_import_run(
            session,
            ImportRun(
                source_id=source_id,
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message="DATASUS public sample file not found",
            ),
        )
        return False

    try:
        records = [record for path in existing_paths for record in read_datasus_records(path)]
        rows = transform(records)
        if not rows:
            save_import_run(
                session,
                ImportRun(
                    source_id=source_id,
                    status="skipped",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    message=(
                        f"no canonical rows produced from {datasus_path_message(existing_paths)}"
                    ),
                ),
            )
            return False
        saver(session, rows)
        save_import_run(
            session,
            ImportRun(
                source_id=source_id,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=len(rows),
                message=f"loaded DATASUS public sample: {datasus_path_message(existing_paths)}",
            ),
        )
        return True
    except Exception as exc:
        save_import_run(
            session,
            ImportRun(
                source_id=source_id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"{datasus_path_message(existing_paths)}: {exc}",
            ),
        )
        return False


def datasus_path_message(paths: Sequence[Path]) -> str:
    return ", ".join(str(path) for path in paths)


def build_sinan_validation_report_file(config: Mvp1Config) -> tuple[Path, int]:
    paths = select_existing_datasus_paths(datasus_source_candidates(config, "sinan_tb"))
    if not paths:
        raise FileNotFoundError("SINAN-TB DATASUS public sample file not found")

    records = [record for path in paths for record in read_datasus_records(path)]
    report = build_sinan_mapping_report(records, year=config.year, uf_code=config.uf_code)
    output_path = write_sinan_mapping_report(report, config.validation_dir)
    return output_path, int(report["record_count"])


def record_sinan_validation_report(session: Session, config: Mvp1Config) -> None:
    started_at = datetime.now(UTC)
    try:
        output_path, row_count = build_sinan_validation_report_file(config)
    except FileNotFoundError as exc:
        save_import_run(
            session,
            ImportRun(
                source_id="sinan_validation",
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=str(exc),
            ),
        )
    except Exception as exc:
        save_import_run(
            session,
            ImportRun(
                source_id="sinan_validation",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=str(exc),
            ),
        )
    else:
        save_import_run(
            session,
            ImportRun(
                source_id="sinan_validation",
                status="success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=row_count,
                message=f"technical audit pending domain review: {output_path}",
            ),
        )


def ingest_optional_csv_sources(
    session: Session,
    config: Mvp1Config,
    *,
    skip_sources: set[str],
) -> None:
    load_optional_csv_source(
        session,
        config,
        "ibge_population",
        "population_denominators.csv",
        read_population_csv,
        save_populations,
        skip_sources=skip_sources,
    )
    load_optional_csv_source(
        session,
        config,
        "sinan_tb",
        "case_aggregates.csv",
        read_case_aggregates_csv,
        save_case_aggregates,
        skip_sources=skip_sources,
    )
    load_optional_csv_source(
        session,
        config,
        "sim",
        "mortality_aggregates.csv",
        read_mortality_aggregates_csv,
        save_mortalities,
        skip_sources=skip_sources,
    )
    load_optional_csv_source(
        session,
        config,
        "sih_sus",
        "hospitalization_aggregates.csv",
        read_hospitalization_aggregates_csv,
        save_hospitalizations,
        skip_sources=skip_sources,
    )
    load_optional_csv_source(
        session,
        config,
        "cnes",
        "facilities.csv",
        read_facilities_csv,
        save_facilities,
        skip_sources=skip_sources,
    )


def load_optional_csv_source(
    session: Session,
    config: Mvp1Config,
    source_id: str,
    filename: str,
    reader: Callable[[Path], Sequence[T]],
    saver: Callable[[Session, Sequence[T]], None],
    *,
    skip_sources: set[str],
) -> None:
    if source_id in skip_sources:
        return

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
            message=f"loaded manual CSV fallback: {path}",
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
