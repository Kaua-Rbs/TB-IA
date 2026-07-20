from __future__ import annotations

from tbia.domain.models import (
    IndicatorDirection,
    IndicatorValue,
    ScenarioEvaluationStatus,
    ScenarioRule,
    ScenarioSeverity,
    TerritoryScenario,
)
from tbia.domain.recommendations import build_recommendations
from tbia.domain.scenarios import (
    DEFAULT_SCENARIO_RULES,
    build_priority_ranking,
    build_territory_scenarios,
    evaluate_territory_scenarios,
)


def indicator(
    territory_id: str,
    indicator_id: str,
    value: float | None,
    *,
    is_suppressed: bool = False,
) -> IndicatorValue:
    return IndicatorValue(
        indicator_id=indicator_id,
        territory_id=territory_id,
        year=2023,
        value=value,
        numerator_value=10,
        denominator_value=100,
        is_suppressed=is_suppressed,
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


def test_diagnostic_coverage_rules_are_provisional_and_use_existing_dimensions() -> None:
    diagnostic_rules = {
        rule.rule_id: rule
        for rule in DEFAULT_SCENARIO_RULES
        if rule.rule_id
        in {
            "low_hiv_testing",
            "low_trm_tb_use",
            "low_culture_use_among_retreatment",
        }
    }

    assert set(diagnostic_rules) == {
        "low_hiv_testing",
        "low_trm_tb_use",
        "low_culture_use_among_retreatment",
    }
    assert {rule.rule_id: rule.ranking_dimension for rule in diagnostic_rules.values()} == {
        "low_hiv_testing": "tb_hiv_integration",
        "low_trm_tb_use": "diagnostic_access",
        "low_culture_use_among_retreatment": "resistance_surveillance",
    }
    assert all(rule.minimum_count == 10 for rule in diagnostic_rules.values())
    assert all(rule.minimum_coverage_ratio == 0.05 for rule in diagnostic_rules.values())
    assert all(rule.review_status == "pending_domain_review" for rule in diagnostic_rules.values())


def test_scenario_evaluation_requires_exact_count_and_coverage_gates() -> None:
    rule = ScenarioRule(
        rule_id="coverage_gate",
        name="Coverage gate",
        indicator_id="coverage_indicator",
        threshold_method="p25",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.LOW_BAD,
        explanation_template="Provisional comparative rule.",
        strategy_ids=("diagnostic_flow_review",),
        ranking_dimension="diagnostic_access",
        minimum_count=10,
        minimum_coverage_ratio=0.05,
        review_status="pending_domain_review",
    )
    values = [
        indicator(f"23{index:05d}", rule.indicator_id, float(index)) for index in range(1, 11)
    ]
    territory_ids = {f"23{index:05d}" for index in range(1, 201)}

    exact_gate = evaluate_territory_scenarios(
        values,
        (rule,),
        geographic_scope="CE",
        year=2023,
        territory_ids=territory_ids,
    )
    below_count = evaluate_territory_scenarios(
        values[:-1],
        (rule,),
        geographic_scope="CE",
        year=2023,
        territory_ids=territory_ids,
    )
    below_coverage = evaluate_territory_scenarios(
        values,
        (rule,),
        geographic_scope="CE",
        year=2023,
        territory_ids={*territory_ids, "23200001"},
    )

    assert exact_gate.evaluations[0].status == ScenarioEvaluationStatus.READY
    assert exact_gate.evaluations[0].coverage_ratio == 0.05
    assert exact_gate.evaluations[0].threshold_value is not None
    assert exact_gate.scenarios
    assert all(
        scenario.review_status == "pending_domain_review" for scenario in exact_gate.scenarios
    )
    assert below_count.evaluations[0].status == ScenarioEvaluationStatus.INSUFFICIENT_COMPARISON
    assert below_count.scenarios == ()
    assert below_coverage.evaluations[0].status == ScenarioEvaluationStatus.INSUFFICIENT_COMPARISON
    assert below_coverage.scenarios == ()


def test_scenario_evaluation_distinguishes_missing_and_suppressed_data() -> None:
    rule = next(rule for rule in DEFAULT_SCENARIO_RULES if rule.rule_id == "low_hiv_testing")
    territory_ids = {f"23{index:05d}" for index in range(1, 11)}
    missing = evaluate_territory_scenarios(
        [],
        (rule,),
        geographic_scope="CE",
        year=2023,
        territory_ids=territory_ids,
    )
    suppressed = evaluate_territory_scenarios(
        [indicator("2300001", rule.indicator_id, None, is_suppressed=True)],
        (rule,),
        geographic_scope="CE",
        year=2023,
        territory_ids=territory_ids,
    )

    assert missing.evaluations[0].status == ScenarioEvaluationStatus.MISSING_INDICATOR
    assert missing.evaluations[0].suppressed_count == 0
    assert suppressed.evaluations[0].status == ScenarioEvaluationStatus.INSUFFICIENT_COMPARISON
    assert suppressed.evaluations[0].suppressed_count == 1
    assert suppressed.scenarios == ()
