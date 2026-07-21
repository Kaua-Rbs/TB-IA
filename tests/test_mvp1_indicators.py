from __future__ import annotations

from pathlib import Path

from tbia.domain.indicator_validation import (
    build_indicator_validation_report,
    write_indicator_validation_report,
)
from tbia.domain.indicators import MANDATORY_INDICATOR_IDS, compute_indicator_values
from tbia.domain.models import CaseAggregate, MortalityAggregate, PopulationDenominator


def test_compute_indicator_values_applies_formulas_and_suppression() -> None:
    values = compute_indicator_values(
        populations=[
            PopulationDenominator(
                "2304400",
                2023,
                1_000_000,
                "ibge_population",
                source_year=2022,
                source_kind="census",
            ),
            PopulationDenominator("2303709", 2023, 100_000, "ibge_population"),
        ],
        cases=[
            CaseAggregate(
                territory_id="2304400",
                year=2023,
                notified_cases=100,
                new_cases=80,
                closed_cases=50,
                cured_cases=40,
                treatment_interruption_cases=5,
                retreatment_cases=10,
                new_pulmonary_cases=70,
                lab_confirmed_pulmonary_cases=35,
                hiv_tested_cases=60,
                tb_hiv_cases=8,
                trm_tb_cases=30,
                retreatment_pulmonary_cases=10,
                culture_retreated_cases=5,
            ),
            CaseAggregate(territory_id="2303709", year=2023, notified_cases=4, new_cases=4),
        ],
        mortalities=[
            MortalityAggregate("2304400", 2023, 10),
            MortalityAggregate("2303709", 2023, 1),
        ],
        year=2023,
        minimum_count=5,
    )
    by_key = {(value.territory_id, value.indicator_id): value for value in values}

    incidence = by_key[("2304400", "tb_incidence_per_100k")]
    assert incidence.value == 8.0
    assert incidence.is_suppressed is False
    assert incidence.denominator_year == 2022
    provenance = [
        (item.source_id, item.reference_year, item.dataset_kind)
        for item in incidence.source_provenance
    ]
    assert provenance == [("sinan_tb", 2023, "notification"), ("ibge_population", 2022, "census")]

    cure = by_key[("2304400", "cure_proportion")]
    assert cure.value == 80.0

    suppressed = by_key[("2303709", "tb_incidence_per_100k")]
    assert suppressed.value is None
    assert suppressed.is_suppressed is True


def test_mandatory_indicator_set_excludes_non_public_restricted_indicators() -> None:
    assert "drug_resistant_tb_burden" not in MANDATORY_INDICATOR_IDS
    assert "preventive_treatment_initiation" not in MANDATORY_INDICATOR_IDS
    assert "tb_incidence_per_100k" in MANDATORY_INDICATOR_IDS


def test_bounded_proportion_with_numerator_above_denominator_is_suppressed() -> None:
    values = compute_indicator_values(
        populations=[PopulationDenominator("2304400", 2023, 1_000_000, "ibge_population")],
        cases=[
            CaseAggregate(
                territory_id="2304400",
                year=2023,
                notified_cases=8,
                new_cases=4,
                hiv_tested_cases=8,
            )
        ],
        mortalities=[],
        year=2023,
        minimum_count=1,
    )
    by_key = {value.indicator_id: value for value in values}

    hiv_testing = by_key["hiv_testing_proportion"]
    assert hiv_testing.value is None
    assert hiv_testing.is_suppressed is True
    assert "numerator exceeds denominator" in hiv_testing.caveats


def test_indicator_validation_report_flags_invalid_bounded_proportion(tmp_path: Path) -> None:
    values = compute_indicator_values(
        populations=[PopulationDenominator("2304400", 2023, 1_000_000, "ibge_population")],
        cases=[
            CaseAggregate(
                territory_id="2304400",
                year=2023,
                notified_cases=8,
                new_cases=4,
                hiv_tested_cases=8,
            )
        ],
        mortalities=[],
        year=2023,
        minimum_count=1,
    )

    hiv_testing = next(value for value in values if value.indicator_id == "hiv_testing_proportion")
    report = build_indicator_validation_report([hiv_testing], year=2023, geographic_scope="CE")

    assert report["status"] == "failed"
    assert report["scope"] == {"year": 2023, "geographic_scope": "CE"}
    assert report["violation_count"] == 1
    assert report["violations"][0]["check"] == "bounded_proportion_numerator_exceeds_denominator"
    assert write_indicator_validation_report(report, tmp_path).name == (
        "indicator_validation_ce_2023.json"
    )


def test_indicator_validation_report_treats_zero_over_zero_as_warning() -> None:
    values = compute_indicator_values(
        populations=[PopulationDenominator("2304400", 2023, 1_000_000, "ibge_population")],
        cases=[CaseAggregate(territory_id="2304400", year=2023, notified_cases=1)],
        mortalities=[],
        year=2023,
        minimum_count=1,
    )
    cure = next(value for value in values if value.indicator_id == "cure_proportion")

    report = build_indicator_validation_report([cure], year=2023, geographic_scope="CE")

    assert report["status"] == "success"
    assert report["violation_count"] == 0
    assert report["warning_count"] == 1
    assert report["warnings"][0]["check"] == "zero_denominator"
