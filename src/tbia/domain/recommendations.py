from __future__ import annotations

from collections.abc import Iterable

from tbia.domain.models import Recommendation, ScenarioSeverity, Strategy, TerritoryScenario
from tbia.domain.scenarios import DEFAULT_SCENARIO_RULES

STRATEGIES: tuple[Strategy, ...] = (
    Strategy(
        strategy_id="active_case_finding",
        name="Active search for respiratory symptomatic individuals",
        target_problem="High incidence or suspected underdiagnosis",
        evidence_source="Brazilian TB control recommendations; WHO End TB Strategy",
        evidence_strength="Guideline-supported",
        required_resources="Community health workers, APS team, sputum collection flow",
        estimated_cost_level="medium",
        operational_complexity="medium",
        monitoring_indicators=("tb_incidence_per_100k", "laboratory_confirmation_proportion"),
        caveats=(
            "Requires local operational planning; public data alone cannot identify individuals."
        ),
    ),
    Strategy(
        strategy_id="contact_investigation",
        name="Strengthen systematic contact investigation",
        target_problem="High pulmonary TB burden or high incidence",
        evidence_source="Brazilian TB control recommendations; WHO consolidated TB guidelines",
        evidence_strength="Guideline-supported",
        required_resources="APS team, surveillance team, contact registry workflow",
        estimated_cost_level="medium",
        operational_complexity="medium",
        monitoring_indicators=("tb_incidence_per_100k",),
        caveats="MVP 1 does not calculate the official contact indicator until validation.",
    ),
    Strategy(
        strategy_id="diagnostic_flow_review",
        name="Review and strengthen diagnostic flow",
        target_problem="Low laboratory confirmation or high mortality",
        evidence_source="Brazilian TB recommendations; Caderno de Indicadores da Tuberculose",
        evidence_strength="Guideline-supported",
        required_resources="Sample collection, lab transport, TRM-TB access, result monitoring",
        estimated_cost_level="medium",
        operational_complexity="medium",
        monitoring_indicators=("laboratory_confirmation_proportion", "trm_tb_use_proportion"),
        caveats="Public aggregate data flags the problem but does not identify missed patients.",
    ),
    Strategy(
        strategy_id="adherence_support",
        name="Strengthen adherence support and active follow-up",
        target_problem="High treatment interruption or low cure",
        evidence_source="Brazilian TB recommendations; WHO adherence technology handbook",
        evidence_strength="Guideline-supported",
        required_resources="Nursing, CHW follow-up, pharmacy coordination, social support pathway",
        estimated_cost_level="medium",
        operational_complexity="medium",
        monitoring_indicators=("cure_proportion", "treatment_interruption_proportion"),
        caveats="Patient-level risk queues require MVP 2 or MVP 3 authorized data.",
    ),
    Strategy(
        strategy_id="resistance_surveillance_review",
        name="Audit resistance surveillance pathway",
        target_problem="High retreatment or possible resistance surveillance gap",
        evidence_source="Brazilian TB recommendations; WHO consolidated TB guidelines",
        evidence_strength="Guideline-supported",
        required_resources="Culture, DST, TRM-TB, reference-service referral flow",
        estimated_cost_level="medium",
        operational_complexity="high",
        monitoring_indicators=("culture_use_among_retreatment", "retreatment_proportion"),
        caveats="Drug-resistant TB burden itself is not public bulk data in MVP 1.",
    ),
    Strategy(
        strategy_id="tb_hiv_integration",
        name="Strengthen TB-HIV integration",
        target_problem="High TB-HIV burden or low HIV testing",
        evidence_source="Brazilian TB recommendations; WHO consolidated TB guidelines",
        evidence_strength="Guideline-supported",
        required_resources="HIV testing, SAE linkage, APS/surveillance coordination",
        estimated_cost_level="medium",
        operational_complexity="medium",
        monitoring_indicators=("hiv_testing_proportion", "tb_hiv_burden_proportion"),
        caveats="Requires local care-network coordination beyond public dashboard review.",
    ),
    Strategy(
        strategy_id="care_pathway_review",
        name="Review severe disease and care pathway signals",
        target_problem="High mortality, high hospitalization, or low cure",
        evidence_source="Brazilian TB recommendations; municipal surveillance review practice",
        evidence_strength="Operational expert validation required",
        required_resources="Surveillance, APS, hospital network, mortality review process",
        estimated_cost_level="medium",
        operational_complexity="high",
        monitoring_indicators=("tb_mortality_per_100k", "hospitalization_burden_per_100k"),
        caveats="Hospitalization is a proxy and should not be interpreted as incidence.",
    ),
)


def build_recommendations(scenarios: Iterable[TerritoryScenario]) -> list[Recommendation]:
    strategy_ids_by_rule = {rule.rule_id: rule.strategy_ids for rule in DEFAULT_SCENARIO_RULES}
    recommendations: list[Recommendation] = []
    seen: set[tuple[str, int, str, str]] = set()

    for scenario in scenarios:
        for strategy_id in strategy_ids_by_rule.get(scenario.rule_id, ()):
            key = (scenario.territory_id, scenario.year, strategy_id, scenario.rule_id)
            if key in seen:
                continue
            seen.add(key)
            recommendations.append(
                Recommendation(
                    territory_id=scenario.territory_id,
                    year=scenario.year,
                    strategy_id=strategy_id,
                    rule_id=scenario.rule_id,
                    priority=scenario.severity,
                    explanation=(
                        f"Recommended because {scenario.rule_id} was triggered. "
                        "This is decision support and requires professional review."
                    ),
                )
            )

    return sorted(
        recommendations,
        key=lambda item: (
            item.territory_id,
            item.year,
            priority_sort_value(item.priority),
            item.strategy_id,
        ),
    )


def get_strategy(strategy_id: str) -> Strategy:
    for strategy in STRATEGIES:
        if strategy.strategy_id == strategy_id:
            return strategy
    raise KeyError(f"unknown strategy: {strategy_id}")


def priority_sort_value(priority: ScenarioSeverity) -> int:
    order = {
        ScenarioSeverity.HIGH: 0,
        ScenarioSeverity.MODERATE: 1,
        ScenarioSeverity.LOW: 2,
    }
    return order[priority]
