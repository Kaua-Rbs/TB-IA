from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from string import hexdigits
from typing import Any, cast

from sqlalchemy.orm import Session

from tbia.domain.indicators import INDICATOR_DEFINITIONS, build_value
from tbia.domain.models import IndicatorValue, SourceProvenance, Territory
from tbia.storage import (
    load_territories,
    save_indicator_definitions,
    save_indicator_history_values,
    save_territories,
)

FIXTURE_ID = "tb_incidence_history_ce_2018_2023_v1"
FIXTURE_UF = "CE"
FIXTURE_UF_CODE = "23"
FIXTURE_START_YEAR = 2018
FIXTURE_END_YEAR = 2023
FIXTURE_YEARS = tuple(range(FIXTURE_START_YEAR, FIXTURE_END_YEAR + 1))
FIXTURE_INDICATOR_ID = "tb_incidence_per_100k"
FIXTURE_MINIMUM_COUNT = 5
AGGREGATE_FILENAME = "incidence_history_ce_2018_2023.json"
MANIFEST_FILENAME = "incidence_history_ce_2018_2023.manifest.json"


@dataclass(frozen=True)
class IncidenceHistoryRow:
    territory_id: str
    territory_name: str
    year: int
    new_cases: int
    population: int
    population_source_year: int
    population_source_kind: str


@dataclass(frozen=True)
class HistorySourceArtifact:
    source_id: str
    analysis_year: int
    reference_year: int
    release_status: str
    dataset_kind: str
    origin: str
    sha256: str


@dataclass(frozen=True)
class IncidenceHistoryBundle:
    fixture_id: str
    minimum_count: int
    rows: tuple[IncidenceHistoryRow, ...]
    source_artifacts: tuple[HistorySourceArtifact, ...]
    aggregate_sha256: str

    @property
    def territory_count(self) -> int:
        return len({row.territory_id for row in self.rows})


@dataclass(frozen=True)
class IncidenceHistoryPreparationResult:
    fixture_id: str
    value_count: int
    territory_count: int
    start_year: int
    end_year: int
    aggregate_sha256: str


def sha256_bytes(content: bytes) -> str:
    return sha256(content).hexdigest()


def bundled_resource_bytes(filename: str) -> bytes:
    resource = files("tbia").joinpath("resources").joinpath("demo").joinpath(filename)
    return resource.read_bytes()


def fixture_bytes(path: Path | None, filename: str) -> bytes:
    return path.read_bytes() if path is not None else bundled_resource_bytes(filename)


def json_mapping(content: bytes, label: str) -> dict[str, Any]:
    payload = json.loads(content.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return cast(dict[str, Any], payload)


def required_string(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"fixture field {key} must be a non-empty string")
    return value


def required_int(row: Mapping[str, Any], key: str, *, minimum: int = 0) -> int:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"fixture field {key} must be an integer >= {minimum}")
    return value


def parse_history_row(raw: object) -> IncidenceHistoryRow:
    if not isinstance(raw, dict):
        raise ValueError("each incidence fixture row must be an object")
    row = cast(dict[str, Any], raw)
    return IncidenceHistoryRow(
        territory_id=required_string(row, "territory_id"),
        territory_name=required_string(row, "territory_name"),
        year=required_int(row, "year", minimum=2000),
        new_cases=required_int(row, "new_cases"),
        population=required_int(row, "population", minimum=1),
        population_source_year=required_int(row, "population_source_year", minimum=2000),
        population_source_kind=required_string(row, "population_source_kind"),
    )


def parse_source_artifact(raw: object) -> HistorySourceArtifact:
    if not isinstance(raw, dict):
        raise ValueError("each source artifact must be an object")
    row = cast(dict[str, Any], raw)
    checksum = required_string(row, "sha256")
    if len(checksum) != 64 or any(character not in hexdigits for character in checksum):
        raise ValueError("source artifact sha256 must contain 64 hexadecimal characters")
    return HistorySourceArtifact(
        source_id=required_string(row, "source_id"),
        analysis_year=required_int(row, "analysis_year", minimum=2000),
        reference_year=required_int(row, "reference_year", minimum=2000),
        release_status=required_string(row, "release_status"),
        dataset_kind=required_string(row, "dataset_kind"),
        origin=required_string(row, "origin"),
        sha256=checksum,
    )


