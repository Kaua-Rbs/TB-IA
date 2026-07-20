from __future__ import annotations

from tbia.domain.models import IndicatorValue, ScenarioSeverity, TerritoryScenario
from tbia.domain.recommendations import build_recommendations
from tbia.domain.scenarios import build_priority_ranking, build_territory_scenarios


def indicator(territory_id: str, indicator_id: str, value: float) -> IndicatorValue:
    return IndicatorValue(
        indicator_id=indicator_id,
        territory_id=territory_id,
        year=2023,
        value=value,
        numerator_value=10,
        denominator_value=100,
        is_suppressed=False,
        source_ids=("fixture",),
        caveats="fixture",
    )


def scenario(
    territory_id: str,
    rule_id: str,
    score: float,
    ranking_dimension: str,
    severity: ScenarioSeverity = ScenarioSeverity.MODERATE,
) -> TerritoryScenario:
    return TerritoryScenario(
        territory_id=territory_id,
        year=2023,
        rule_id=rule_id,
        scenario_id=rule_id,
        severity=severity,
        score=score,
        explanation=f"{rule_id} fixture",
        indicator_id=f"{rule_id}_indicator",
        indicator_value=10,
        threshold_value=5,
        ranking_dimension=ranking_dimension,
    )


def test_build_territory_scenarios_uses_transparent_percentile_rules() -> None:
    scenarios = build_territory_scenarios(
        [
            indicator("2304400", "tb_incidence_per_100k", 90),
            indicator("2303709", "tb_incidence_per_100k", 30),
            indicator("2312908", "tb_incidence_per_100k", 20),
            indicator("2305001", "tb_incidence_per_100k", 50),
            indicator("2306009", "tb_incidence_per_100k", 40),
            indicator("2304400", "cure_proportion", 60),
            indicator("2303709", "cure_proportion", 90),
            indicator("2312908", "cure_proportion", 95),
            indicator("2305001", "cure_proportion", 75),
            indicator("2306009", "cure_proportion", 80),
        ]
    )

    scenario_ids = {(scenario.territory_id, scenario.rule_id) for scenario in scenarios}

    assert ("2304400", "high_incidence") in scenario_ids
    assert ("2304400", "low_cure") in scenario_ids
    assert all("Value=" in scenario.explanation for scenario in scenarios)


def test_build_priority_ranking_and_recommendations_are_deterministic() -> None:
    scenarios = build_territory_scenarios(
        [
            indicator("2304400", "tb_incidence_per_100k", 90),
            indicator("2303709", "tb_incidence_per_100k", 30),
            indicator("2312908", "tb_incidence_per_100k", 20),
            indicator("2305001", "tb_incidence_per_100k", 50),
            indicator("2306009", "tb_incidence_per_100k", 40),
            indicator("2304400", "treatment_interruption_proportion", 20),
            indicator("2303709", "treatment_interruption_proportion", 10),
            indicator("2312908", "treatment_interruption_proportion", 5),
            indicator("2305001", "treatment_interruption_proportion", 15),
            indicator("2306009", "treatment_interruption_proportion", 12),
        ]
    )
    ranking = build_priority_ranking(scenarios)
    recommendations = build_recommendations(scenarios)

    assert ranking[0][0] == "2304400"
    assert recommendations[0].territory_id == "2304400"
    assert "professional review" in recommendations[0].explanation


def test_priority_ranking_caps_correlated_dimensions_and_uses_dimension_ties() -> None:
    scenarios = [
        scenario("2304400", "signal_a", 5, "diagnostic_access"),
        scenario("2304400", "signal_b", 4, "diagnostic_access"),
        scenario("2303709", "signal_c", 3, "dimension_c"),
        scenario("2303709", "signal_d", 2, "dimension_d"),
    ]

    ranking = build_priority_ranking(scenarios)

    assert {row[0]: row[2] for row in ranking} == {
        "2303709": 5,
        "2304400": 5,
    }
    assert ranking[0][0] == "2303709"
    assert all(row[3] == 2 for row in ranking)


def test_recommendations_group_one_strategy_and_keep_all_trigger_rules() -> None:
    scenarios = [
        scenario(
            "2304400",
            "high_mortality",
            6,
            "high_mortality",
            ScenarioSeverity.HIGH,
        ),
        scenario(
            "2304400",
            "low_lab_confirmation",
            4,
            "diagnostic_access",
            ScenarioSeverity.HIGH,
        ),
    ]

    recommendations = build_recommendations(scenarios)

    diagnostic = [item for item in recommendations if item.strategy_id == "diagnostic_flow_review"]
    assert len(diagnostic) == 1
    assert diagnostic[0].rule_id == "high_mortality"
    assert diagnostic[0].trigger_rule_ids == (
        "high_mortality",
        "low_lab_confirmation",
    )


def test_build_territory_scenarios_skips_thresholds_with_small_comparison_group() -> None:
    scenarios = build_territory_scenarios(
        [
            indicator("2304400", "tb_incidence_per_100k", 90),
            indicator("2303709", "tb_incidence_per_100k", 30),
            indicator("2312908", "tb_incidence_per_100k", 20),
            indicator("2305001", "tb_incidence_per_100k", 50),
        ]
    )

    assert scenarios == []
