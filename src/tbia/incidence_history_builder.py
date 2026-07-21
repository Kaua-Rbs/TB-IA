from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tbia.domain.models import Territory
from tbia.incidence_history_fixture import (
    AGGREGATE_FILENAME,
    FIXTURE_END_YEAR,
    FIXTURE_ID,
    FIXTURE_INDICATOR_ID,
    FIXTURE_MINIMUM_COUNT,
    FIXTURE_START_YEAR,
    FIXTURE_UF,
    FIXTURE_UF_CODE,
    FIXTURE_YEARS,
    MANIFEST_FILENAME,
    sha256_bytes,
)
from tbia.ingest.datasus import (
    DatasusFile,
    download_datasus_file,
    read_datasus_records,
)
from tbia.ingest.datasus_transforms import (
    build_datasus_municipality_map,
    transform_sinan_tb_records,
)
from tbia.ingest.readers import fetch_json, read_ibge_municipalities
from tbia.pipeline import ibge_population_url, read_ibge_population_payload

DEFAULT_RESOURCE_OUTPUT_DIR = Path("src/tbia/resources/demo")
IBGE_MUNICIPALITIES_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/estados/23/municipios"
)


@dataclass(frozen=True)
class IncidenceHistoryBuildResult:
    aggregate_path: Path
    manifest_path: Path
    row_count: int
    territory_count: int
    aggregate_sha256: str


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def denominator_reference_year(analysis_year: int) -> int:
    return 2022 if analysis_year >= 2022 else analysis_year


def historical_sinan_file(year: int) -> DatasusFile:
    if year not in FIXTURE_YEARS:
        raise ValueError(f"year outside bundled fixture interval: {year}")
    release_dir = "FINAIS" if year <= 2019 else "PRELIM"
    release_label = "final" if year <= 2019 else "preliminary"
    return DatasusFile(
        source_id="sinan_tb",
        label=f"SINAN-TB Brazil {year} {release_label}",
        host="ftp.datasus.gov.br",
        remote_path=(f"dissemin/publicos/SINAN/DADOS/{release_dir}/TUBEBR{str(year)[-2:]}.dbc"),
        local_name=f"sinan_tb_br_{year}.dbc",
    )


def source_release_status(year: int) -> str:
    return "final" if year <= 2019 else "preliminary"


def build_fixture_row(
    territory: Territory,
    *,
    year: int,
    new_cases: int,
    population: int,
    population_source_year: int,
    population_source_kind: str,
) -> dict[str, object]:
    return {
        "territory_id": territory.territory_id,
        "territory_name": territory.name,
        "year": year,
        "new_cases": new_cases,
        "population": population,
        "population_source_year": population_source_year,
        "population_source_kind": population_source_kind,
    }


