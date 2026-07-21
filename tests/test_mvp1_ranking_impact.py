from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from tbia.domain.models import ScenarioSeverity, TerritoryScenario
from tbia.domain.ranking_impact import (
    REPORT_STATUS_PENDING_DOMAIN_REVIEW,
    build_diagnostic_ranking_impact_report,
    write_diagnostic_ranking_impact_report,
)


def scenario(
    territory_id: str,
    rule_id: str,
    score: float,
    dimension: str,
    *,
    comparison_scope: str = "uf",
) -> TerritoryScenario:
    return TerritoryScenario(
        territory_id=territory_id,
        year=2023,
        rule_id=rule_id,
        scenario_id=rule_id,
        severity=ScenarioSeverity.MODERATE,
        score=score,
        explanation="fixture",
        indicator_id=f"{rule_id}_indicator",
        indicator_value=1.0,
        threshold_value=2.0,
        comparison_scope=comparison_scope,
        ranking_dimension=dimension,
        review_status=("pending_domain_review" if rule_id.startswith("low_") else None),
    )


def test_diagnostic_ranking_impact_isolated_with_production_dimension_caps() -> None:
    scenarios = [
        scenario("A", "high_tb_hiv_burden", 3.0, "tb_hiv_integration"),
        scenario("A", "low_lab_confirmation", 4.0, "diagnostic_access"),
        scenario("A", "low_hiv_testing", 5.0, "tb_hiv_integration"),
        scenario("A", "low_trm_tb_use", 2.0, "diagnostic_access"),
        scenario("B", "high_incidence", 8.0, "high_incidence"),
        scenario(
            "C",
            "low_culture_use_among_retreatment",
            2.0,
            "resistance_surveillance",
        ),
    ]

    report = build_diagnostic_ranking_impact_report(
        scenarios,
        {"A": "Alpha", "B": "Beta", "C": "Gamma"},
        year=2023,
        geographic_scope="CE",
        comparison_scopes=("uf",),
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert report["status"] == REPORT_STATUS_PENDING_DOMAIN_REVIEW
    assert report["generated_at"] == "2026-07-21T00:00:00+00:00"
    comparison = report["comparisons"]["uf"]
    assert comparison["scenario_counts"] == {
        "baseline": 3,
        "candidate": 6,
        "diagnostic": 3,
    }
    assert comparison["territory_counts"] == {
        "baseline_ranked": 2,
        "candidate_ranked": 3,
        "directly_affected": 2,
        "newly_ranked": 1,
        "rank_changed": 3,
        "score_changed": 2,
    }
    assert comparison["ranking_impact"] == {
        "top_10_overlap_count": 2,
        "top_10_entered": ["C"],
        "top_10_left": [],
        "maximum_score_increase": 2.0,
    }
    assert comparison["dimension_cap"] == {
        "aggregation": "maximum scenario score per ranking dimension",
        "territories_with_correlated_scenarios": 1,
        "raw_scenario_score_total": 24.0,
        "capped_ranking_score_total": 19.0,
        "duplicate_score_excluded": 5.0,
    }
    assert [row["territory_id"] for row in comparison["baseline_top_10"]] == ["B", "A"]
    assert [row["territory_id"] for row in comparison["candidate_top_10"]] == [
        "A",
        "B",
        "C",
    ]

    changes = {row["territory_id"]: row for row in comparison["changes"]}
    assert changes["A"]["baseline_rank"] == 2
    assert changes["A"]["candidate_rank"] == 1
    assert changes["A"]["rank_change"] == 1
    assert changes["A"]["score_change"] == 2.0
    assert changes["A"]["diagnostic_rule_ids"] == [
        "low_hiv_testing",
        "low_trm_tb_use",
    ]
    assert changes["C"]["baseline_rank"] is None
    assert changes["C"]["candidate_rank"] == 3
    assert changes["B"]["has_diagnostic_signal"] is False


def test_diagnostic_ranking_impact_writer_uses_scope_and_year(tmp_path: Path) -> None:
    report = build_diagnostic_ranking_impact_report(
        [],
        {},
        year=2023,
        geographic_scope="BR",
        comparison_scopes=("uf", "national"),
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )

    output_path = write_diagnostic_ranking_impact_report(report, tmp_path)
    persisted = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.name == "diagnostic_ranking_impact_br_2023.json"
    assert persisted["scope"] == {"year": 2023, "geographic_scope": "BR"}
    assert set(persisted["comparisons"]) == {"uf", "national"}
    assert persisted["comparisons"]["national"]["scenario_counts"]["candidate"] == 0
