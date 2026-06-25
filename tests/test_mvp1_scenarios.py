from __future__ import annotations

from tbia.domain.models import IndicatorValue
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


def test_build_territory_scenarios_uses_transparent_percentile_rules() -> None:
    scenarios = build_territory_scenarios(
        [
            indicator("2304400", "tb_incidence_per_100k", 90),
            indicator("2303709", "tb_incidence_per_100k", 30),
            indicator("2312908", "tb_incidence_per_100k", 20),
            indicator("2304400", "cure_proportion", 60),
            indicator("2303709", "cure_proportion", 90),
            indicator("2312908", "cure_proportion", 95),
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
            indicator("2304400", "treatment_interruption_proportion", 20),
            indicator("2303709", "treatment_interruption_proportion", 10),
            indicator("2312908", "treatment_interruption_proportion", 5),
        ]
    )
    ranking = build_priority_ranking(scenarios)
    recommendations = build_recommendations(scenarios)

    assert ranking[0][0] == "2304400"
    assert recommendations[0].territory_id == "2304400"
    assert "professional review" in recommendations[0].explanation
