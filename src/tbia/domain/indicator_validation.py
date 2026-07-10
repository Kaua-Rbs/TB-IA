from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tbia.domain.indicators import get_indicator_definition
from tbia.domain.models import IndicatorUnit, IndicatorValue

REPORT_STATUS_CLEAN = "success"
REPORT_STATUS_FAILED = "failed"


def build_indicator_validation_report(
    values: Iterable[IndicatorValue],
    *,
    year: int,
    geographic_scope: str,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    records = list(values)
    violations = [violation for value in records for violation in indicator_violations(value)]
    warnings = [warning for value in records for warning in indicator_warnings(value)]
    timestamp = generated_at or datetime.now(UTC)
    return {
        "status": REPORT_STATUS_FAILED if violations else REPORT_STATUS_CLEAN,
        "generated_at": timestamp.isoformat(),
        "scope": {"year": year, "geographic_scope": geographic_scope},
        "indicator_count": len(records),
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "violations": violations,
        "warnings": warnings,
        "caveats": [
            "This report checks mechanical public-output invariants only.",
            "It does not replace domain review of SINAN dictionaries or indicator handbooks.",
        ],
    }


def indicator_violations(value: IndicatorValue) -> list[dict[str, Any]]:
    definition = get_indicator_definition(value.indicator_id)
    violations: list[dict[str, Any]] = []

    if value.numerator_value < 0 or value.denominator_value < 0:
        violations.append(violation_row(value, "negative_count"))
    if value.denominator_value == 0 and value.numerator_value > 0:
        violations.append(violation_row(value, "zero_denominator_positive_numerator"))
    if (
        definition.unit == IndicatorUnit.PERCENT
        and value.denominator_value > 0
        and value.numerator_value > value.denominator_value
    ):
        violations.append(violation_row(value, "bounded_proportion_numerator_exceeds_denominator"))
    if (
        definition.unit == IndicatorUnit.PERCENT
        and not value.is_suppressed
        and value.value is not None
        and not 0 <= value.value <= 100
    ):
        violations.append(violation_row(value, "unsuppressed_percent_outside_0_100"))

    return violations


def indicator_warnings(value: IndicatorValue) -> list[dict[str, Any]]:
    if value.denominator_value == 0 and value.numerator_value == 0:
        return [violation_row(value, "zero_denominator")]
    return []


def violation_row(value: IndicatorValue, check: str) -> dict[str, Any]:
    return {
        "check": check,
        "indicator_id": value.indicator_id,
        "territory_id": value.territory_id,
        "year": value.year,
        "value": value.value,
        "numerator_value": value.numerator_value,
        "denominator_value": value.denominator_value,
        "is_suppressed": value.is_suppressed,
    }


def write_indicator_validation_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    year = report["scope"]["year"]
    scope_slug = str(report["scope"]["geographic_scope"]).lower()
    output_path = output_dir / f"indicator_validation_{scope_slug}_{year}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
