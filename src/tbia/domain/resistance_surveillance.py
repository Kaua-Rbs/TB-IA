from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Any

from tbia.domain.models import (
    IndicatorValue,
    ScenarioEvaluationStatus,
    ScenarioRuleEvaluation,
)

RESISTANCE_SURVEILLANCE_SIGNALS = (
    {
        "signal_id": "high_retreatment",
        "rule_id": "high_retreatment",
        "indicator_id": "retreatment_proportion",
        "label": "High retreatment",
        "unit": "percentage",
    },
    {
        "signal_id": "low_culture_use_among_retreatment",
        "rule_id": "low_culture_use_among_retreatment",
        "indicator_id": "culture_use_among_retreatment",
        "label": "Low culture use among pulmonary retreatment cases",
        "unit": "percentage",
    },
    {
        "signal_id": "low_trm_tb_use",
        "rule_id": "low_trm_tb_use",
        "indicator_id": "trm_tb_use_proportion",
        "label": "Low rapid molecular test use",
        "unit": "percentage",
    },
)


def build_resistance_surveillance_profile(
    indicator_values: Sequence[IndicatorValue],
    evaluations: Sequence[ScenarioRuleEvaluation],
    triggered_rule_ids: Collection[str],
    *,
    comparison_scope: str,
) -> dict[str, Any]:
    indicators_by_id = {value.indicator_id: value for value in indicator_values}
    evaluations_by_rule = {evaluation.rule_id: evaluation for evaluation in evaluations}
    return {
        "interpretation": "surveillance_gap_not_confirmed_burden",
        "confirmed_resistance_status": ("not_available_in_public_aggregate_sources"),
        "review_status": "pending_domain_review",
        "ranking_effect": "none",
        "comparison_scope": comparison_scope,
        "signals": [
            resistance_surveillance_signal(
                definition,
                indicators_by_id.get(str(definition["indicator_id"])),
                evaluations_by_rule.get(str(definition["rule_id"])),
                triggered_rule_ids,
            )
            for definition in RESISTANCE_SURVEILLANCE_SIGNALS
        ],
    }


def resistance_surveillance_signal(
    definition: dict[str, str],
    indicator: IndicatorValue | None,
    evaluation: ScenarioRuleEvaluation | None,
    triggered_rule_ids: Collection[str],
) -> dict[str, Any]:
    data_status = indicator_data_status(indicator)
    rule_id = definition["rule_id"]
    trigger_status = resistance_trigger_status(rule_id, data_status, evaluation, triggered_rule_ids)
    is_suppressed = indicator is not None and indicator.is_suppressed
    return {
        **definition,
        "data_status": data_status,
        "evaluation_status": (
            evaluation.status.value if evaluation is not None else "not_evaluated"
        ),
        "trigger_status": trigger_status,
        "value": (
            indicator.value if indicator is not None and data_status == "available" else None
        ),
        "numerator_value": (
            indicator.numerator_value if indicator is not None and not is_suppressed else None
        ),
        "denominator_value": (
            indicator.denominator_value if indicator is not None and not is_suppressed else None
        ),
        "threshold_value": (evaluation.threshold_value if evaluation is not None else None),
        "coverage_ratio": (evaluation.coverage_ratio if evaluation is not None else None),
        "source_ids": list(indicator.source_ids) if indicator is not None else [],
        "source_provenance": (
            [
                {
                    "source_id": source.source_id,
                    "reference_year": source.reference_year,
                    "release_status": source.release_status,
                    "dataset_kind": source.dataset_kind,
                    "artifact_sha256": source.artifact_sha256,
                }
                for source in indicator.source_provenance
            ]
            if indicator is not None
            else []
        ),
        "caveats": indicator.caveats if indicator is not None else "",
    }


def indicator_data_status(indicator: IndicatorValue | None) -> str:
    if indicator is None or indicator.value is None and not indicator.is_suppressed:
        return "missing"
    if indicator.is_suppressed:
        return "suppressed"
    return "available"


def resistance_trigger_status(
    rule_id: str,
    data_status: str,
    evaluation: ScenarioRuleEvaluation | None,
    triggered_rule_ids: Collection[str],
) -> str:
    if (
        data_status != "available"
        or evaluation is None
        or evaluation.status is not ScenarioEvaluationStatus.READY
    ):
        return "not_evaluable"
    return "triggered" if rule_id in triggered_rule_ids else "not_triggered"
