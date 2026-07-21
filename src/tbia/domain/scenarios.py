from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from tbia.domain.models import (
    IndicatorDirection,
    IndicatorValue,
    ScenarioBuildResult,
    ScenarioEvaluationStatus,
    ScenarioRule,
    ScenarioRuleEvaluation,
    ScenarioSeverity,
    TerritoryScenario,
)

DIAGNOSTIC_SCENARIO_RULE_IDS = frozenset(
    {
        "low_hiv_testing",
        "low_trm_tb_use",
        "low_culture_use_among_retreatment",
    }
)

DEFAULT_SCENARIO_RULES: tuple[ScenarioRule, ...] = (
    ScenarioRule(
        rule_id="high_incidence",
        name="High incidence",
        indicator_id="tb_incidence_per_100k",
        threshold_method="p75",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.HIGH,
        direction=IndicatorDirection.HIGH_BAD,
        explanation_template=(
            "TB incidence is at or above the p75 threshold for the selected UF/year."
        ),
        strategy_ids=("active_case_finding", "contact_investigation"),
        ranking_dimension="high_incidence",
    ),
    ScenarioRule(
        rule_id="high_mortality",
        name="High mortality",
        indicator_id="tb_mortality_per_100k",
        threshold_method="p75",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.HIGH,
        direction=IndicatorDirection.HIGH_BAD,
        explanation_template=(
            "TB mortality is at or above the p75 threshold for the selected UF/year."
        ),
        strategy_ids=("diagnostic_flow_review", "care_pathway_review"),
        ranking_dimension="high_mortality",
    ),
    ScenarioRule(
        rule_id="high_treatment_interruption",
        name="High treatment interruption",
        indicator_id="treatment_interruption_proportion",
        threshold_method="p75",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.HIGH,
        direction=IndicatorDirection.HIGH_BAD,
        explanation_template="Treatment interruption is at or above the p75 threshold.",
        strategy_ids=("adherence_support",),
        ranking_dimension="high_treatment_interruption",
    ),
    ScenarioRule(
        rule_id="low_cure",
        name="Low cure",
        indicator_id="cure_proportion",
        threshold_method="p25",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.HIGH,
        direction=IndicatorDirection.LOW_BAD,
        explanation_template="Cure proportion is at or below the p25 threshold.",
        strategy_ids=("adherence_support", "care_pathway_review"),
        ranking_dimension="low_cure",
    ),
    ScenarioRule(
        rule_id="high_retreatment",
        name="High retreatment",
        indicator_id="retreatment_proportion",
        threshold_method="p75",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.HIGH_BAD,
        explanation_template="Retreatment proportion is at or above the p75 threshold.",
        strategy_ids=("resistance_surveillance_review",),
        ranking_dimension="resistance_surveillance",
    ),
    ScenarioRule(
        rule_id="low_lab_confirmation",
        name="Low laboratory confirmation",
        indicator_id="laboratory_confirmation_proportion",
        threshold_method="p25",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.HIGH,
        direction=IndicatorDirection.LOW_BAD,
        explanation_template="Laboratory confirmation is at or below the p25 threshold.",
        strategy_ids=("diagnostic_flow_review",),
        ranking_dimension="diagnostic_access",
    ),
    ScenarioRule(
        rule_id="high_tb_hiv_burden",
        name="High TB-HIV burden",
        indicator_id="tb_hiv_burden_proportion",
        threshold_method="p75",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.HIGH_BAD,
        explanation_template="TB-HIV burden is at or above the p75 threshold.",
        strategy_ids=("tb_hiv_integration",),
        ranking_dimension="tb_hiv_integration",
    ),
    ScenarioRule(
        rule_id="high_hospitalization_burden",
        name="High hospitalization burden",
        indicator_id="hospitalization_burden_per_100k",
        threshold_method="p75",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.HIGH_BAD,
        explanation_template="TB hospitalization burden is at or above the p75 threshold.",
        strategy_ids=("care_pathway_review",),
        ranking_dimension="high_hospitalization_burden",
    ),
    ScenarioRule(
        rule_id="low_hiv_testing",
        name="Low HIV testing",
        indicator_id="hiv_testing_proportion",
        threshold_method="p25",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.LOW_BAD,
        explanation_template=(
            "Provisional comparative rule: HIV testing is at or below the p25 threshold."
        ),
        strategy_ids=("tb_hiv_integration",),
        ranking_dimension="tb_hiv_integration",
        minimum_count=10,
        minimum_coverage_ratio=0.05,
        review_status="pending_domain_review",
    ),
    ScenarioRule(
        rule_id="low_trm_tb_use",
        name="Low TRM-TB use",
        indicator_id="trm_tb_use_proportion",
        threshold_method="p25",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.LOW_BAD,
        explanation_template=(
            "Provisional comparative rule: TRM-TB use is at or below the p25 threshold."
        ),
        strategy_ids=("diagnostic_flow_review",),
        ranking_dimension="diagnostic_access",
        minimum_count=10,
        minimum_coverage_ratio=0.05,
        review_status="pending_domain_review",
    ),
    ScenarioRule(
        rule_id="low_culture_use_among_retreatment",
        name="Low culture use among retreatment",
        indicator_id="culture_use_among_retreatment",
        threshold_method="p25",
        comparison_group="selected_uf_year",
        severity=ScenarioSeverity.MODERATE,
        direction=IndicatorDirection.LOW_BAD,
        explanation_template=(
            "Provisional comparative rule: culture use among pulmonary retreatment cases "
            "is at or below the p25 threshold."
        ),
        strategy_ids=("resistance_surveillance_review",),
        ranking_dimension="resistance_surveillance",
        minimum_count=10,
        minimum_coverage_ratio=0.05,
        review_status="pending_domain_review",
    ),
)


