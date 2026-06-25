from __future__ import annotations

from tbia.domain.indicators import MANDATORY_INDICATOR_IDS, compute_indicator_values
from tbia.domain.models import CaseAggregate, MortalityAggregate, PopulationDenominator


def test_compute_indicator_values_applies_formulas_and_suppression() -> None:
    values = compute_indicator_values(
        populations=[
            PopulationDenominator("2304400", 2023, 1_000_000, "ibge_population"),
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

    cure = by_key[("2304400", "cure_proportion")]
    assert cure.value == 80.0

    suppressed = by_key[("2303709", "tb_incidence_per_100k")]
    assert suppressed.value is None
    assert suppressed.is_suppressed is True


def test_mandatory_indicator_set_excludes_non_public_restricted_indicators() -> None:
    assert "drug_resistant_tb_burden" not in MANDATORY_INDICATOR_IDS
    assert "preventive_treatment_initiation" not in MANDATORY_INDICATOR_IDS
    assert "tb_incidence_per_100k" in MANDATORY_INDICATOR_IDS
