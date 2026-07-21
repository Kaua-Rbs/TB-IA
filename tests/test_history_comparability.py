from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tbia.cli import app
from tbia.domain.history import IndicatorHistory, build_indicator_history
from tbia.domain.history_comparability import (
    REPORT_STATUS_PENDING_DOMAIN_REVIEW,
    build_history_comparability_report,
    validate_histories,
    write_history_comparability_report,
)
from tbia.domain.models import IndicatorValue, SourceProvenance


def history_value(
    territory_id: str,
    year: int,
    *,
    amount: float | None,
    suppressed: bool = False,
    release_status: str,
    population_kind: str,
) -> IndicatorValue:
    return IndicatorValue(
        indicator_id="tb_incidence_per_100k",
        territory_id=territory_id,
        year=year,
        value=amount,
        numerator_value=3 if suppressed else 10,
        denominator_value=100_000,
        is_suppressed=suppressed,
        source_ids=("sinan_tb", "ibge_population"),
        caveats="fixture",
        denominator_year=year,
        source_provenance=(
            SourceProvenance(
                "sinan_tb",
                reference_year=year,
                release_status=release_status,
                dataset_kind="notification",
            ),
            SourceProvenance(
                "ibge_population",
                reference_year=year,
                release_status="final",
                dataset_kind=population_kind,
            ),
        ),
    )


def sample_history(
    territory_id: str,
    *,
    suppressed_2020: bool = False,
) -> IndicatorHistory:
    return build_indicator_history(
        [
            history_value(
                territory_id,
                2019,
                amount=10,
                release_status="final",
                population_kind="estimate",
            ),
            history_value(
                territory_id,
                2020,
                amount=None if suppressed_2020 else 12,
                suppressed=suppressed_2020,
                release_status="preliminary",
                population_kind="census",
            ),
        ],
        indicator_id="tb_incidence_per_100k",
        territory_id=territory_id,
        start_year=2019,
        end_year=2020,
    )


def test_comparability_report_separates_coverage_from_structural_breaks(
    tmp_path: Path,
) -> None:
    generated_at = datetime(2026, 7, 21, tzinfo=UTC)
    report = build_history_comparability_report(
        [
            sample_history("2304400"),
            sample_history("2303709", suppressed_2020=True),
        ],
        {"2304400": "Fortaleza", "2303709": "Caucaia"},
        geographic_scope="CE",
        headline_territory_ids=("2304400",),
        source_bundle_sha256="a" * 64,
        generated_at=generated_at,
    )

    assert report["status"] == REPORT_STATUS_PENDING_DOMAIN_REVIEW
    assert report["generated_at"] == generated_at.isoformat()
    assert report["summary"] == {
        "territory_count": 2,
        "expected_point_count": 4,
        "available_point_count": 3,
        "suppressed_point_count": 1,
        "missing_point_count": 0,
        "provenance_incomplete_point_count": 0,
        "complete_series_territory_count": 1,
        "candidate_for_domain_comparison_count": 1,
    }
    assert report["annual_coverage"][1] == {
        "year": 2020,
        "territory_count": 2,
        "available_count": 1,
        "suppressed_count": 1,
        "missing_count": 0,
        "provenance_incomplete_count": 0,
        "population_reference_years": [2020],
        "population_methods": ["census"],
        "sinan_release_statuses": ["preliminary"],
    }
    shared_codes = {row["code"] for row in report["shared_structural_flags"]}
    assert shared_codes == {"source_release_changed", "denominator_method_changed"}
    suppression = next(
        row for row in report["comparability_flags"] if row["code"] == "suppressed_year"
    )
    assert suppression["territory_ids"] == ["2303709"]
    assert report["headline_municipalities"][0]["territory_name"] == "Fortaleza"
    assert report["headline_municipalities"][0]["candidate_for_domain_comparison"] is True
    output_path = write_history_comparability_report(report, tmp_path)
    assert output_path.name == "incidence_history_comparability_ce_2019_2020.json"
    assert json.loads(output_path.read_text(encoding="utf-8"))["summary"] == report["summary"]


def test_comparability_report_rejects_empty_duplicate_and_mixed_inputs() -> None:
    with pytest.raises(ValueError, match="at least one"):
        validate_histories([])

    fortaleza = sample_history("2304400")
    with pytest.raises(ValueError, match="duplicate"):
        validate_histories([fortaleza, fortaleza])

    longer = build_indicator_history(
        [
            history_value(
                "2303709",
                2018,
                amount=9,
                release_status="final",
                population_kind="estimate",
            )
        ],
        indicator_id="tb_incidence_per_100k",
        territory_id="2303709",
        start_year=2018,
        end_year=2020,
    )
    with pytest.raises(ValueError, match="share indicator and interval"):
        validate_histories([fortaleza, longer])


def test_validate_incidence_history_cli_reproduces_ce_audit(tmp_path: Path) -> None:
    output_dir = tmp_path / "validation"
    result = CliRunner().invoke(
        app,
        [
            "validate-incidence-history",
            "--database-url",
            f"sqlite:///{tmp_path / 'audit.db'}",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Coverage: 534 available, 570 suppressed, 0 missing." in result.output
    assert "Candidates for domain comparison: 56/184 municipalities." in result.output
    report_path = output_dir / "incidence_history_comparability_ce_2018_2023.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["expected_point_count"] == 1104
    assert report["summary"]["provenance_incomplete_point_count"] == 0
    assert {
        (row["year"], row["available_count"], row["suppressed_count"])
        for row in report["annual_coverage"]
    } == {
        (2018, 95, 89),
        (2019, 83, 101),
        (2020, 83, 101),
        (2021, 89, 95),
        (2022, 90, 94),
        (2023, 94, 90),
    }
    assert {row["code"] for row in report["shared_structural_flags"]} == {
        "source_release_changed",
        "denominator_method_changed",
        "denominator_year_mismatch",
    }
    assert len(report["headline_municipalities"]) == 5


def test_validate_incidence_history_cli_rejects_reversed_range(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "validate-incidence-history",
            "--year-from",
            "2023",
            "--year-to",
            "2022",
            "--database-url",
            f"sqlite:///{tmp_path / 'invalid.db'}",
        ],
    )

    assert result.exit_code == 2
    assert "--year-from must not exceed --year-to" in result.output
