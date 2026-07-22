from __future__ import annotations

from tbia.domain.models import (
    IndicatorValue,
    ScenarioEvaluationStatus,
    ScenarioRuleEvaluation,
    SourceProvenance,
)
from tbia.domain.resistance_surveillance import (
    build_resistance_surveillance_profile,
)


def test_resistance_surveillance_profile_distinguishes_public_signal_states() -> None:
    profile = build_resistance_surveillance_profile(
        [
            indicator_value(
                "retreatment_proportion",
                value=18.0,
                numerator=9,
                denominator=50,
            ),
            indicator_value(
                "culture_use_among_retreatment",
                value=None,
                numerator=2,
                denominator=9,
                suppressed=True,
            ),
        ],
        [
            evaluation("high_retreatment", ScenarioEvaluationStatus.READY, 12.0),
            evaluation(
                "low_culture_use_among_retreatment",
                ScenarioEvaluationStatus.READY,
                30.0,
            ),
            evaluation(
                "low_trm_tb_use",
                ScenarioEvaluationStatus.MISSING_INDICATOR,
                None,
            ),
        ],
        {"high_retreatment", "low_culture_use_among_retreatment"},
        comparison_scope="uf",
    )

    assert profile["interpretation"] == "surveillance_gap_not_confirmed_burden"
    assert profile["confirmed_resistance_status"] == "not_available_in_public_aggregate_sources"
    assert profile["ranking_effect"] == "none"
    signals = {row["signal_id"]: row for row in profile["signals"]}

    retreatment = signals["high_retreatment"]
    assert retreatment["data_status"] == "available"
    assert retreatment["trigger_status"] == "triggered"
    assert retreatment["value"] == 18.0
    assert retreatment["source_ids"] == ["sinan_tb"]
    assert retreatment["source_provenance"][0]["reference_year"] == 2023

    culture = signals["low_culture_use_among_retreatment"]
    assert culture["data_status"] == "suppressed"
    assert culture["trigger_status"] == "not_evaluable"
    assert culture["value"] is None
    assert culture["numerator_value"] is None
    assert culture["denominator_value"] is None

    molecular = signals["low_trm_tb_use"]
    assert molecular["data_status"] == "missing"
    assert molecular["evaluation_status"] == "missing_indicator"
    assert molecular["trigger_status"] == "not_evaluable"


def test_ready_available_signal_can_be_explicitly_not_triggered() -> None:
    profile = build_resistance_surveillance_profile(
        [
            indicator_value(
                "trm_tb_use_proportion",
                value=75.0,
                numerator=75,
                denominator=100,
            )
        ],
        [
            evaluation(
                "low_trm_tb_use",
                ScenarioEvaluationStatus.READY,
                40.0,
            )
        ],
        set(),
        comparison_scope="national",
    )

    signals = {row["signal_id"]: row for row in profile["signals"]}
    molecular = signals["low_trm_tb_use"]
    assert molecular["trigger_status"] == "not_triggered"
    assert profile["comparison_scope"] == "national"


def indicator_value(
    indicator_id: str,
    *,
    value: float | None,
    numerator: float,
    denominator: float,
    suppressed: bool = False,
) -> IndicatorValue:
    return IndicatorValue(
        indicator_id=indicator_id,
        territory_id="2304400",
        year=2023,
        value=value,
        numerator_value=numerator,
        denominator_value=denominator,
        is_suppressed=suppressed,
        source_ids=("sinan_tb",),
        caveats="Public aggregate.",
        source_provenance=(
            SourceProvenance(
                source_id="sinan_tb",
                reference_year=2023,
                release_status="final",
                dataset_kind="notification",
                artifact_sha256="abc123",
            ),
        ),
    )


def evaluation(
    rule_id: str,
    status: ScenarioEvaluationStatus,
    threshold: float | None,
) -> ScenarioRuleEvaluation:
    return ScenarioRuleEvaluation(
        geographic_scope="CE",
        year=2023,
        comparison_scope="uf",
        rule_id=rule_id,
        status=status,
        available_count=10,
        suppressed_count=1,
        unavailable_count=0,
        territory_count=11,
        coverage_ratio=10 / 11,
        threshold_value=threshold,
        minimum_count=5,
        minimum_coverage_ratio=0.5,
    )
