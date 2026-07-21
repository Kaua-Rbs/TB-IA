from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from hashlib import sha256
from importlib.resources import files
from math import isclose
from pathlib import Path
from typing import Any, cast

from tbia.domain.indicators import case_indicator_values
from tbia.domain.models import CaseAggregate
from tbia.ingest.datasus_transforms import Record, transform_sinan_tb_records

DIAGNOSTIC_INDICATOR_FIELDS: dict[str, tuple[str, str]] = {
    "hiv_testing_proportion": ("hiv_tested_cases", "new_cases"),
    "trm_tb_use_proportion": ("trm_tb_cases", "new_pulmonary_cases"),
    "culture_use_among_retreatment": (
        "culture_retreated_cases",
        "retreatment_pulmonary_cases",
    ),
}


def load_sinan_acceptance_fixture(uf: str, year: int) -> dict[str, Any] | None:
    filename = f"sinan_diagnostic_acceptance_{uf.lower()}_{year}.json"
    resource = files("tbia").joinpath("resources", "validation", filename)
    if not resource.is_file():
        return None

    parsed = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"SINAN acceptance fixture must contain an object: {filename}")
    return cast(dict[str, Any], parsed)


def build_sinan_diagnostic_acceptance_report(
    records: Sequence[Record],
    fixture: Mapping[str, Any],
    *,
    source_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    scope = cast(Mapping[str, Any], fixture["scope"])
    expected_cases = cast(list[Mapping[str, Any]], fixture["cases"])
    minimum_count = int(fixture.get("minimum_count", 5))
    municipality_map = {
        str(case["territory_id"])[:6]: str(case["territory_id"]) for case in expected_cases
    }
    aggregates = transform_sinan_tb_records(
        records,
        municipality_map,
        year=int(scope["year"]),
    )
    aggregates_by_territory = {item.territory_id: item for item in aggregates}

    source_checks = build_source_checks(source_paths, fixture)
    differences = [
        f"source artifact mismatch: {item['filename']}"
        for item in source_checks
        if not item["matches_fixture"]
    ]
    checks: list[dict[str, Any]] = []
    for expected_case in expected_cases:
        case_checks, case_differences = build_case_checks(
            expected_case,
            aggregates_by_territory.get(str(expected_case["territory_id"])),
            minimum_count=minimum_count,
        )
        checks.extend(case_checks)
        differences.extend(case_differences)

    return {
        "status": "passed" if not differences else "failed",
        "review_status": fixture.get(
            "review_status",
            "technical_acceptance_pending_domain_review",
        ),
        "fixture_id": fixture["fixture_id"],
        "scope": dict(scope),
        "minimum_count": minimum_count,
        "source_artifacts": source_checks,
        "check_count": len(checks),
        "checks": checks,
        "differences": differences,
    }


def build_source_checks(
    source_paths: Sequence[Path],
    fixture: Mapping[str, Any],
) -> list[dict[str, Any]]:
    expected_artifacts = {
        str(item["filename"]): str(item["sha256"])
        for item in cast(list[Mapping[str, Any]], fixture.get("source_artifacts", []))
    }
    checks: list[dict[str, Any]] = []
    for path in source_paths:
        actual_hash = file_sha256(path)
        expected_hash = expected_artifacts.get(path.name)
        checks.append(
            {
                "filename": path.name,
                "sha256": actual_hash,
                "expected_sha256": expected_hash,
                "matches_fixture": expected_hash == actual_hash,
            }
        )
    return checks


def build_case_checks(
    expected_case: Mapping[str, Any],
    aggregate: CaseAggregate | None,
    *,
    minimum_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    territory_id = str(expected_case["territory_id"])
    expected_indicators = cast(
        Mapping[str, Mapping[str, Any]],
        expected_case["indicators"],
    )
    actual_values = (
        {
            value.indicator_id: value
            for value in case_indicator_values(
                aggregate, population=None, minimum_count=minimum_count
            )
        }
        if aggregate is not None
        else {}
    )

    checks: list[dict[str, Any]] = []
    differences: list[str] = []
    for indicator_id in DIAGNOSTIC_INDICATOR_FIELDS:
        expected = expected_indicators[indicator_id]
        value = actual_values.get(indicator_id)
        actual = actual_indicator_result(aggregate, value, indicator_id)
        mismatches = compare_indicator_result(expected, actual)
        checks.append(
            {
                "territory_id": territory_id,
                "territory_name": expected_case["territory_name"],
                "indicator_id": indicator_id,
                "status": "passed" if not mismatches else "failed",
                "expected": dict(expected),
                "actual": actual,
            }
        )
        differences.extend(f"{territory_id}/{indicator_id}: {field}" for field in mismatches)
    return checks, differences


def actual_indicator_result(
    aggregate: CaseAggregate | None,
    value: object,
    indicator_id: str,
) -> dict[str, Any]:
    if aggregate is None or value is None:
        return {
            "numerator": None,
            "denominator": None,
            "raw_value": None,
            "value": None,
            "is_suppressed": None,
        }

    numerator_field, denominator_field = DIAGNOSTIC_INDICATOR_FIELDS[indicator_id]
    numerator = int(getattr(aggregate, numerator_field))
    denominator = int(getattr(aggregate, denominator_field))
    indicator_value = cast(Any, value)
    raw_value = round(numerator / denominator * 100, 6) if denominator > 0 else None
    public_value = indicator_value.value
    return {
        "numerator": numerator,
        "denominator": denominator,
        "raw_value": raw_value,
        "value": round(float(public_value), 6) if public_value is not None else None,
        "is_suppressed": bool(indicator_value.is_suppressed),
    }


def compare_indicator_result(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> list[str]:
    mismatches: list[str] = []
    for field in ("numerator", "denominator", "is_suppressed"):
        if actual[field] != expected[field]:
            mismatches.append(field)
    for field in ("raw_value", "value"):
        if not optional_float_matches(expected[field], actual[field]):
            mismatches.append(field)
    return mismatches


def optional_float_matches(expected: float | int | None, actual: float | int | None) -> bool:
    if expected is None or actual is None:
        return expected is actual
    return isclose(float(expected), float(actual), abs_tol=1e-6)


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