def validate_fixture_coverage(
    rows: tuple[IncidenceHistoryRow, ...],
    *,
    expected_row_count: int,
    expected_territory_count: int,
) -> None:
    if len(rows) != expected_row_count:
        raise ValueError(
            f"incidence fixture row count mismatch: {len(rows)} != {expected_row_count}"
        )
    keys = {(row.territory_id, row.year) for row in rows}
    if len(keys) != len(rows):
        raise ValueError("incidence fixture contains duplicate municipality-year rows")
    rows_by_year: dict[int, set[str]] = defaultdict(set)
    names_by_territory: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        rows_by_year[row.year].add(row.territory_id)
        names_by_territory[row.territory_id].add(row.territory_name)
    if set(rows_by_year) != set(FIXTURE_YEARS):
        raise ValueError("incidence fixture does not cover the declared annual interval")
    expected_ids = rows_by_year[FIXTURE_START_YEAR]
    if len(expected_ids) != expected_territory_count:
        raise ValueError("incidence fixture municipality count does not match its manifest")
    if any(ids != expected_ids for ids in rows_by_year.values()):
        raise ValueError("incidence fixture municipality coverage changes between years")
    if any(len(names) != 1 for names in names_by_territory.values()):
        raise ValueError("incidence fixture municipality names change between years")


def validate_source_coverage(artifacts: tuple[HistorySourceArtifact, ...]) -> None:
    keys = {(artifact.source_id, artifact.analysis_year) for artifact in artifacts}
    expected = {
        (source_id, year) for source_id in ("sinan_tb", "ibge_population") for year in FIXTURE_YEARS
    }
    if keys != expected or len(keys) != len(artifacts):
        raise ValueError("source manifest must contain one SINAN and IBGE artifact per year")


def validate_fixture_scope(aggregate: Mapping[str, Any]) -> None:
    scope = aggregate.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("incidence fixture scope must be an object")
    expected_scope = {
        "uf": FIXTURE_UF,
        "uf_code": FIXTURE_UF_CODE,
        "start_year": FIXTURE_START_YEAR,
        "end_year": FIXTURE_END_YEAR,
    }
    if any(scope.get(key) != value for key, value in expected_scope.items()):
        raise ValueError("incidence fixture scope differs from the supported bundle")


def load_incidence_history_bundle(
    aggregate_path: Path | None = None,
    manifest_path: Path | None = None,
) -> IncidenceHistoryBundle:
    aggregate_content = fixture_bytes(aggregate_path, AGGREGATE_FILENAME)
    manifest_content = fixture_bytes(manifest_path, MANIFEST_FILENAME)
    aggregate = json_mapping(aggregate_content, "incidence aggregate")
    manifest = json_mapping(manifest_content, "incidence manifest")
    aggregate_checksum = sha256_bytes(aggregate_content)
    expected_checksum = required_string(manifest, "aggregate_sha256")
    if aggregate_checksum != expected_checksum:
        raise ValueError("incidence aggregate checksum does not match its manifest")
    if required_string(aggregate, "fixture_id") != FIXTURE_ID:
        raise ValueError("unsupported incidence fixture identifier")
    if required_string(manifest, "fixture_id") != FIXTURE_ID:
        raise ValueError("incidence manifest and loader identifiers differ")
    if required_string(aggregate, "indicator_id") != FIXTURE_INDICATOR_ID:
        raise ValueError("incidence fixture contains an unsupported indicator")
    validate_fixture_scope(aggregate)
    raw_rows = aggregate.get("rows")
    raw_artifacts = manifest.get("source_artifacts")
    if not isinstance(raw_rows, list) or not isinstance(raw_artifacts, list):
        raise ValueError("incidence fixture rows and source artifacts must be arrays")
    rows = tuple(parse_history_row(row) for row in raw_rows)
    artifacts = tuple(parse_source_artifact(row) for row in raw_artifacts)
    validate_fixture_coverage(
        rows,
        expected_row_count=required_int(manifest, "row_count", minimum=1),
        expected_territory_count=required_int(manifest, "territory_count", minimum=1),
    )
    validate_source_coverage(artifacts)
    minimum_count = required_int(aggregate, "minimum_count", minimum=1)
    if minimum_count != FIXTURE_MINIMUM_COUNT:
        raise ValueError("incidence fixture minimum-count policy changed unexpectedly")
    return IncidenceHistoryBundle(
        fixture_id=FIXTURE_ID,
        minimum_count=minimum_count,
        rows=rows,
        source_artifacts=artifacts,
        aggregate_sha256=aggregate_checksum,
    )


