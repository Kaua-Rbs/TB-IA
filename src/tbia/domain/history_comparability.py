from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tbia.domain.history import (
    HistoryPointStatus,
    IndicatorHistory,
    IndicatorHistoryPoint,
)

REPORT_STATUS_PENDING_DOMAIN_REVIEW = "technical_comparability_ready_pending_domain_review"
STRUCTURAL_FLAG_CODES = frozenset(
    {
        "denominator_year_mismatch",
        "source_release_changed",
        "denominator_method_changed",
    }
)


def build_history_comparability_report(
    histories: Iterable[IndicatorHistory],
    territory_names: Mapping[str, str],
    *,
    geographic_scope: str,
    headline_territory_ids: Sequence[str] = (),
    source_bundle_sha256: str | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    records = validate_histories(histories)
    first = records[0]
    municipality_rows = [
        municipality_comparability_row(history, territory_names) for history in records
    ]
    annual_rows = [
        annual_coverage_row(records, year) for year in range(first.start_year, first.end_year + 1)
    ]
    flag_rows = comparability_flag_rows(records)
    candidate_rows = [row for row in municipality_rows if row["candidate_for_domain_comparison"]]
    headline_ids = set(headline_territory_ids)
    timestamp = generated_at or datetime.now(UTC)
    return {
        "status": REPORT_STATUS_PENDING_DOMAIN_REVIEW,
        "generated_at": timestamp.isoformat(),
        "scope": {
            "geographic_scope": geographic_scope,
            "indicator_id": first.indicator_id,
            "start_year": first.start_year,
            "end_year": first.end_year,
        },
        "source_bundle_sha256": source_bundle_sha256,
        "summary": {
            "territory_count": len(records),
            "expected_point_count": len(records) * first.coverage.requested_year_count,
            "available_point_count": sum(
                history.coverage.available_year_count for history in records
            ),
            "suppressed_point_count": sum(
                history.coverage.suppressed_year_count for history in records
            ),
            "missing_point_count": sum(history.coverage.missing_year_count for history in records),
            "provenance_incomplete_point_count": sum(
                history.coverage.provenance_incomplete_year_count for history in records
            ),
            "complete_series_territory_count": sum(
                history.coverage.available_year_count == history.coverage.requested_year_count
                for history in records
            ),
            "candidate_for_domain_comparison_count": len(candidate_rows),
        },
        "candidate_definition": (
            "All requested years are available and provenance is complete. Known "
            "scope-wide source-release and denominator transitions remain explicit "
            "and still require domain acceptance."
        ),
        "annual_coverage": annual_rows,
        "comparability_flags": flag_rows,
        "shared_structural_flags": [
            row
            for row in flag_rows
            if row["code"] in STRUCTURAL_FLAG_CODES
            and row["territory_count"] == len(records)
            and len(row["patterns"]) == 1
        ],
        "headline_municipalities": [
            row for row in municipality_rows if row["territory_id"] in headline_ids
        ],
        "municipalities": municipality_rows,
        "caveats": [
            "Candidate status is a technical completeness screen, not epidemiological approval.",
            "Suppressed annual values are never replaced by zero or interpolation.",
            "Release and denominator changes are reported, not statistically corrected.",
            "No trend, prediction, hotspot, severity, or ranking contribution is calculated here.",
        ],
    }


def validate_histories(histories: Iterable[IndicatorHistory]) -> list[IndicatorHistory]:
    records = sorted(histories, key=lambda history: history.territory_id)
    if not records:
        raise ValueError("comparability audit requires at least one history")
    keys = {(history.territory_id, history.indicator_id) for history in records}
    if len(keys) != len(records):
        raise ValueError("comparability audit received duplicate territory histories")
    first = records[0]
    expected = (first.indicator_id, first.start_year, first.end_year)
    if any(
        (history.indicator_id, history.start_year, history.end_year) != expected
        for history in records
    ):
        raise ValueError("comparability audit histories must share indicator and interval")
    return records


def municipality_comparability_row(
    history: IndicatorHistory,
    territory_names: Mapping[str, str],
) -> dict[str, Any]:
    flag_rows = [{"code": flag.code, "years": list(flag.years)} for flag in history.flags]
    coverage = history.coverage
    candidate = (
        coverage.available_year_count == coverage.requested_year_count
        and coverage.provenance_incomplete_year_count == 0
    )
    return {
        "territory_id": history.territory_id,
        "territory_name": territory_names.get(history.territory_id, history.territory_id),
        "coverage_status": coverage.status.value,
        "available_year_count": coverage.available_year_count,
        "suppressed_year_count": coverage.suppressed_year_count,
        "missing_year_count": coverage.missing_year_count,
        "provenance_incomplete_year_count": (coverage.provenance_incomplete_year_count),
        "candidate_for_domain_comparison": candidate,
        "flags": flag_rows,
        "annual_values": [
            {
                "year": point.year,
                "status": point.status.value,
                "value": point.value,
                "numerator_value": point.numerator_value,
                "denominator_value": point.denominator_value,
                "denominator_year": point.denominator_year,
            }
            for point in history.points
        ],
    }


def annual_coverage_row(
    histories: Sequence[IndicatorHistory],
    year: int,
) -> dict[str, Any]:
    points = [history.points[year - history.start_year] for history in histories]
    statuses = Counter(point.status.value for point in points)
    population_years: set[int] = set()
    population_methods: set[str] = set()
    sinan_releases: set[str] = set()
    for point in points:
        collect_annual_provenance(
            point,
            population_years,
            population_methods,
            sinan_releases,
        )
    return {
        "year": year,
        "territory_count": len(points),
        "available_count": statuses[HistoryPointStatus.AVAILABLE.value],
        "suppressed_count": statuses[HistoryPointStatus.SUPPRESSED.value],
        "missing_count": statuses[HistoryPointStatus.MISSING.value],
        "provenance_incomplete_count": sum(
            point.status != HistoryPointStatus.MISSING
            and (
                not point.source_provenance
                or any(
                    source.reference_year is None
                    or source.release_status == "unknown"
                    or source.dataset_kind == "unknown"
                    for source in point.source_provenance
                )
            )
            for point in points
        ),
        "population_reference_years": sorted(population_years),
        "population_methods": sorted(population_methods),
        "sinan_release_statuses": sorted(sinan_releases),
    }


def collect_annual_provenance(
    point: IndicatorHistoryPoint,
    population_years: set[int],
    population_methods: set[str],
    sinan_releases: set[str],
) -> None:
    for source in point.source_provenance:
        if source.source_id == "ibge_population":
            if source.reference_year is not None:
                population_years.add(source.reference_year)
            population_methods.add(source.dataset_kind)
        elif source.source_id == "sinan_tb":
            sinan_releases.add(source.release_status)


def comparability_flag_rows(
    histories: Sequence[IndicatorHistory],
) -> list[dict[str, Any]]:
    patterns_by_code: defaultdict[str, defaultdict[tuple[int, ...], list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for history in histories:
        for flag in history.flags:
            patterns_by_code[flag.code][flag.years].append(history.territory_id)

    rows = []
    for code, patterns in sorted(patterns_by_code.items()):
        territory_ids = sorted(
            territory_id for pattern_ids in patterns.values() for territory_id in pattern_ids
        )
        rows.append(
            {
                "code": code,
                "territory_count": len(territory_ids),
                "territory_ids": territory_ids,
                "years": sorted({year for pattern in patterns for year in pattern}),
                "patterns": [
                    {
                        "years": list(years),
                        "territory_count": len(pattern_ids),
                        "territory_ids": sorted(pattern_ids),
                    }
                    for years, pattern_ids in sorted(patterns.items())
                ],
            }
        )
    return rows


def write_history_comparability_report(
    report: dict[str, Any],
    output_dir: Path,
) -> Path:
    scope = report["scope"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (
        "incidence_history_comparability_"
        f"{str(scope['geographic_scope']).lower()}_"
        f"{scope['start_year']}_{scope['end_year']}.json"
    )
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
