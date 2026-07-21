from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tbia.domain.models import TerritoryScenario
from tbia.domain.scenarios import (
    DIAGNOSTIC_SCENARIO_RULE_IDS,
    build_priority_ranking,
    summarize_dimension_scores,
)

REPORT_STATUS_PENDING_DOMAIN_REVIEW = "technical_validation_pending_domain_review"
TOP_RANK_LIMIT = 10


def build_diagnostic_ranking_impact_report(
    scenarios: Iterable[TerritoryScenario],
    territory_names: Mapping[str, str],
    *,
    year: int,
    geographic_scope: str,
    comparison_scopes: Iterable[str] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    records = [scenario for scenario in scenarios if scenario.year == year]
    scopes = sorted(
        set(comparison_scopes)
        if comparison_scopes is not None
        else {scenario.comparison_scope for scenario in records}
    )
    timestamp = generated_at or datetime.now(UTC)
    return {
        "status": REPORT_STATUS_PENDING_DOMAIN_REVIEW,
        "generated_at": timestamp.isoformat(),
        "scope": {"year": year, "geographic_scope": geographic_scope},
        "baseline_definition": (
            "Current dimension-capped ranking with the three provisional CAP-01 "
            "diagnostic rules excluded."
        ),
        "candidate_definition": (
            "Current dimension-capped ranking with the three provisional CAP-01 "
            "diagnostic rules included."
        ),
        "diagnostic_rule_ids": sorted(DIAGNOSTIC_SCENARIO_RULE_IDS),
        "comparisons": {
            scope: _build_comparison_impact(
                [scenario for scenario in records if scenario.comparison_scope == scope],
                territory_names,
            )
            for scope in scopes
        },
        "caveats": [
            "This artifact validates deterministic ranking impact, not clinical benefit.",
            "Percentile thresholds are comparative prioritization signals, not Ministry targets.",
            "Thresholds, severity, dimension grouping, and strategies still require domain review.",
        ],
    }


def write_diagnostic_ranking_impact_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    scope = report["scope"]
    scope_slug = str(scope["geographic_scope"]).lower()
    output_path = output_dir / f"diagnostic_ranking_impact_{scope_slug}_{scope['year']}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def _build_comparison_impact(
    scenarios: list[TerritoryScenario], territory_names: Mapping[str, str]
) -> dict[str, Any]:
    baseline_scenarios = [
        scenario for scenario in scenarios if scenario.rule_id not in DIAGNOSTIC_SCENARIO_RULE_IDS
    ]
    diagnostic_scenarios = [
        scenario for scenario in scenarios if scenario.rule_id in DIAGNOSTIC_SCENARIO_RULE_IDS
    ]
    baseline = _ranking_snapshot(baseline_scenarios, territory_names)
    candidate = _ranking_snapshot(scenarios, territory_names)
    diagnostic_rules_by_territory = _diagnostic_rules_by_territory(diagnostic_scenarios)
    changes = _ranking_changes(baseline, candidate, diagnostic_rules_by_territory)
    baseline_top = _top_ranking_rows(baseline)
    candidate_top = _top_ranking_rows(candidate)
    baseline_top_ids = {row["territory_id"] for row in baseline_top}
    candidate_top_ids = {row["territory_id"] for row in candidate_top}

    return {
        "scenario_counts": {
            "baseline": len(baseline_scenarios),
            "candidate": len(scenarios),
            "diagnostic": len(diagnostic_scenarios),
        },
        "territory_counts": {
            "baseline_ranked": len(baseline),
            "candidate_ranked": len(candidate),
            "directly_affected": len(diagnostic_rules_by_territory),
            "newly_ranked": sum(
                1
                for change in changes
                if change["baseline_rank"] is None and change["candidate_rank"] is not None
            ),
            "rank_changed": sum(1 for change in changes if change["rank_changed"]),
            "score_changed": sum(1 for change in changes if change["score_change"] != 0),
        },
        "ranking_impact": {
            "top_10_overlap_count": len(baseline_top_ids & candidate_top_ids),
            "top_10_entered": sorted(candidate_top_ids - baseline_top_ids),
            "top_10_left": sorted(baseline_top_ids - candidate_top_ids),
            "maximum_score_increase": max(
                (float(change["score_change"]) for change in changes), default=0.0
            ),
        },
        "dimension_cap": _dimension_cap_summary(candidate),
        "baseline_top_10": baseline_top,
        "candidate_top_10": candidate_top,
        "changes": changes,
    }