def build_territory_scenarios(
    values: Iterable[IndicatorValue],
    rules: Iterable[ScenarioRule] = DEFAULT_SCENARIO_RULES,
    *,
    comparison_scope: str = "uf",
) -> list[TerritoryScenario]:
    return list(
        evaluate_territory_scenarios(
            values,
            rules,
            comparison_scope=comparison_scope,
        ).scenarios
    )


def evaluate_territory_scenarios(
    values: Iterable[IndicatorValue],
    rules: Iterable[ScenarioRule] = DEFAULT_SCENARIO_RULES,
    *,
    comparison_scope: str = "uf",
    geographic_scope: str = "",
    year: int | None = None,
    territory_ids: Iterable[str] | None = None,
) -> ScenarioBuildResult:
    materialized_values = list(values)
    scope_territory_ids = (
        set(territory_ids)
        if territory_ids is not None
        else {value.territory_id for value in materialized_values}
    )
    effective_year = (
        year
        if year is not None
        else next(
            (value.year for value in materialized_values),
            0,
        )
    )
    values_by_indicator: dict[str, list[IndicatorValue]] = defaultdict(list)
    for value in materialized_values:
        if value.territory_id in scope_territory_ids:
            values_by_indicator[value.indicator_id].append(value)

    scenarios: list[TerritoryScenario] = []
    evaluations: list[ScenarioRuleEvaluation] = []
    for rule in rules:
        evaluation, available_values = evaluate_rule_readiness(
            rule,
            values_by_indicator.get(rule.indicator_id, []),
            geographic_scope=geographic_scope,
            comparison_scope=comparison_scope,
            year=effective_year,
            territory_ids=scope_territory_ids,
        )
        evaluations.append(evaluation)
        if evaluation.threshold_value is None:
            continue
        scenarios.extend(
            build_rule_scenarios(
                available_values,
                rule,
                threshold=evaluation.threshold_value,
                comparison_scope=comparison_scope,
            )
        )

    return ScenarioBuildResult(
        scenarios=tuple(
            sorted(scenarios, key=lambda item: (-item.score, item.territory_id, item.rule_id))
        ),
        evaluations=tuple(evaluations),
    )


def evaluate_rule_readiness(
    rule: ScenarioRule,
    indicator_values: Iterable[IndicatorValue],
    *,
    geographic_scope: str,
    comparison_scope: str,
    year: int,
    territory_ids: set[str],
) -> tuple[ScenarioRuleEvaluation, list[IndicatorValue]]:
    by_territory = {
        value.territory_id: value
        for value in indicator_values
        if value.territory_id in territory_ids
    }
    available_values = [
        value
        for value in by_territory.values()
        if value.value is not None and not value.is_suppressed
    ]
    suppressed_count = sum(1 for value in by_territory.values() if value.is_suppressed)
    territory_count = len(territory_ids)
    available_count = len(available_values)
    unavailable_count = max(territory_count - available_count - suppressed_count, 0)
    coverage_ratio = available_count / territory_count if territory_count else 0.0
    status = scenario_evaluation_status(
        has_indicator_values=bool(by_territory),
        available_count=available_count,
        coverage_ratio=coverage_ratio,
        rule=rule,
    )
    threshold = (
        threshold_for_rule(available_values, rule)
        if status == ScenarioEvaluationStatus.READY
        else None
    )
    return (
        ScenarioRuleEvaluation(
            geographic_scope=geographic_scope,
            year=year,
            comparison_scope=comparison_scope,
            rule_id=rule.rule_id,
            status=status,
            available_count=available_count,
            suppressed_count=suppressed_count,
            unavailable_count=unavailable_count,
            territory_count=territory_count,
            coverage_ratio=round(coverage_ratio, 6),
            threshold_value=threshold,
            minimum_count=rule.minimum_count,
            minimum_coverage_ratio=rule.minimum_coverage_ratio,
        ),
        available_values,
    )