def generate_incidence_history_fixture(
    raw_dir: Path,
    output_dir: Path = DEFAULT_RESOURCE_OUTPUT_DIR,
    *,
    timeout: int = 60,
) -> IncidenceHistoryBuildResult:
    municipality_payload = fetch_json(IBGE_MUNICIPALITIES_URL, timeout=timeout)
    territories = read_ibge_municipalities(municipality_payload, FIXTURE_UF)
    if len(territories) != 184:
        raise ValueError(f"expected 184 Ceará municipalities, received {len(territories)}")
    municipality_map = build_datasus_municipality_map(territories)
    sample_dir = raw_dir / "datasus_samples"
    rows: list[dict[str, object]] = []
    source_artifacts: list[dict[str, object]] = []
    population_cache: dict[int, tuple[object, str, str]] = {}

    for year in FIXTURE_YEARS:
        sinan_file = historical_sinan_file(year)
        sinan_path = sample_dir / sinan_file.local_name
        if not sinan_path.exists():
            download_datasus_file(sinan_file, sample_dir, timeout=timeout)
        cases = transform_sinan_tb_records(
            read_datasus_records(sinan_path),
            municipality_map,
            year=year,
        )
        cases_by_territory = {case.territory_id: case for case in cases}
        population_year = denominator_reference_year(year)
        if population_year not in population_cache:
            population_url = ibge_population_url(FIXTURE_UF_CODE, population_year)
            population_payload = fetch_json(population_url, timeout=timeout)
            population_cache[population_year] = (
                population_payload,
                population_url,
                sha256_bytes(canonical_json_bytes(population_payload)),
            )
        population_payload, population_url, population_checksum = population_cache[population_year]
        populations = read_ibge_population_payload(
            population_payload,
            source_year=population_year,
            analysis_year=year,
        )
        populations_by_territory = {
            population.territory_id: population for population in populations
        }
        if set(populations_by_territory) != {item.territory_id for item in territories}:
            raise ValueError(f"IBGE population coverage is incomplete for analysis year {year}")

        for territory in territories:
            case = cases_by_territory.get(territory.territory_id)
            population = populations_by_territory[territory.territory_id]
            rows.append(
                build_fixture_row(
                    territory,
                    year=year,
                    new_cases=case.new_cases if case is not None else 0,
                    population=population.population,
                    population_source_year=population.source_year or population_year,
                    population_source_kind=population.source_kind,
                )
            )
        source_artifacts.extend(
            [
                {
                    "source_id": "sinan_tb",
                    "analysis_year": year,
                    "reference_year": year,
                    "release_status": source_release_status(year),
                    "dataset_kind": "notification",
                    "origin": sinan_file.ftp_url,
                    "sha256": sha256_bytes(sinan_path.read_bytes()),
                },
                {
                    "source_id": "ibge_population",
                    "analysis_year": year,
                    "reference_year": population_year,
                    "release_status": "final",
                    "dataset_kind": "census" if population_year == 2022 else "estimate",
                    "origin": population_url,
                    "sha256": population_checksum,
                    "checksum_basis": "canonical JSON payload",
                },
            ]
        )

    aggregate = {
        "schema_version": "1",
        "fixture_id": FIXTURE_ID,
        "indicator_id": FIXTURE_INDICATOR_ID,
        "minimum_count": FIXTURE_MINIMUM_COUNT,
        "scope": {
            "uf": FIXTURE_UF,
            "uf_code": FIXTURE_UF_CODE,
            "start_year": FIXTURE_START_YEAR,
            "end_year": FIXTURE_END_YEAR,
        },
        "rows": rows,
    }
    aggregate_content = pretty_json_bytes(aggregate)
    aggregate_checksum = sha256_bytes(aggregate_content)
    manifest = {
        "schema_version": "1",
        "fixture_id": FIXTURE_ID,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "review_status": "technical_fixture_pending_domain_review",
        "aggregate_file": AGGREGATE_FILENAME,
        "aggregate_sha256": aggregate_checksum,
        "row_count": len(rows),
        "territory_count": len(territories),
        "transformation": {
            "version": "cap02-incidence-v1",
            "numerator": "SINAN-TB new cases using TRATAMENTO codes 1, 4 and 6",
            "denominator_policy": (
                "Same-year IBGE estimates through 2021; 2022 Census population for "
                "analysis years 2022 and 2023 to match the reproducible MVP demo."
            ),
            "suppression": "Public values hidden when the numerator is below 5.",
        },
        "supporting_artifacts": [
            {
                "source_id": "ibge_localidades",
                "origin": IBGE_MUNICIPALITIES_URL,
                "sha256": sha256_bytes(canonical_json_bytes(municipality_payload)),
                "checksum_basis": "canonical JSON payload",
            }
        ],
        "source_artifacts": source_artifacts,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    aggregate_path = output_dir / AGGREGATE_FILENAME
    manifest_path = output_dir / MANIFEST_FILENAME
    aggregate_path.write_bytes(aggregate_content)
    manifest_path.write_bytes(pretty_json_bytes(manifest))
    return IncidenceHistoryBuildResult(
        aggregate_path=aggregate_path,
        manifest_path=manifest_path,
        row_count=len(rows),
        territory_count=len(territories),
        aggregate_sha256=aggregate_checksum,
    )