def _ranking_snapshot(
    scenarios: list[TerritoryScenario], territory_names: Mapping[str, str]
) -> dict[tuple[str, int], dict[str, Any]]:
    by_territory: defaultdict[tuple[str, int], list[TerritoryScenario]] = defaultdict(list)
    for scenario in scenarios:
        by_territory[(scenario.territory_id, scenario.year)].append(scenario)

    snapshot: dict[tuple[str, int], dict[str, Any]] = {}
    for rank, (territory_id, year, score, scenario_count) in enumerate(
        build_priority_ranking(scenarios), start=1
    ):
        territory_scenarios = by_territory[(territory_id, year)]
        dimensions = _dimension_rows(territory_scenarios)
        raw_score = round(sum(scenario.score for scenario in territory_scenarios), 4)
        snapshot[(territory_id, year)] = {
            "rank": rank,
            "territory_id": territory_id,
            "territory_name": territory_names.get(territory_id, territory_id),
            "year": year,
            "score": score,
            "raw_scenario_score": raw_score,
            "score_removed_by_dimension_cap": round(raw_score - score, 4),
            "scenario_count": scenario_count,
            "dimension_count": len(dimensions),
            "dimensions": dimensions,
        }
    return snapshot


def _dimension_rows(scenarios: list[TerritoryScenario]) -> list[dict[str, Any]]:
    by_dimension: defaultdict[str, list[TerritoryScenario]] = defaultdict(list)
    for scenario in scenarios:
        by_dimension[scenario.ranking_dimension or scenario.rule_id].append(scenario)

    rows = []
    for dimension_id, dimension_scenarios in sorted(by_dimension.items()):
        contributing_score, _ = summarize_dimension_scores(
            (dimension_id, scenario.score) for scenario in dimension_scenarios
        )
        rows.append(
            {
                "dimension_id": dimension_id,
                "contributing_score": contributing_score,
                "scenario_count": len(dimension_scenarios),
                "rule_ids": sorted({scenario.rule_id for scenario in dimension_scenarios}),
            }
        )
    return rows


def _diagnostic_rules_by_territory(
    scenarios: list[TerritoryScenario],
) -> dict[tuple[str, int], list[str]]:
    rules: defaultdict[tuple[str, int], set[str]] = defaultdict(set)
    for scenario in scenarios:
        rules[(scenario.territory_id, scenario.year)].add(scenario.rule_id)
    return {key: sorted(rule_ids) for key, rule_ids in rules.items()}


def _ranking_changes(
    baseline: Mapping[tuple[str, int], dict[str, Any]],
    candidate: Mapping[tuple[str, int], dict[str, Any]],
    diagnostic_rules: Mapping[tuple[str, int], list[str]],
) -> list[dict[str, Any]]:
    keys = sorted(
        set(baseline) | set(candidate),
        key=lambda key: (
            candidate.get(key, {}).get("rank", float("inf")),
            baseline.get(key, {}).get("rank", float("inf")),
            key,
        ),
    )
    changes = []
    for key in keys:
        baseline_row = baseline.get(key)
        candidate_row = candidate.get(key)
        baseline_rank = baseline_row["rank"] if baseline_row else None
        candidate_rank = candidate_row["rank"] if candidate_row else None
        baseline_score = float(baseline_row["score"]) if baseline_row else 0.0
        candidate_score = float(candidate_row["score"]) if candidate_row else 0.0
        score_change = round(candidate_score - baseline_score, 4)
        rank_changed = baseline_rank != candidate_rank
        if not (rank_changed or score_change or key in diagnostic_rules):
            continue
        source_row = candidate_row or baseline_row
        if source_row is None:
            continue
        changes.append(
            {
                "territory_id": source_row["territory_id"],
                "territory_name": source_row["territory_name"],
                "year": source_row["year"],
                "has_diagnostic_signal": key in diagnostic_rules,
                "diagnostic_rule_ids": diagnostic_rules.get(key, []),
                "baseline_rank": baseline_rank,
                "candidate_rank": candidate_rank,
                "rank_change": (
                    baseline_rank - candidate_rank
                    if baseline_rank is not None and candidate_rank is not None
                    else None
                ),
                "rank_changed": rank_changed,
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "score_change": score_change,
                "baseline_scenario_count": (baseline_row["scenario_count"] if baseline_row else 0),
                "candidate_scenario_count": (
                    candidate_row["scenario_count"] if candidate_row else 0
                ),
                "candidate_dimensions": candidate_row["dimensions"] if candidate_row else [],
            }
        )
    return changes


def _top_ranking_rows(
    snapshot: Mapping[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = sorted(snapshot.values(), key=lambda row: int(row["rank"]))[:TOP_RANK_LIMIT]
    return [
        {
            "rank": row["rank"],
            "territory_id": row["territory_id"],
            "territory_name": row["territory_name"],
            "score": row["score"],
            "scenario_count": row["scenario_count"],
            "dimension_count": row["dimension_count"],
        }
        for row in rows
    ]


def _dimension_cap_summary(
    snapshot: Mapping[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    rows = list(snapshot.values())
    return {
        "aggregation": "maximum scenario score per ranking dimension",
        "territories_with_correlated_scenarios": sum(
            1
            for row in rows
            if any(dimension["scenario_count"] > 1 for dimension in row["dimensions"])
        ),
        "raw_scenario_score_total": round(sum(float(row["raw_scenario_score"]) for row in rows), 4),
        "capped_ranking_score_total": round(sum(float(row["score"]) for row in rows), 4),
        "duplicate_score_excluded": round(
            sum(float(row["score_removed_by_dimension_cap"]) for row in rows), 4
        ),
    }
