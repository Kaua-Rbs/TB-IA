from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from tbia.domain.models import (
    IndicatorDirection,
    IndicatorValue,
    ScenarioRule,
    ScenarioSeverity,
    TerritoryScenario,
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
    ),
)


def build_territory_scenarios(
    values: Iterable[IndicatorValue],
    rules: Iterable[ScenarioRule] = DEFAULT_SCENARIO_RULES,
) -> list[TerritoryScenario]:
    values_by_indicator: dict[str, list[IndicatorValue]] = defaultdict(list)
    for value in values:
        if value.value is not None and not value.is_suppressed:
            values_by_indicator[value.indicator_id].append(value)

    scenarios: list[TerritoryScenario] = []
    for rule in rules:
        indicator_values = values_by_indicator.get(rule.indicator_id, [])
        threshold = threshold_for_rule(indicator_values, rule)
        if threshold is None:
            continue

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
                )
            )

    return sorted(scenarios, key=lambda item: (-item.score, item.territory_id, item.rule_id))


def build_priority_ranking(
    scenarios: Iterable[TerritoryScenario],
) -> list[tuple[str, int, float, int]]:
    totals: dict[tuple[str, int], list[float]] = defaultdict(list)
    for scenario in scenarios:
        totals[(scenario.territory_id, scenario.year)].append(scenario.score)

    ranking = [
        (territory_id, year, round(sum(scores), 4), len(scores))
        for (territory_id, year), scores in totals.items()
    ]
    return sorted(ranking, key=lambda item: (-item[2], -item[3], item[0]))


def threshold_for_rule(
    values: Iterable[IndicatorValue],
    rule: ScenarioRule,
) -> float | None:
    raw_values = sorted(value.value for value in values if value.value is not None)
    if not raw_values:
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