def incidence_history_values(bundle: IncidenceHistoryBundle) -> list[IndicatorValue]:
    artifacts = {
        (artifact.source_id, artifact.analysis_year): artifact
        for artifact in bundle.source_artifacts
    }
    return [build_incidence_value(row, artifacts, bundle.minimum_count) for row in bundle.rows]


def build_incidence_value(
    row: IncidenceHistoryRow,
    artifacts: Mapping[tuple[str, int], HistorySourceArtifact],
    minimum_count: int,
) -> IndicatorValue:
    event = artifacts[("sinan_tb", row.year)]
    population = artifacts[("ibge_population", row.year)]
    if event.reference_year != row.year:
        raise ValueError(f"SINAN provenance mismatch for {row.territory_id}/{row.year}")
    if (
        population.reference_year != row.population_source_year
        or population.dataset_kind != row.population_source_kind
    ):
        raise ValueError(f"population provenance mismatch for {row.territory_id}/{row.year}")
    return build_value(
        FIXTURE_INDICATOR_ID,
        row.territory_id,
        row.year,
        numerator=row.new_cases,
        denominator=row.population,
        source_ids=("sinan_tb", "ibge_population"),
        denominator_year=row.population_source_year,
        source_provenance=(
            SourceProvenance(
                "sinan_tb",
                reference_year=event.reference_year,
                release_status=event.release_status,
                dataset_kind=event.dataset_kind,
                artifact_sha256=event.sha256,
            ),
            SourceProvenance(
                "ibge_population",
                reference_year=population.reference_year,
                release_status=population.release_status,
                dataset_kind=population.dataset_kind,
                artifact_sha256=population.sha256,
            ),
        ),
        scale=100_000,
        minimum_count=minimum_count,
    )


def prepare_bundled_incidence_history(
    session: Session,
    *,
    aggregate_path: Path | None = None,
    manifest_path: Path | None = None,
) -> IncidenceHistoryPreparationResult:
    bundle = load_incidence_history_bundle(aggregate_path, manifest_path)
    save_indicator_definitions(session, INDICATOR_DEFINITIONS)
    existing_ids = {territory.territory_id for territory in load_territories(session, FIXTURE_UF)}
    fixture_territories = {
        row.territory_id: Territory(
            territory_id=row.territory_id,
            name=row.territory_name,
            territory_type="municipality",
            uf_code=FIXTURE_UF_CODE,
            uf_sigla=FIXTURE_UF,
        )
        for row in bundle.rows
    }
    save_territories(
        session,
        (
            territory
            for territory_id, territory in fixture_territories.items()
            if territory_id not in existing_ids
        ),
    )
    values = incidence_history_values(bundle)
    save_indicator_history_values(
        session,
        values,
        indicator_id=FIXTURE_INDICATOR_ID,
        start_year=FIXTURE_START_YEAR,
        end_year=FIXTURE_END_YEAR,
        replace_territory_ids=set(fixture_territories),
    )
    return IncidenceHistoryPreparationResult(
        fixture_id=bundle.fixture_id,
        value_count=len(values),
        territory_count=bundle.territory_count,
        start_year=FIXTURE_START_YEAR,
        end_year=FIXTURE_END_YEAR,
        aggregate_sha256=bundle.aggregate_sha256,
    )
