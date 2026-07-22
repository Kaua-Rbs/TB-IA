from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar, cast

from sqlalchemy.orm import Session

from tbia.domain.indicator_validation import (
    build_indicator_validation_report,
    write_indicator_validation_report,
)
from tbia.domain.indicators import INDICATOR_DEFINITIONS, compute_indicator_values
from tbia.domain.models import (
    ImportRun,
    IndicatorValue,
    PopulationDenominator,
    ScenarioRuleEvaluation,
    Territory,
    TerritoryScenario,
)
from tbia.domain.ranking_impact import (
    build_diagnostic_ranking_impact_report,
    write_diagnostic_ranking_impact_report,
)
from tbia.domain.recommendations import STRATEGIES, build_recommendations
from tbia.domain.resistance_surveillance_audit import (
    build_resistance_surveillance_audit,
    write_resistance_surveillance_audit,
)
from tbia.domain.scenarios import DEFAULT_SCENARIO_RULES, evaluate_territory_scenarios
from tbia.geography import BRAZIL_SCOPE, is_brazil_scope, uf_code_for, ufs_for_scope
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
    read_ibge_malhas_municipality_geometries,
    read_ibge_municipalities,
    read_mortality_aggregates_csv,
    read_population_csv,
    read_public_subterritory_geojson,
    read_sidra_population_payload,
    read_sidra_values_population_payload,
)
from tbia.ingest.sinan_acceptance import (
    build_sinan_diagnostic_acceptance_report,
    load_sinan_acceptance_fixture,
)
from tbia.ingest.sinan_validation import (
    build_sinan_mapping_report,
    write_sinan_mapping_report,
)
from tbia.storage import (
    COMPARISON_SCOPE_NATIONAL,
    COMPARISON_SCOPE_UF,
    SIH_EXPECTED_MONTHS,
    complete_sih_scopes,
    load_cases,
    load_hospitalizations,
    load_indicator_values,
    load_mortalities,
    load_populations,
    load_territories,
    load_territory_scenarios,
    resistance_surveillance_profile_for_territory,
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
    save_scenario_rule_evaluations,
    save_scenario_rules,
    save_strategies,
    save_territories,
    save_territory_scenarios,
)

HOSPITALIZATION_INDICATOR_ID = "hospitalization_burden_per_100k"

T = TypeVar("T")
DEFAULT_CENSUS_POPULATION_YEAR = 2022


@dataclass(frozen=True)
class Mvp1Config:
    uf: str = "CE"
    uf_code: str = ""
    year: int = 2023
    raw_dir: Path = Path("data/raw/public_sources")
    processed_dir: Path = Path("data/processed/mvp1")
    minimum_count: int = 5
    population_source_year: int | None = None
    sinan_acceptance_enabled: bool = True

    def __post_init__(self) -> None:
        normalized_uf = self.uf.upper()
        object.__setattr__(self, "uf", normalized_uf)
        if not self.uf_code:
            object.__setattr__(self, "uf_code", uf_code_for(normalized_uf))

    @property
    def is_national(self) -> bool:
        return is_brazil_scope(self.uf)

    def for_uf(self, uf: str) -> Mvp1Config:
        return replace(self, uf=uf, uf_code=uf_code_for(uf))

    @property
    def manual_dir(self) -> Path:
        return self.raw_dir / "manual"

    @property
    def datasus_sample_dir(self) -> Path:
        return self.raw_dir / "datasus_samples"

    @property
    def validation_dir(self) -> Path:
        return self.processed_dir / "validation"

    @property
    def ibge_malhas_dir(self) -> Path:
        return self.raw_dir / "ibge_malhas"

    def ibge_malhas_geojson(self) -> Path:
        return self.ibge_malhas_dir / f"{self.uf.lower()}_{self.uf_code}_municipios.geojson"

    @property
    def ibge_intramunicipal_dir(self) -> Path:
        return self.raw_dir / "ibge_intramunicipal"

    def manual_csv(self, filename: str) -> Path:
        return self.manual_dir / filename


