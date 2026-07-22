from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_STATUS_PENDING_DOMAIN_REVIEW = "technical_validation_pending_domain_review"
REPORT_STATUS_FAILED = "failed"
EXPECTED_SIGNAL_IDS = frozenset(
    {
        "high_retreatment",
        "low_culture_use_among_retreatment",
        "low_trm_tb_use",
    }
)
EXPECTED_CONFIRMED_STATUS = "not_available_in_public_aggregate_sources"


def build_resistance_surveillance_audit(
    profiles_by_scope: Mapping[str, Mapping[str, Mapping[str, Any]]],
    territory_ids: Sequence[str],
    *,
    year: int,
    geographic_scope: str,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    expected_territories = set(territory_ids)
    comparisons: dict[str, Any] = {}
    violations: list[dict[str, Any]] = []
    if not expected_territories:
        violations.append({"code": "empty_territorial_scope"})
    if not profiles_by_scope:
        violations.append({"code": "missing_comparison_scopes"})
    for comparison_scope, profiles in sorted(profiles_by_scope.items()):
        comparison, comparison_violations = summarize_comparison_scope(
            profiles,
            expected_territories,
            comparison_scope=comparison_scope,
        )
        comparisons[comparison_scope] = comparison
        violations.extend(comparison_violations)

    return {
        "status": (REPORT_STATUS_FAILED if violations else REPORT_STATUS_PENDING_DOMAIN_REVIEW),
        "generated_at": (generated_at or datetime.now(UTC)).isoformat(),
        "scope": {
            "year": year,
            "geographic_scope": geographic_scope,
            "comparison_scopes": sorted(profiles_by_scope),
        },
        "interpretation": "surveillance_gap_not_confirmed_burden",
        "confirmed_resistance_status": EXPECTED_CONFIRMED_STATUS,
        "ranking_effect": "none",
        "comparisons": comparisons,
        "structural_violation_count": len(violations),
        "structural_violations": violations,
        "caveats": [
            (
                "This artifact audits public surveillance signals and data "
                "readiness, not confirmed drug-resistant TB burden."
            ),
            (
                "Triggered signals are comparative prioritization outputs, not "
                "diagnostic findings or Ministry performance targets."
            ),
            (
                "Clinical meaning, action thresholds, and governance decisions "
                "remain pending health-domain review."
            ),
        ],
    }


def comparison_profile_set_violations(
    profiles: Mapping[str, Mapping[str, Any]],
    expected_territories: set[str],
    comparison_scope: str,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    missing_profiles = sorted(expected_territories - set(profiles))
    unexpected_profiles = sorted(set(profiles) - expected_territories)
    if missing_profiles:
        violations.append(
            {
                "code": "missing_territory_profiles",
                "comparison_scope": comparison_scope,
                "territory_ids": missing_profiles,
            }
        )
    if unexpected_profiles:
        violations.append(
            {
                "code": "unexpected_territory_profiles",
                "comparison_scope": comparison_scope,
                "territory_ids": unexpected_profiles,
            }
        )
    return violations


def normalized_profile_signals(
    profile: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    signals = profile.get("signals", [])
    if not isinstance(signals, list):
        return []
    return [signal for signal in signals if isinstance(signal, Mapping)]


def empty_signal_summaries() -> dict[str, dict[str, Counter[str]]]:
    return {
        signal_id: {
            "data_status": Counter(),
            "evaluation_status": Counter(),
            "trigger_status": Counter(),
        }
        for signal_id in sorted(EXPECTED_SIGNAL_IDS)
    }


def record_signal_audit(
    signal: Mapping[str, Any],
    signal_summaries: dict[str, dict[str, Counter[str]]],
    provenance_sources: Counter[str],
) -> tuple[str | None, int, int]:
    signal_id = str(signal.get("signal_id", ""))
    summary = signal_summaries.get(signal_id)
    if summary is None:
        return None, 0, 0

    for status_key in ("data_status", "evaluation_status", "trigger_status"):
        summary[status_key][str(signal.get(status_key, "unknown"))] += 1

    data_status = str(signal.get("data_status", "unknown"))
    if data_status != "available":
        return signal_id, 0, 0
    source_provenance = signal.get("source_provenance", [])
    if not isinstance(source_provenance, list) or not source_provenance:
        return signal_id, 1, 1
    for source in source_provenance:
        if isinstance(source, Mapping):
            provenance_sources[str(source.get("source_id", "unknown"))] += 1
    return signal_id, 1, 0


def collect_signal_audit(
    profiles: Mapping[str, Mapping[str, Any]],
    comparison_scope: str,
) -> tuple[
    dict[str, dict[str, Counter[str]]],
    Counter[str],
    int,
    int,
    Counter[tuple[str, ...]],
    list[dict[str, Any]],
]:
    signal_summaries = empty_signal_summaries()
    provenance_sources: Counter[str] = Counter()
    available_signal_count = 0
    available_without_provenance_count = 0
    triggered_combinations: Counter[tuple[str, ...]] = Counter()
    violations: list[dict[str, Any]] = []
    unexpected_signal_territories: list[str] = []

    for territory_id, profile in sorted(profiles.items()):
        violations.extend(
            profile_guard_violations(
                territory_id,
                profile,
                comparison_scope=comparison_scope,
            )
        )
        signals = normalized_profile_signals(profile)
        if {str(signal.get("signal_id")) for signal in signals} != EXPECTED_SIGNAL_IDS:
            unexpected_signal_territories.append(territory_id)

        triggered_ids: list[str] = []
        for signal in signals:
            signal_id, available_increment, missing_provenance_increment = record_signal_audit(
                signal,
                signal_summaries,
                provenance_sources,
            )
            available_signal_count += available_increment
            available_without_provenance_count += missing_provenance_increment
            if signal_id is not None and signal.get("trigger_status") == "triggered":
                triggered_ids.append(signal_id)
        triggered_combinations[tuple(sorted(triggered_ids))] += 1

    if unexpected_signal_territories:
        violations.append(
            {
                "code": "unexpected_signal_set",
                "comparison_scope": comparison_scope,
                "territory_ids": sorted(unexpected_signal_territories),
            }
        )
    return (
        signal_summaries,
        provenance_sources,
        available_signal_count,
        available_without_provenance_count,
        triggered_combinations,
        violations,
    )


def summarize_comparison_scope(
    profiles: Mapping[str, Mapping[str, Any]],
    expected_territories: set[str],
    *,
    comparison_scope: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    violations = comparison_profile_set_violations(
        profiles,
        expected_territories,
        comparison_scope,
    )
    (
        signal_summaries,
        provenance_sources,
        available_signal_count,
        available_without_provenance_count,
        triggered_combinations,
        signal_violations,
    ) = collect_signal_audit(profiles, comparison_scope)
    violations.extend(signal_violations)

    combination_rows = [
        {
            "triggered_signal_ids": list(signal_ids),
            "territory_count": count,
        }
        for signal_ids, count in sorted(triggered_combinations.items())
    ]
    triggered_territory_count = sum(
        count for signal_ids, count in triggered_combinations.items() if signal_ids
    )
    multiple_triggered_territory_count = sum(
        count for signal_ids, count in triggered_combinations.items() if len(signal_ids) > 1
    )
    return (
        {
            "comparison_scope": comparison_scope,
            "expected_territory_count": len(expected_territories),
            "profile_count": len(profiles),
            "signal_summaries": [
                {
                    "signal_id": signal_id,
                    "data_status": dict(sorted(summary["data_status"].items())),
                    "evaluation_status": dict(sorted(summary["evaluation_status"].items())),
                    "trigger_status": dict(sorted(summary["trigger_status"].items())),
                }
                for signal_id, summary in signal_summaries.items()
            ],
            "overlap": {
                "triggered_territory_count": triggered_territory_count,
                "multiple_triggered_territory_count": (multiple_triggered_territory_count),
                "combinations": combination_rows,
            },
            "provenance": {
                "available_signal_count": available_signal_count,
                "available_without_provenance_count": (available_without_provenance_count),
                "source_occurrences": dict(sorted(provenance_sources.items())),
            },
            "ranking_guard": {
                "expected_effect": "none",
                "violating_profile_count": sum(
                    1 for profile in profiles.values() if profile.get("ranking_effect") != "none"
                ),
            },
            "confirmed_resistance_guard": {
                "expected_status": EXPECTED_CONFIRMED_STATUS,
                "violating_profile_count": sum(
                    1
                    for profile in profiles.values()
                    if profile.get("confirmed_resistance_status") != EXPECTED_CONFIRMED_STATUS
                ),
            },
        },
        violations,
    )


def profile_guard_violations(
    territory_id: str,
    profile: Mapping[str, Any],
    *,
    comparison_scope: str,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if profile.get("ranking_effect") != "none":
        violations.append(
            {
                "code": "ranking_effect_not_none",
                "comparison_scope": comparison_scope,
                "territory_id": territory_id,
                "actual": profile.get("ranking_effect"),
            }
        )
    if profile.get("confirmed_resistance_status") != EXPECTED_CONFIRMED_STATUS:
        violations.append(
            {
                "code": "public_confirmed_resistance_claim",
                "comparison_scope": comparison_scope,
                "territory_id": territory_id,
                "actual": profile.get("confirmed_resistance_status"),
            }
        )
    return violations


def write_resistance_surveillance_audit(report: Mapping[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    scope = report["scope"]
    scope_slug = str(scope["geographic_scope"]).lower()
    output_path = output_dir / f"resistance_surveillance_audit_{scope_slug}_{scope['year']}.json"
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
