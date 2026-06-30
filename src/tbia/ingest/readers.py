from __future__ import annotations

import csv
import gzip
import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, TypeVar
from urllib.request import Request, urlopen

from tbia.domain.models import (
    CaseAggregate,
    Facility,
    HospitalizationAggregate,
    MortalityAggregate,
    PopulationDenominator,
    Territory,
)

T = TypeVar("T")


def fetch_json(url: str, *, timeout: int = 30) -> Any:
    request = Request(url, headers={"User-Agent": "TB-IA MVP1 public-data pipeline"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        if response.headers.get("Content-Encoding") == "gzip" or payload.startswith(b"\x1f\x8b"):
            payload = gzip.decompress(payload)
    return json.loads(payload.decode("utf-8"))


def read_csv_records(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def read_ibge_municipalities(payload: Iterable[dict[str, Any]], uf_sigla: str) -> list[Territory]:
    territories: list[Territory] = []
    for item in payload:
        code = str(item["id"])
        uf = item["microrregiao"]["mesorregiao"]["UF"]
        if uf["sigla"] != uf_sigla:
            continue
        territories.append(
            Territory(
                territory_id=code,
                name=str(item["nome"]),
                territory_type="municipality",
                uf_code=str(uf["id"]),
                uf_sigla=str(uf["sigla"]),
            )
        )
    return sorted(territories, key=lambda territory: territory.territory_id)


def read_ibge_malhas_municipality_geometries(
    payload: object,
    territories: Sequence[Territory],
) -> list[Territory]:
    if not isinstance(payload, dict):
        return []

    territory_by_id = {territory.territory_id: territory for territory in territories}
    matched: dict[str, Territory] = {}
    features = payload.get("features", [])
    if not isinstance(features, list):
        return []

    for feature in features:
        if not isinstance(feature, dict):
            continue
        municipality_code = ibge_malhas_feature_code(feature)
        if municipality_code is None:
            continue
        territory = territory_by_id.get(municipality_code)
        geometry = feature.get("geometry")
        if territory is None or not is_geojson_geometry(geometry):
            continue
        matched[municipality_code] = replace(territory, geometry=geometry)

    return sorted(matched.values(), key=lambda territory: territory.territory_id)


def ibge_malhas_feature_code(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties", {})
    raw_code: object | None = None
    if isinstance(properties, dict):
        raw_code = properties.get("codarea")
    if raw_code in (None, ""):
        raw_code = feature.get("id")
    if raw_code in (None, ""):
        return None
    code = str(raw_code).strip()
    return code or None


def is_geojson_geometry(value: object) -> bool:
    return isinstance(value, dict) and isinstance(value.get("type"), str)


def read_sidra_population_payload(
    payload: list[dict[str, Any]],
    year: int,
    source_id: str = "ibge_population",
) -> list[PopulationDenominator]:
    populations: list[PopulationDenominator] = []
    for variable in payload:
        for result in variable.get("resultados", []):
            for series in result.get("series", []):
                location = series.get("localidade", {})
                values = series.get("serie", {})
                raw_population = values.get(str(year))
                if raw_population in (None, "-", "..."):
                    continue
                populations.append(
                    PopulationDenominator(
                        territory_id=str(location["id"]),
                        year=year,
                        population=positive_int(str(raw_population), "population"),
                        source_id=source_id,
                    )
                )
    return sorted(populations, key=lambda population: population.territory_id)


def read_sidra_values_population_payload(
    payload: list[dict[str, str]],
    analysis_year: int,
    source_id: str = "ibge_population",
) -> list[PopulationDenominator]:
    populations: list[PopulationDenominator] = []
    for row in payload:
        raw_population = row.get("V")
        municipality_code = row.get("D1C")
        if raw_population is None or raw_population in ("-", "...", "Valor"):
            continue
        if not municipality_code:
            continue
        populations.append(
            PopulationDenominator(
                territory_id=municipality_code,
                year=analysis_year,
                population=positive_int(raw_population, "population"),
                source_id=source_id,
            )
        )
    return sorted(populations, key=lambda population: population.territory_id)


def read_population_csv(
    path: Path, source_id: str = "ibge_population"
) -> list[PopulationDenominator]:
    rows = read_csv_records(path)
    return collapse_by_key(
        rows,
        key_fields=("municipality_code", "year"),
        builder=lambda key, row: PopulationDenominator(
            territory_id=key[0],
            year=int(key[1]),
            population=positive_int(row["population"], "population"),
            source_id=source_id,
        ),
        merge=lambda existing, new: PopulationDenominator(
            territory_id=existing.territory_id,
            year=existing.year,
            population=new.population,
            source_id=source_id,
        ),
    )


def read_case_aggregates_csv(path: Path, source_id: str = "sinan_tb") -> list[CaseAggregate]:
    rows = read_csv_records(path)
    return collapse_by_key(
        rows,
        key_fields=("municipality_code", "year"),
        builder=lambda key, row: CaseAggregate(
            territory_id=key[0],
            year=int(key[1]),
            notified_cases=non_negative_int(row, "notified_cases"),
            new_cases=non_negative_int(row, "new_cases"),
            closed_cases=non_negative_int(row, "closed_cases"),
            cured_cases=non_negative_int(row, "cured_cases"),
            treatment_interruption_cases=non_negative_int(row, "treatment_interruption_cases"),
            retreatment_cases=non_negative_int(row, "retreatment_cases"),
            new_pulmonary_cases=non_negative_int(row, "new_pulmonary_cases"),
            lab_confirmed_pulmonary_cases=non_negative_int(row, "lab_confirmed_pulmonary_cases"),
            hiv_tested_cases=non_negative_int(row, "hiv_tested_cases"),
            tb_hiv_cases=non_negative_int(row, "tb_hiv_cases"),
            trm_tb_cases=non_negative_int(row, "trm_tb_cases"),
            retreatment_pulmonary_cases=non_negative_int(row, "retreatment_pulmonary_cases"),
            culture_retreated_cases=non_negative_int(row, "culture_retreated_cases"),
            source_id=source_id,
        ),
        merge=merge_case_aggregate,
    )


def read_mortality_aggregates_csv(path: Path, source_id: str = "sim") -> list[MortalityAggregate]:
    rows = read_csv_records(path)
    return collapse_by_key(
        rows,
        key_fields=("municipality_code", "year"),
        builder=lambda key, row: MortalityAggregate(
            territory_id=key[0],
            year=int(key[1]),
            tb_deaths=non_negative_int(row, "tb_deaths"),
            source_id=source_id,
        ),
        merge=lambda existing, new: MortalityAggregate(
            territory_id=existing.territory_id,
            year=existing.year,
            tb_deaths=existing.tb_deaths + new.tb_deaths,
            source_id=source_id,
        ),
    )


def read_hospitalization_aggregates_csv(
    path: Path,
    source_id: str = "sih_sus",
) -> list[HospitalizationAggregate]:
    rows = read_csv_records(path)
    return collapse_by_key(
        rows,
        key_fields=("municipality_code", "year"),
        builder=lambda key, row: HospitalizationAggregate(
            territory_id=key[0],
            year=int(key[1]),
            tb_admissions=non_negative_int(row, "tb_admissions"),
            source_id=source_id,
        ),
        merge=lambda existing, new: HospitalizationAggregate(
            territory_id=existing.territory_id,
            year=existing.year,
            tb_admissions=existing.tb_admissions + new.tb_admissions,
            source_id=source_id,
        ),
    )


def read_facilities_csv(path: Path, source_id: str = "cnes") -> list[Facility]:
    rows = read_csv_records(path)
    facilities: dict[str, Facility] = {}
    for row in rows:
        facility_id = required_text(row, "facility_id")
        facilities[facility_id] = Facility(
            facility_id=facility_id,
            territory_id=required_text(row, "municipality_code"),
            name=required_text(row, "name"),
            facility_type=required_text(row, "facility_type"),
            sus_linked=text_bool(row.get("sus_linked", "true")),
            source_id=source_id,
        )
    return sorted(facilities.values(), key=lambda facility: facility.facility_id)


def collapse_by_key(
    rows: Iterable[dict[str, str]],
    *,
    key_fields: tuple[str, ...],
    builder: Callable[[tuple[str, ...], dict[str, str]], T],
    merge: Callable[[T, T], T],
) -> list[T]:
    records: dict[tuple[str, ...], T] = {}
    for row in rows:
        key = tuple(required_text(row, field) for field in key_fields)
        item = builder(key, row)
        records[key] = merge(records[key], item) if key in records else item
    return list(records.values())


def merge_case_aggregate(existing: CaseAggregate, new: CaseAggregate) -> CaseAggregate:
    return CaseAggregate(
        territory_id=existing.territory_id,
        year=existing.year,
        notified_cases=existing.notified_cases + new.notified_cases,
        new_cases=existing.new_cases + new.new_cases,
        closed_cases=existing.closed_cases + new.closed_cases,
        cured_cases=existing.cured_cases + new.cured_cases,
        treatment_interruption_cases=(
            existing.treatment_interruption_cases + new.treatment_interruption_cases
        ),
        retreatment_cases=existing.retreatment_cases + new.retreatment_cases,
        new_pulmonary_cases=existing.new_pulmonary_cases + new.new_pulmonary_cases,
        lab_confirmed_pulmonary_cases=(
            existing.lab_confirmed_pulmonary_cases + new.lab_confirmed_pulmonary_cases
        ),
        hiv_tested_cases=existing.hiv_tested_cases + new.hiv_tested_cases,
        tb_hiv_cases=existing.tb_hiv_cases + new.tb_hiv_cases,
        trm_tb_cases=existing.trm_tb_cases + new.trm_tb_cases,
        retreatment_pulmonary_cases=(
            existing.retreatment_pulmonary_cases + new.retreatment_pulmonary_cases
        ),
        culture_retreated_cases=(existing.culture_retreated_cases + new.culture_retreated_cases),
        source_id=existing.source_id,
    )


def required_text(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"missing required field: {field}")
    return value


def non_negative_int(row: dict[str, str], field: str) -> int:
    raw_value = row.get(field, "").strip()
    if raw_value == "":
        return 0
    value = int(raw_value)
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def positive_int(raw_value: str, field: str) -> int:
    value = int(raw_value)
    if value <= 0:
        raise ValueError(f"{field} must be positive")
    return value


def text_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "sim", "s"}