def scenario_evaluation_status(
    *,
    has_indicator_values: bool,
    available_count: int,
    coverage_ratio: float,
    rule: ScenarioRule,
) -> ScenarioEvaluationStatus:
    if not has_indicator_values:
        return ScenarioEvaluationStatus.MISSING_INDICATOR
    if available_count < rule.minimum_count or coverage_ratio < rule.minimum_coverage_ratio:
        return ScenarioEvaluationStatus.INSUFFICIENT_COMPARISON
    return ScenarioEvaluationStatus.READY


def build_rule_scenarios(
    indicator_values: Iterable[IndicatorValue],
    rule: ScenarioRule,
    *,
    threshold: float,
    comparison_scope: str,
) -> list[TerritoryScenario]:
    scenarios: list[TerritoryScenario] = []
    for value in indicator_values:
        if value.value is None or not rule_matches(value.value, threshold, rule.direction):
            continue
        score = severity_weight(rule.severity) * score_multiplier(value.value, threshold, rule)
        scenarios.append(
            TerritoryScenario(
                territory_id=value.territory_id,
                year=value.year,
                rule_id=rule.rule_id,
                scenario_id=rule.rule_id,
                severity=rule.severity,
                score=round(score, 4),
                explanation=(
                    f"{rule.explanation_template} "
                    f"Value={value.value:.2f}; threshold={threshold:.2f}."
                ),
                indicator_id=rule.indicator_id,
                indicator_value=value.value,
                threshold_value=threshold,
                comparison_scope=comparison_scope,
                ranking_dimension=rule.ranking_dimension or rule.rule_id,
                review_status=rule.review_status,
            )
        )
    return scenarios


def summarize_dimension_scores(
    dimension_scores: Iterable[tuple[str, float]],
) -> tuple[float, int]:
    maximum_by_dimension: dict[str, float] = {}
    for dimension, score in dimension_scores:
        current = maximum_by_dimension.get(dimension)
        if current is None or score > current:
            maximum_by_dimension[dimension] = score
    return round(sum(maximum_by_dimension.values()), 4), len(maximum_by_dimension)


def build_priority_ranking(
    scenarios: Iterable[TerritoryScenario],
) -> list[tuple[str, int, float, int]]:
    totals: dict[tuple[str, int], list[TerritoryScenario]] = defaultdict(list)
    for scenario in scenarios:
        totals[(scenario.territory_id, scenario.year)].append(scenario)

    ranking = []
    for (territory_id, year), territory_scenarios in totals.items():
        score, dimension_count = summarize_dimension_scores(
            (scenario.ranking_dimension or scenario.rule_id, scenario.score)
            for scenario in territory_scenarios
        )
        ranking.append((territory_id, year, score, len(territory_scenarios), dimension_count))

    ranked = sorted(ranking, key=lambda item: (-item[2], -item[4], item[0]))
    return [
        (territory_id, year, score, scenario_count)
        for territory_id, year, score, scenario_count, _dimension_count in ranked
    ]


def threshold_for_rule(
    values: Iterable[IndicatorValue],
    rule: ScenarioRule,
) -> float | None:
    raw_values = sorted(value.value for value in values if value.value is not None)
    if len(raw_values) < rule.minimum_count:
        return None

    if rule.threshold_method == "p75":
        return percentile(raw_values, 75)
    if rule.threshold_method == "p25":
        return percentile(raw_values, 25)
    raise ValueError(f"unsupported threshold method: {rule.threshold_method}")


def percentile(sorted_values: list[float], percentile_value: int) -> float:
    if not sorted_values:
        raise ValueError("cannot calculate percentile for empty values")
    rank = round((percentile_value / 100) * (len(sorted_values) - 1))
    return sorted_values[rank]


def rule_matches(value: float, threshold: float, direction: IndicatorDirection) -> bool:
    if direction == IndicatorDirection.HIGH_BAD:
        return value >= threshold
    if direction == IndicatorDirection.LOW_BAD:
        return value <= threshold
    return False


def severity_weight(severity: ScenarioSeverity) -> float:
    weights = {
        ScenarioSeverity.LOW: 1.0,
        ScenarioSeverity.MODERATE: 2.0,
        ScenarioSeverity.HIGH: 3.0,
    }
    return weights[severity]


def score_multiplier(value: float, threshold: float, rule: ScenarioRule) -> float:
    if threshold <= 0:
        return 1.0
    if rule.direction == IndicatorDirection.LOW_BAD:
        return max(1.0, threshold / max(value, 0.01))
    return max(1.0, value / threshold)