def public_import_run(
    config: Mvp1Config,
    *,
    source_id: str,
    status: str,
    started_at: datetime,
    finished_at: datetime | None = None,
    row_count: int = 0,
    message: str = "",
    loaded_months: tuple[int, ...] | None = None,
) -> ImportRun:
    return ImportRun(
        source_id=source_id,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        row_count=row_count,
        message=message,
        year=config.year,
        geographic_scope=config.uf,
        loaded_months=loaded_months,
    )


def seed_reference_data(session: Session) -> None:
    save_data_sources(session, (contract.as_data_source() for contract in SOURCE_CONTRACTS))
    save_indicator_definitions(session, INDICATOR_DEFINITIONS)
    save_scenario_rules(session, DEFAULT_SCENARIO_RULES)
    save_strategies(session, STRATEGIES)


def ingest_public_data(session: Session, config: Mvp1Config) -> None:
    seed_reference_data(session)
    if config.is_national:
        ingest_brazil_public_data(session, config)
        return
    ingest_single_uf_public_data(session, config)


def ingest_brazil_public_data(session: Session, config: Mvp1Config) -> None:
    uf_configs = [config.for_uf(uf) for uf in ufs_for_scope(BRAZIL_SCOPE)]
    for uf_config in uf_configs:
        ingest_ibge_territories(session, uf_config)
        ingest_ibge_malhas_geometries(session, uf_config)

    ingest_public_subterritory_geometries(session, config)
    loaded_sources: set[str] = set()
    population_loaded = False
    for uf_config in uf_configs:
        population_loaded = ingest_ibge_population(session, uf_config) or population_loaded
    if population_loaded:
        loaded_sources.add("ibge_population")
    loaded_sources.update(ingest_datasus_public_samples(session, config))
    record_sinan_validation_report(session, config)
    ingest_optional_csv_sources(session, config, skip_sources=loaded_sources)


def ingest_single_uf_public_data(session: Session, config: Mvp1Config) -> None:
    ingest_ibge_territories(session, config)
    ingest_ibge_malhas_geometries(session, config)
    ingest_public_subterritory_geometries(session, config)
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
        territories = preserve_existing_geometries(
            read_ibge_municipalities(payload, config.uf),
            load_territories(session, config.uf),
        )
        save_territories(session, territories)
        save_import_run(
            session,
            public_import_run(
                config,
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
            public_import_run(
                config,
                source_id="ibge_localidades",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=str(exc),
            ),
        )


def ingest_ibge_malhas_geometries(session: Session, config: Mvp1Config) -> None:
    started_at = datetime.now(UTC)
    territories = load_territories(session, config.uf)
    if not territories:
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="ibge_malhas",
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message="no territories available for geometry matching",
            ),
        )
        return

    url = ibge_malhas_url(config.uf_code)
    cache_path = config.ibge_malhas_geojson()
    try:
        payload = fetch_json(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        territories_with_geometry = read_ibge_malhas_municipality_geometries(payload, territories)
        save_territories(session, territories_with_geometry)
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="ibge_malhas",
                status="success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=len(territories_with_geometry),
                message=f"{url}; cached raw GeoJSON at {cache_path}",
            ),
        )
    except Exception as exc:
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="ibge_malhas",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"{url}: {exc}",
            ),
        )


def ingest_public_subterritory_geometries(session: Session, config: Mvp1Config) -> None:
    started_at = datetime.now(UTC)
    paths = tuple(sorted(config.ibge_intramunicipal_dir.glob("*.geojson")))
    if not paths:
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="ibge_intramunicipal",
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"normalized public GeoJSON not found: {config.ibge_intramunicipal_dir}",
            ),
        )
        return

    try:
        parent_ids = {territory.territory_id for territory in load_territories(session, config.uf)}
        territories = [
            territory
            for path in paths
            for territory in read_public_subterritory_geojson(
                json.loads(path.read_text(encoding="utf-8")), parent_ids
            )
        ]
        save_territories(session, territories)
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="ibge_intramunicipal",
                status="success" if territories else "skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=len(territories),
                message=public_subterritory_import_message(paths, len(territories)),
            ),
        )
    except Exception as exc:
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="ibge_intramunicipal",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"{config.ibge_intramunicipal_dir}: {exc}",
            ),
        )


