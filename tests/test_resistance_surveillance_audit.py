from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from tbia.domain.resistance_surveillance_audit import (
    REPORT_STATUS_FAILED,
    REPORT_STATUS_PENDING_DOMAIN_REVIEW,
    build_resistance_surveillance_audit,
    write_resistance_surveillance_audit,
)


def test_resistance_surveillance_audit_summarizes_overlap_and_provenance(
    tmp_path: Path,
) -> None:
    report = build_resistance_surveillance_audit(
        {
            "uf": {
                "2304400": profile(
                    triggered={
                        "high_retreatment",
                        "low_culture_use_among_retreatment",
                    }
                ),
                "2303709": profile(triggered=set(), with_provenance=False),
            }
        },
        ["2304400", "2303709"],
        year=2023,
        geographic_scope="CE",
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert report["status"] == REPORT_STATUS_PENDING_DOMAIN_REVIEW
    assert report["structural_violation_count"] == 0
    comparison = report["comparisons"]["uf"]
    assert comparison["profile_count"] == 2
    assert comparison["overlap"]["triggered_territory_count"] == 1
    assert comparison["overlap"]["multiple_triggered_territory_count"] == 1
    assert comparison["provenance"]["available_signal_count"] == 6
    assert comparison["provenance"]["available_without_provenance_count"] == 3
    assert comparison["provenance"]["source_occurrences"] == {"sinan_tb": 3}
    assert comparison["ranking_guard"]["violating_profile_count"] == 0

    output_path = write_resistance_surveillance_audit(report, tmp_path)
    assert output_path.name == "resistance_surveillance_audit_ce_2023.json"
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["generated_at"] == "2026-07-21T00:00:00+00:00"


def test_resistance_surveillance_audit_fails_closed_on_structural_claims() -> None:
    unsafe_profile = profile(triggered=set())
    unsafe_profile["ranking_effect"] = "adds_score"
    unsafe_profile["confirmed_resistance_status"] = "confirmed_public_burden"

    report = build_resistance_surveillance_audit(
        {"uf": {"2304400": unsafe_profile}},
        ["2304400", "2303709"],
        year=2023,
        geographic_scope="CE",
    )

    assert report["status"] == REPORT_STATUS_FAILED
    codes = {row["code"] for row in report["structural_violations"]}
    assert codes == {
        "missing_territory_profiles",
        "ranking_effect_not_none",
        "public_confirmed_resistance_claim",
    }


def test_resistance_surveillance_audit_rejects_empty_scope() -> None:
    report = build_resistance_surveillance_audit(
        {"uf": {}},
        [],
        year=2023,
        geographic_scope="CE",
    )

    assert report["status"] == REPORT_STATUS_FAILED
    assert report["structural_violations"] == [{"code": "empty_territorial_scope"}]


def profile(
    *,
    triggered: set[str],
    with_provenance: bool = True,
) -> dict[str, object]:
    signal_ids = (
        "high_retreatment",
        "low_culture_use_among_retreatment",
        "low_trm_tb_use",
    )
    provenance = (
        [
            {
                "source_id": "sinan_tb",
                "reference_year": 2023,
                "release_status": "final",
                "dataset_kind": "notification",
                "artifact_sha256": "abc123",
            }
        ]
        if with_provenance
        else []
    )
    return {
        "interpretation": "surveillance_gap_not_confirmed_burden",
        "confirmed_resistance_status": ("not_available_in_public_aggregate_sources"),
        "review_status": "pending_domain_review",
        "ranking_effect": "none",
        "comparison_scope": "uf",
        "signals": [
            {
                "signal_id": signal_id,
                "rule_id": signal_id,
                "indicator_id": signal_id,
                "data_status": "available",
                "evaluation_status": "ready",
                "trigger_status": ("triggered" if signal_id in triggered else "not_triggered"),
                "source_provenance": provenance,
            }
            for signal_id in signal_ids
        ],
    }