def public_subterritory_import_message(paths: Sequence[Path], row_count: int) -> str:
    path_message = ", ".join(str(path) for path in paths)
    if row_count == 0:
        return f"no valid neighborhood_reference polygon features in {path_message}"
    return f"loaded normalized public reference GeoJSON: {path_message}"


def ibge_malhas_url(uf_code: str) -> str:
    return (
        f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{uf_code}"
        "?intrarregiao=municipio"
        "&formato=application/vnd.geo+json"
        "&qualidade=minima"
    )


def preserve_existing_geometries(
    territories: Sequence[Territory],
    existing_territories: Sequence[Territory],
) -> list[Territory]:
    geometry_by_id = {
        territory.territory_id: territory.geometry
        for territory in existing_territories
        if territory.geometry is not None
    }
    return [
        replace(territory, geometry=geometry_by_id[territory.territory_id])
        if territory.territory_id in geometry_by_id
        else territory
        for territory in territories
    ]


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
            public_import_run(
                config,
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
            public_import_run(
                config,
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
        public_import_run(
            config,
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
            source_year=source_year,
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
            source_year=population.source_year,
            source_kind=population.source_kind,
        )
        for population in populations
    ]


def ingest_datasus_public_samples(session: Session, config: Mvp1Config) -> set[str]:
    if config.is_national:
        return ingest_brazil_datasus_public_samples(session, config)
    return ingest_uf_datasus_public_samples(session, config)


def ingest_brazil_datasus_public_samples(session: Session, config: Mvp1Config) -> set[str]:
    territories = load_territories(session, BRAZIL_SCOPE)
    if not territories:
        return set()

    loaded_sources: set[str] = set()
    target_ids = {territory.territory_id for territory in territories}
    municipality_map = build_datasus_municipality_map(territories)
    if load_datasus_source(
        session,
        config,
        source_id="sinan_tb",
        paths=datasus_source_candidates(config, "sinan_tb"),
        transform=lambda records: transform_sinan_tb_records(
            records,
            municipality_map,
            year=config.year,
        ),
        saver=lambda active_session, rows: save_case_aggregates(
            active_session, rows, replace_territory_ids=target_ids
        ),
    ):
        loaded_sources.add("sinan_tb")

    for uf in ufs_for_scope(BRAZIL_SCOPE):
        uf_loaded_sources = ingest_uf_regional_datasus_public_samples(session, config.for_uf(uf))
        loaded_sources.update(uf_loaded_sources)
    return loaded_sources


def ingest_uf_regional_datasus_public_samples(session: Session, config: Mvp1Config) -> set[str]:
    territories = load_territories(session, config.uf)
    if not territories:
        return set()
    municipality_map = build_datasus_municipality_map(territories)
    target_ids = {territory.territory_id for territory in territories}
    loaded_sources: set[str] = set()

    if load_datasus_source(
        session,
        config,
        source_id="sim",
        paths=datasus_source_candidates(config, "sim"),
        transform=lambda records: transform_sim_records(
            records, municipality_map, year=config.year
        ),
        saver=lambda active_session, rows: save_mortalities(
            active_session, rows, replace_territory_ids=target_ids
        ),
    ):
        loaded_sources.add("sim")

    if load_datasus_source(
        session,
        config,
        source_id="sih_sus",
        track_month_coverage=True,
        paths=datasus_source_candidates(config, "sih_sus"),
        transform=lambda records: transform_sih_records(
            records, municipality_map, year=config.year
        ),
        saver=lambda active_session, rows: save_hospitalizations(
            active_session, rows, replace_territory_ids=target_ids
        ),
    ):
        loaded_sources.add("sih_sus")

    if load_datasus_source(
        session,
        config,
        source_id="cnes",
        paths=datasus_source_candidates(config, "cnes"),
        transform=lambda records: transform_cnes_records(records, municipality_map),
        saver=save_facilities,
    ):
        loaded_sources.add("cnes")
    return loaded_sources


def ingest_uf_datasus_public_samples(session: Session, config: Mvp1Config) -> set[str]:
    territories = load_territories(session, config.uf)
    if not territories:
        return set()
    municipality_map = build_datasus_municipality_map(territories)
    target_ids = {territory.territory_id for territory in territories}
    loaded_sources: set[str] = set()

    if load_datasus_source(
        session,
        config,
        source_id="sinan_tb",
        paths=datasus_source_candidates(config, "sinan_tb"),
        transform=lambda records: transform_sinan_tb_records(
            records,
            municipality_map,
            year=config.year,
        ),
        saver=lambda active_session, rows: save_case_aggregates(
            active_session, rows, replace_territory_ids=target_ids
        ),
    ):
        loaded_sources.add("sinan_tb")

    if load_datasus_source(
        session,
        config,
        source_id="sim",
        paths=datasus_source_candidates(config, "sim"),
        transform=lambda records: transform_sim_records(
            records, municipality_map, year=config.year
        ),
        saver=lambda active_session, rows: save_mortalities(
            active_session, rows, replace_territory_ids=target_ids
        ),
    ):
        loaded_sources.add("sim")

    if load_datasus_source(
        session,
        config,
        source_id="sih_sus",
        track_month_coverage=True,
        paths=datasus_source_candidates(config, "sih_sus"),
        transform=lambda records: transform_sih_records(
            records, municipality_map, year=config.year
        ),
        saver=lambda active_session, rows: save_hospitalizations(
            active_session, rows, replace_territory_ids=target_ids
        ),
    ):
        loaded_sources.add("sih_sus")

    if load_datasus_source(
        session,
        config,
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


def sih_month_for_path(path: Path, config: Mvp1Config) -> int:
    prefix = f"sih_{config.uf.lower()}_{config.year}_"
    if not path.stem.startswith(prefix):
        raise ValueError(f"unexpected SIH/SUS filename for {config.uf}/{config.year}: {path.name}")
    month_text = path.stem.removeprefix(prefix)
    if not month_text.isdigit() or int(month_text) not in SIH_EXPECTED_MONTHS:
        raise ValueError(f"invalid SIH/SUS month in filename: {path.name}")
    return int(month_text)


def load_datasus_source(
    session: Session,
    config: Mvp1Config,
    *,
    source_id: str,
    paths: Sequence[Path],
    transform: Callable[[Sequence[dict[str, object]]], Sequence[T]],
    saver: Callable[[Session, Sequence[T]], None],
    track_month_coverage: bool = False,
) -> bool:
    started_at = datetime.now(UTC)
    existing_paths = select_existing_datasus_paths(paths)
    loaded_months: list[int] | None = [] if track_month_coverage else None
    if not existing_paths:
        save_import_run(
            session,
            public_import_run(
                config,
                source_id=source_id,
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message="DATASUS public sample file not found",
                loaded_months=() if loaded_months is not None else None,
            ),
        )
        return False

    try:
        records: list[dict[str, object]] = []
        for path in existing_paths:
            records.extend(read_datasus_records(path))
            if loaded_months is not None:
                loaded_months.append(sih_month_for_path(path, config))
        recorded_months = tuple(sorted(set(loaded_months))) if loaded_months is not None else None
        rows = transform(records)
        if not rows:
            save_import_run(
                session,
                public_import_run(
                    config,
                    source_id=source_id,
                    status="skipped",
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    message=(
                        f"no canonical rows produced from {datasus_path_message(existing_paths)}"
                    ),
                    loaded_months=recorded_months,
                ),
            )
            return False

        saver(session, rows)
        complete_coverage = recorded_months is None or recorded_months == SIH_EXPECTED_MONTHS
        status = "success" if complete_coverage else "partial"
        message = f"loaded DATASUS public sample: {datasus_path_message(existing_paths)}"
        if recorded_months is not None and not complete_coverage:
            missing_months = sorted(set(SIH_EXPECTED_MONTHS) - set(recorded_months))
            missing_text = ",".join(f"{month:02d}" for month in missing_months)
            message = (
                f"loaded {len(recorded_months)}/12 SIH/SUS months; "
                f"annual hospitalization indicators excluded; missing {missing_text}: "
                f"{datasus_path_message(existing_paths)}"
            )
        save_import_run(
            session,
            public_import_run(
                config,
                source_id=source_id,
                status=status,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=len(rows),
                message=message,
                loaded_months=recorded_months,
            ),
        )
        return True
    except Exception as exc:
        recorded_months = tuple(sorted(set(loaded_months))) if loaded_months is not None else None
        save_import_run(
            session,
            public_import_run(
                config,
                source_id=source_id,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=f"{datasus_path_message(existing_paths)}: {exc}",
                loaded_months=recorded_months,
            ),
        )
        return False


def datasus_path_message(paths: Sequence[Path]) -> str:
    return ", ".join(str(path) for path in paths)


def build_sinan_validation_report_file(config: Mvp1Config) -> tuple[Path, int, str]:
    paths = select_existing_datasus_paths(datasus_source_candidates(config, "sinan_tb"))
    if not paths:
        raise FileNotFoundError("SINAN-TB DATASUS public sample file not found")

    records = [record for path in paths for record in read_datasus_records(path)]
    report = build_sinan_mapping_report(records, year=config.year, uf_code=config.uf_code)
    acceptance: dict[str, Any] = {"status": "disabled"}
    if config.sinan_acceptance_enabled:
        fixture = load_sinan_acceptance_fixture(config.uf, config.year)
        if fixture is None:
            acceptance = {"status": "not_configured"}
        else:
            acceptance = build_sinan_diagnostic_acceptance_report(
                records,
                fixture,
                source_paths=paths,
            )
    report["diagnostic_acceptance"] = acceptance
    output_path = write_sinan_mapping_report(report, config.validation_dir)
    return output_path, int(report["record_count"]), str(acceptance["status"])


def record_sinan_validation_report(session: Session, config: Mvp1Config) -> None:
    started_at = datetime.now(UTC)
    try:
        output_path, row_count, acceptance_status = build_sinan_validation_report_file(config)
    except FileNotFoundError as exc:
        save_import_run(
            session,
            public_import_run(
                config,
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
            public_import_run(
                config,
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
            public_import_run(
                config,
                source_id="sinan_validation",
                status="failed" if acceptance_status == "failed" else "success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=row_count,
                message=(
                    f"technical audit pending domain review; diagnostic acceptance "
                    f"{acceptance_status}: {output_path}"
                ),
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
            public_import_run(
                config,
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
    coverage_unknown = source_id == "sih_sus"
    status = "partial" if coverage_unknown else "success"
    message = f"loaded manual CSV fallback: {path}"
    if coverage_unknown:
        message = (
            "loaded manual SIH/SUS aggregates with unknown monthly coverage; "
            f"annual hospitalization indicators excluded: {path}"
        )
    save_import_run(
        session,
        public_import_run(
            config,
            source_id=source_id,
            status=status,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=len(rows),
            message=message,
        ),
    )


def compute_and_store_indicators(session: Session, config: Mvp1Config) -> int:
    territory_ids = target_municipality_ids(session, config)
    hospitalization_territory_ids = complete_hospitalization_territory_ids(session, config)
    values = compute_indicator_values(
        filter_public_rows(load_populations(session, config.year), territory_ids),
        filter_public_rows(load_cases(session, config.year), territory_ids),
        filter_public_rows(load_mortalities(session, config.year), territory_ids),
        filter_public_rows(
            load_hospitalizations(session, config.year),
            hospitalization_territory_ids,
        ),
        year=config.year,
        minimum_count=config.minimum_count,
    )
    save_indicator_values(session, values, config.year, replace_territory_ids=territory_ids)
    record_indicator_validation_report(session, config, values)
    return len(values)


def target_municipality_ids(session: Session, config: Mvp1Config) -> set[str]:
    return {territory.territory_id for territory in load_territories(session, config.uf)}


def complete_hospitalization_territory_ids(
    session: Session,
    config: Mvp1Config,
) -> set[str]:
    complete_scopes = complete_sih_scopes(
        session,
        year=config.year,
        geographic_scopes=ufs_for_scope(config.uf),
    )
    return {
        territory.territory_id
        for territory in load_territories(session, config.uf)
        if territory.uf_sigla in complete_scopes
    }


def exclude_hospitalization_values(
    values: Sequence[IndicatorValue],
) -> list[IndicatorValue]:
    return [value for value in values if value.indicator_id != HOSPITALIZATION_INDICATOR_ID]


def filter_public_rows(rows: Sequence[T], territory_ids: set[str]) -> list[T]:
    return [row for row in rows if cast(Any, row).territory_id in territory_ids]


def record_indicator_validation_report(
    session: Session,
    config: Mvp1Config,
    values: Sequence[IndicatorValue],
) -> None:
    started_at = datetime.now(UTC)
    try:
        report = build_indicator_validation_report(
            values, year=config.year, geographic_scope=config.uf
        )
        output_path = write_indicator_validation_report(report, config.validation_dir)
    except Exception as exc:
        save_import_run(
            session,
            public_import_run(
                config,
                source_id="indicator_validation",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                message=str(exc),
            ),
        )
        return

    violation_count = int(report["violation_count"])
    warning_count = int(report.get("warning_count", 0))
    message = f"indicator sanity report: {output_path}"
    if violation_count:
        message = f"{message}; {violation_count} invariant violation(s) found"
    if warning_count:
        message = f"{message}; {warning_count} warning(s) found"
    save_import_run(
        session,
        public_import_run(
            config,
            source_id="indicator_validation",
            status=str(report["status"]),
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=int(report["indicator_count"]),
            message=message,
        ),
    )


def diagnostic_comparison_scopes(config: Mvp1Config) -> tuple[str, ...]:
    if config.is_national:
        return COMPARISON_SCOPE_UF, COMPARISON_SCOPE_NATIONAL
    return (COMPARISON_SCOPE_UF,)


def generate_diagnostic_ranking_impact_report(
    session: Session,
    config: Mvp1Config,
    *,
    scenarios: Sequence[TerritoryScenario] | None = None,
) -> Path:
    territory_ids = target_municipality_ids(session, config)
    scenario_records = (
        list(scenarios)
        if scenarios is not None
        else [
            scenario
            for comparison_scope in diagnostic_comparison_scopes(config)
            for scenario in load_territory_scenarios(
                session,
                config.year,
                comparison_scope,
            )
        ]
    )
    scoped_scenarios = [
        scenario for scenario in scenario_records if scenario.territory_id in territory_ids
    ]
    territory_names = {
        territory.territory_id: territory.name
        for territory in load_territories(session, config.uf)
        if territory.territory_id in territory_ids
    }
    report = build_diagnostic_ranking_impact_report(
        scoped_scenarios,
        territory_names,
        year=config.year,
        geographic_scope=config.uf,
        comparison_scopes=diagnostic_comparison_scopes(config),
    )
    return write_diagnostic_ranking_impact_report(report, config.validation_dir)


def generate_resistance_surveillance_audit_report(
    session: Session,
    config: Mvp1Config,
    output_dir: Path | None = None,
) -> Path:
    territory_ids = target_municipality_ids(session, config)
    territories = {
        territory.territory_id: territory
        for territory in load_territories(session, config.uf)
        if territory.territory_id in territory_ids
    }
    profiles_by_scope: dict[str, dict[str, dict[str, Any]]] = {}
    for comparison_scope in diagnostic_comparison_scopes(config):
        triggered_by_territory: dict[str, set[str]] = {}
        for scenario in load_territory_scenarios(
            session,
            config.year,
            comparison_scope,
        ):
            if scenario.territory_id in territory_ids:
                triggered_by_territory.setdefault(scenario.territory_id, set()).add(
                    scenario.rule_id
                )
        profiles_by_scope[comparison_scope] = {
            territory_id: resistance_surveillance_profile_for_territory(
                session,
                territory_id=territory_id,
                territory_uf=territory.uf_sigla,
                year=config.year,
                comparison_scope=comparison_scope,
                triggered_rule_ids=triggered_by_territory.get(territory_id, set()),
            )
            for territory_id, territory in sorted(territories.items())
        }

    report = build_resistance_surveillance_audit(
        profiles_by_scope,
        sorted(territory_ids),
        year=config.year,
        geographic_scope=config.uf,
    )
    return write_resistance_surveillance_audit(report, output_dir or config.validation_dir)


def build_and_store_scenarios(session: Session, config: Mvp1Config) -> tuple[int, int]:
    territory_ids = target_municipality_ids(session, config)
    if not territory_ids:
        return 0, 0

    scenarios: list[TerritoryScenario] = []
    recommendations: list[Any] = []
    uf_scenarios, uf_evaluations = build_uf_scope_scenarios(session, config, territory_ids)
    uf_recommendations = build_recommendations(uf_scenarios)
    save_territory_scenarios(
        session,
        uf_scenarios,
        config.year,
        comparison_scope=COMPARISON_SCOPE_UF,
        replace_territory_ids=territory_ids,
    )
    save_recommendations(
        session,
        uf_recommendations,
        config.year,
        comparison_scope=COMPARISON_SCOPE_UF,
        replace_territory_ids=territory_ids,
    )
    save_scenario_rule_evaluations(
        session,
        uf_evaluations,
        config.year,
        COMPARISON_SCOPE_UF,
        replace_geographic_scopes=ufs_for_scope(config.uf),
    )
    scenarios.extend(uf_scenarios)
    recommendations.extend(uf_recommendations)

    if config.is_national:
        national_values = load_indicator_values(session, config.year, territory_ids)
        expected_scopes = set(ufs_for_scope(BRAZIL_SCOPE))
        nationally_complete_sih = complete_sih_scopes(
            session,
            year=config.year,
            geographic_scopes=expected_scopes,
        )
        if nationally_complete_sih != expected_scopes:
            national_values = exclude_hospitalization_values(national_values)
        national_result = evaluate_territory_scenarios(
            national_values,
            comparison_scope=COMPARISON_SCOPE_NATIONAL,
            geographic_scope=BRAZIL_SCOPE,
            year=config.year,
            territory_ids=territory_ids,
        )
        national_scenarios = list(national_result.scenarios)
        national_recommendations = build_recommendations(national_scenarios)
        save_territory_scenarios(
            session,
            national_scenarios,
            config.year,
            comparison_scope=COMPARISON_SCOPE_NATIONAL,
            replace_territory_ids=territory_ids,
        )
        save_recommendations(
            session,
            national_recommendations,
            config.year,
            comparison_scope=COMPARISON_SCOPE_NATIONAL,
            replace_territory_ids=territory_ids,
        )
        save_scenario_rule_evaluations(
            session,
            national_result.evaluations,
            config.year,
            COMPARISON_SCOPE_NATIONAL,
            replace_geographic_scopes={BRAZIL_SCOPE},
        )
        scenarios.extend(national_scenarios)
        recommendations.extend(national_recommendations)

    generate_diagnostic_ranking_impact_report(session, config, scenarios=scenarios)
    generate_resistance_surveillance_audit_report(session, config)
    return len(scenarios), len(recommendations)


def build_uf_scope_scenarios(
    session: Session, config: Mvp1Config, territory_ids: set[str]
) -> tuple[list[TerritoryScenario], list[ScenarioRuleEvaluation]]:
    complete_scopes = complete_sih_scopes(
        session,
        year=config.year,
        geographic_scopes=ufs_for_scope(config.uf),
    )
    scenarios: list[TerritoryScenario] = []
    evaluations: list[ScenarioRuleEvaluation] = []
    if not config.is_national:
        values = load_indicator_values(session, config.year, territory_ids)
        if config.uf not in complete_scopes:
            values = exclude_hospitalization_values(values)
        result = evaluate_territory_scenarios(
            values,
            comparison_scope=COMPARISON_SCOPE_UF,
            geographic_scope=config.uf,
            year=config.year,
            territory_ids=territory_ids,
        )
        return list(result.scenarios), list(result.evaluations)

    territories_by_uf: dict[str, set[str]] = {}
    for territory in load_territories(session, BRAZIL_SCOPE):
        if territory.territory_id in territory_ids:
            territories_by_uf.setdefault(territory.uf_sigla, set()).add(territory.territory_id)
    for uf, uf_territory_ids in territories_by_uf.items():
        values = load_indicator_values(session, config.year, uf_territory_ids)
        if uf not in complete_scopes:
            values = exclude_hospitalization_values(values)
        result = evaluate_territory_scenarios(
            values,
            comparison_scope=COMPARISON_SCOPE_UF,
            geographic_scope=uf,
            year=config.year,
            territory_ids=uf_territory_ids,
        )
        scenarios.extend(result.scenarios)
        evaluations.extend(result.evaluations)
    return scenarios, evaluations
