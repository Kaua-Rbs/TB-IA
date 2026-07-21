from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from tbia.ingest.datasus import read_datasus_records
from tbia.ingest.datasus_transforms import record_text, record_year

Record = Mapping[str, Any]

REPORT_STATUS_PENDING_REVIEW = "technical_audit_pending_domain_review"
REPORT_STATUS_RECONCILIATION_REQUIRED = "technical_reconciliation_required"
REPORT_STATUS_INVALID_SOURCE = "invalid_source"
CONTACT_MANIFEST_FILENAME = "sinan_contact_audit_ce_2018_2024.json"

REQUIRED_CONTACT_FIELDS = (
    "NU_ANO",
    "ID_MN_RESI",
    "TRATAMENTO",
    "FORMA",
    "SITUA_ENCE",
    "BACILOSC_E",
    "BACILOS_E2",
    "CULTURA_ES",
    "TEST_MOLEC",
    "NU_CONTATO",
    "NU_COMU_EX",
)
NEW_CASE_ENTRY_TYPES = frozenset({"1", "4", "6"})
PULMONARY_FORMS = frozenset({"1", "3"})
DIAGNOSIS_CHANGE_CLOSURE = "6"
TRM_TB_DETECTED_RESULTS = frozenset({"1", "2"})


def load_contact_audit_manifest() -> dict[str, Any]:
    resource = files("tbia").joinpath("resources", "validation", CONTACT_MANIFEST_FILENAME)
    parsed = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("SINAN contact audit manifest must contain an object")
    return cast(dict[str, Any], parsed)


def build_cached_sinan_contact_audit(
    *,
    raw_dir: Path,
    uf: str,
    uf_code: str,
    year_from: int,
    year_to: int,
    manifest: Mapping[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    active_manifest = manifest or load_contact_audit_manifest()
    annual_reports: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    headline_names = manifest_headline_names(active_manifest)

    for year in range(year_from, year_to + 1):
        source_path = select_cached_sinan_path(raw_dir, year)
        source_report = build_source_artifact_report(
            source_path,
            year=year,
            manifest=active_manifest,
        )
        source_artifacts.append(source_report)
        if source_path is None:
            annual_reports.append(missing_source_year_report(year))
            continue
        records = read_datasus_records(source_path)
        annual_reports.append(
            build_contact_year_report(
                records,
                year=year,
                uf_code=uf_code,
                headline_names=headline_names,
            )
        )

    return build_contact_audit_report(
        annual_reports,
        source_artifacts,
        manifest=active_manifest,
        uf=uf,
        uf_code=uf_code,
        year_from=year_from,
        year_to=year_to,
        generated_at=generated_at,
    )


def select_cached_sinan_path(raw_dir: Path, year: int) -> Path | None:
    sample_dir = raw_dir / "datasus_samples"
    for suffix in ("dbf", "dbc"):
        candidate = sample_dir / f"sinan_tb_br_{year}.{suffix}"
        if candidate.exists():
            return candidate
    return None


def build_source_artifact_report(
    path: Path | None,
    *,
    year: int,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    expected_rows = [
        item
        for item in cast(Sequence[Mapping[str, Any]], manifest.get("source_artifacts", ()))
        if int(item["year"]) == year
    ]
    if path is None:
        return {
            "year": year,
            "filename": None,
            "sha256": None,
            "matches_manifest": False,
            "expected_artifacts": [dict(item) for item in expected_rows],
        }
    actual_hash = file_sha256(path)
    matches = any(
        str(item["filename"]) == path.name and str(item["sha256"]) == actual_hash
        for item in expected_rows
    )
    return {
        "year": year,
        "filename": path.name,
        "sha256": actual_hash,
        "matches_manifest": matches,
        "expected_artifacts": [dict(item) for item in expected_rows],
    }


def build_contact_year_report(
    records: Sequence[Record],
    *,
    year: int,
    uf_code: str,
    headline_names: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    observed_fields = {field for record in records for field in record}
    missing_fields = sorted(set(REQUIRED_CONTACT_FIELDS) - observed_fields)
    year_records = [record for record in records if record_year(record.get("NU_ANO")) == year]
    scope_records = [
        record
        for record in year_records
        if municipality_in_scope(record_text(record, "ID_MN_RESI"), uf_code)
    ]
    candidate_universe = [
        record
        for record in scope_records
        if record_text(record, "TRATAMENTO") in NEW_CASE_ENTRY_TYPES
        and record_text(record, "FORMA") in PULMONARY_FORMS
        and record_text(record, "SITUA_ENCE") != DIAGNOSIS_CHANGE_CLOSURE
    ]
    eligible_records = [
        record for record in candidate_universe if has_candidate_lab_confirmation(record)
    ]

    if missing_fields:
        return invalid_fields_year_report(
            year,
            source_record_count=len(records),
            year_record_count=len(year_records),
            scope_record_count=len(scope_records),
            missing_fields=missing_fields,
        )

    total_metrics = empty_contact_metrics()
    municipality_metrics: defaultdict[str, dict[str, int]] = defaultdict(empty_contact_metrics)
    for record in eligible_records:
        municipality_code = record_text(record, "ID_MN_RESI")
        update_contact_metrics(total_metrics, record)
        update_contact_metrics(municipality_metrics[municipality_code], record)

    summary = finalize_contact_metrics(total_metrics)
    names = headline_names or {}
    municipalities = [
        {
            "municipality_code": municipality_code,
            "territory_name": names.get(municipality_code),
            **finalize_contact_metrics(metrics),
        }
        for municipality_code, metrics in sorted(municipality_metrics.items())
    ]
    reasons = year_reconciliation_reasons(summary, municipalities)
    status = (
        REPORT_STATUS_INVALID_SOURCE
        if summary["invalid_value_count"] > 0
        else (REPORT_STATUS_RECONCILIATION_REQUIRED if reasons else REPORT_STATUS_PENDING_REVIEW)
    )
    return {
        "year": year,
        "status": status,
        "status_reasons": reasons,
        "missing_required_fields": [],
        "selection": {
            "source_record_count": len(records),
            "year_record_count": len(year_records),
            "scope_record_count": len(scope_records),
            "candidate_universe_count": len(candidate_universe),
            "eligible_case_count": len(eligible_records),
            "blank_closure_count": sum(
                not record_text(record, "SITUA_ENCE") for record in candidate_universe
            ),
        },
        "lab_confirmation_components": {
            "initial_smear_positive": sum(
                record_text(record, "BACILOSC_E") == "1" for record in candidate_universe
            ),
            "second_smear_positive": sum(
                record_text(record, "BACILOS_E2") == "1" for record in candidate_universe
            ),
            "culture_positive": sum(
                record_text(record, "CULTURA_ES") == "1" for record in candidate_universe
            ),
            "trm_tb_detected": sum(
                record_text(record, "TEST_MOLEC") in TRM_TB_DETECTED_RESULTS
                for record in candidate_universe
            ),
        },
        "summary": summary,
        "municipalities": municipalities,
    }


def municipality_in_scope(municipality_code: str, uf_code: str) -> bool:
    return bool(municipality_code) and (not uf_code or municipality_code.startswith(uf_code))


def has_candidate_lab_confirmation(record: Record) -> bool:
    return (
        record_text(record, "BACILOSC_E") == "1"
        or record_text(record, "BACILOS_E2") == "1"
        or record_text(record, "CULTURA_ES") == "1"
        or record_text(record, "TEST_MOLEC") in TRM_TB_DETECTED_RESULTS
    )


def empty_contact_metrics() -> dict[str, int]:
    return {
        "eligible_case_count": 0,
        "identified_present_count": 0,
        "examined_present_count": 0,
        "complete_pair_count": 0,
        "missing_identified_count": 0,
        "missing_examined_count": 0,
        "invalid_identified_count": 0,
        "invalid_examined_count": 0,
        "zero_identified_count": 0,
        "examined_above_identified_count": 0,
        "examined_without_identified_count": 0,
        "recorded_identified_sum": 0,
        "recorded_examined_sum": 0,
        "complete_pair_identified_sum": 0,
        "complete_pair_examined_sum": 0,
    }


def update_contact_metrics(metrics: dict[str, int], record: Record) -> None:
    metrics["eligible_case_count"] += 1
    identified, identified_error = parse_contact_count(record.get("NU_CONTATO"))
    examined, examined_error = parse_contact_count(record.get("NU_COMU_EX"))

    update_single_count(
        metrics,
        value=identified,
        error=identified_error,
        kind="identified",
    )
    update_single_count(
        metrics,
        value=examined,
        error=examined_error,
        kind="examined",
    )
    if identified is not None and identified_error is None:
        metrics["recorded_identified_sum"] += identified
        if identified == 0:
            metrics["zero_identified_count"] += 1
    if examined is not None and examined_error is None:
        metrics["recorded_examined_sum"] += examined

    if (
        identified is not None
        and examined is not None
        and identified_error is None
        and examined_error is None
    ):
        metrics["complete_pair_count"] += 1
        metrics["complete_pair_identified_sum"] += identified
        metrics["complete_pair_examined_sum"] += examined
        if examined > identified:
            metrics["examined_above_identified_count"] += 1
    if (
        examined is not None
        and examined > 0
        and examined_error is None
        and (identified is None or identified == 0 or identified_error is not None)
    ):
        metrics["examined_without_identified_count"] += 1


def update_single_count(
    metrics: dict[str, int],
    *,
    value: int | None,
    error: str | None,
    kind: str,
) -> None:
    if error is not None:
        metrics[f"invalid_{kind}_count"] += 1
    elif value is None:
        metrics[f"missing_{kind}_count"] += 1
    else:
        metrics[f"{kind}_present_count"] += 1


def parse_contact_count(value: object) -> tuple[int | None, str | None]:
    if value is None:
        return None, None
    text = str(value).strip()
    if not text:
        return None, None
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        return None, "not_numeric"
    if not parsed.is_finite():
        return None, "not_finite"
    if parsed < 0:
        return None, "negative"
    integral = parsed.to_integral_value()
    if parsed != integral:
        return None, "not_integer"
    return int(integral), None


def finalize_contact_metrics(metrics: Mapping[str, int]) -> dict[str, Any]:
    recorded_identified = metrics["recorded_identified_sum"]
    recorded_examined = metrics["recorded_examined_sum"]
    pair_identified = metrics["complete_pair_identified_sum"]
    pair_examined = metrics["complete_pair_examined_sum"]
    return {
        **dict(metrics),
        "invalid_value_count": (
            metrics["invalid_identified_count"] + metrics["invalid_examined_count"]
        ),
        "recorded_values": aggregate_result(recorded_identified, recorded_examined),
        "complete_pairs": aggregate_result(pair_identified, pair_examined),
    }


def aggregate_result(identified: int, examined: int) -> dict[str, int | float | None]:
    return {
        "identified_contacts": identified,
        "examined_contacts": examined,
        "proportion": round(examined / identified * 100, 6) if identified > 0 else None,
    }


def year_reconciliation_reasons(
    summary: Mapping[str, Any],
    municipalities: Sequence[Mapping[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    if summary["missing_identified_count"] or summary["missing_examined_count"]:
        reasons.append("missing_contact_values")
    if summary["invalid_value_count"]:
        reasons.append("invalid_contact_values")
    if summary["examined_above_identified_count"]:
        reasons.append("case_examined_above_identified")
    if summary["examined_without_identified_count"]:
        reasons.append("examined_without_identified")
    if any(
        municipality["recorded_values"]["examined_contacts"]
        > municipality["recorded_values"]["identified_contacts"]
        for municipality in municipalities
    ):
        reasons.append("municipality_examined_above_identified")
    return reasons


def build_contact_audit_report(
    annual_reports: Sequence[dict[str, Any]],
    source_artifacts: Sequence[dict[str, Any]],
    *,
    manifest: Mapping[str, Any],
    uf: str,
    uf_code: str,
    year_from: int,
    year_to: int,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    benchmark_comparisons = build_benchmark_comparisons(
        annual_reports,
        manifest=manifest,
        uf=uf,
        year_from=year_from,
        year_to=year_to,
    )
    headline_acceptance = build_headline_acceptance(
        annual_reports,
        manifest=manifest,
    )
    reasons: list[str] = []
    invalid_source = any(
        report["status"] == REPORT_STATUS_INVALID_SOURCE for report in annual_reports
    )
    if invalid_source:
        reasons.append("invalid_or_missing_source")
    if any(not artifact["matches_manifest"] for artifact in source_artifacts):
        reasons.append("source_artifact_mismatch")
    if any(report["status_reasons"] for report in annual_reports):
        reasons.append("annual_data_quality_requires_reconciliation")
    if any(not comparison["matches_official"] for comparison in benchmark_comparisons):
        reasons.append("official_benchmark_mismatch")
    if any(not item["matches_fixture"] for item in headline_acceptance):
        reasons.append("headline_acceptance_mismatch")

    if invalid_source:
        status = REPORT_STATUS_INVALID_SOURCE
    elif reasons:
        status = REPORT_STATUS_RECONCILIATION_REQUIRED
    else:
        status = REPORT_STATUS_PENDING_REVIEW

    timestamp = generated_at or datetime.now(UTC)
    return {
        "status": status,
        "status_reasons": reasons,
        "review_status": manifest.get(
            "review_status",
            "technical_acceptance_pending_domain_review",
        ),
        "generated_at": timestamp.isoformat(),
        "manifest_id": manifest.get("manifest_id"),
        "scope": {
            "uf": uf.upper(),
            "uf_code": uf_code,
            "year_from": year_from,
            "year_to": year_to,
        },
        "candidate_contract": dict(cast(Mapping[str, Any], manifest.get("candidate_contract", {}))),
        "source_artifacts": list(source_artifacts),
        "annual_reports": list(annual_reports),
        "official_benchmark_comparisons": benchmark_comparisons,
        "headline_acceptance": headline_acceptance,
        "caveats": [
            "This report is a technical audit, not approval of a public indicator.",
            (
                "Recorded-value and complete-pair sums are both evidence; "
                "neither resolves missingness."
            ),
            "No individual SINAN record is persisted in the report.",
            "No contact result contributes to indicators, scenarios, ranking, API, or frontend.",
            "The synthetic municipal pending-contact alert remains a separate governed workflow.",
        ],
    }


def build_benchmark_comparisons(
    annual_reports: Sequence[Mapping[str, Any]],
    *,
    manifest: Mapping[str, Any],
    uf: str,
    year_from: int,
    year_to: int,
) -> list[dict[str, Any]]:
    reports_by_year = {int(report["year"]): report for report in annual_reports}
    comparisons: list[dict[str, Any]] = []
    for benchmark in cast(
        Sequence[Mapping[str, Any]],
        manifest.get("official_benchmarks", ()),
    ):
        year = int(benchmark["year"])
        if str(benchmark["uf"]).upper() != uf.upper() or not year_from <= year <= year_to:
            continue
        annual = reports_by_year.get(year)
        actual = (
            cast(Mapping[str, Any], annual["summary"])["recorded_values"]
            if annual is not None and "summary" in annual
            else None
        )
        expected_identified = int(benchmark["identified_contacts"])
        expected_examined = int(benchmark["examined_contacts"])
        actual_identified = (
            int(cast(Mapping[str, Any], actual)["identified_contacts"])
            if actual is not None
            else None
        )
        actual_examined = (
            int(cast(Mapping[str, Any], actual)["examined_contacts"])
            if actual is not None
            else None
        )
        matches = actual_identified == expected_identified and actual_examined == expected_examined
        comparisons.append(
            {
                "year": year,
                "publication": benchmark["publication"],
                "reference": benchmark["reference"],
                "expected": {
                    "identified_contacts": expected_identified,
                    "examined_contacts": expected_examined,
                    "proportion": benchmark["proportion"],
                },
                "actual": actual,
                "difference": {
                    "identified_contacts": (
                        actual_identified - expected_identified
                        if actual_identified is not None
                        else None
                    ),
                    "examined_contacts": (
                        actual_examined - expected_examined if actual_examined is not None else None
                    ),
                },
                "matches_official": matches,
            }
        )
    return comparisons


def manifest_headline_names(manifest: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(item["municipality_code"]): str(item["territory_name"])
        for item in cast(
            Sequence[Mapping[str, Any]],
            manifest.get("headline_municipalities", ()),
        )
    }


def build_headline_acceptance(
    annual_reports: Sequence[Mapping[str, Any]],
    *,
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    reports_by_year = {int(report["year"]): report for report in annual_reports}
    results: list[dict[str, Any]] = []
    for expected in cast(
        Sequence[Mapping[str, Any]],
        manifest.get("headline_municipalities", ()),
    ):
        if "expected" not in expected:
            continue
        year = int(expected["year"])
        annual = reports_by_year.get(year)
        municipality_code = str(expected["municipality_code"])
        municipalities = (
            cast(Sequence[Mapping[str, Any]], annual.get("municipalities", ()))
            if annual is not None
            else ()
        )
        actual = next(
            (
                municipality
                for municipality in municipalities
                if municipality["municipality_code"] == municipality_code
            ),
            None,
        )
        expected_values = cast(Mapping[str, Any], expected["expected"])
        matches = actual is not None and all(
            actual[field] == value for field, value in expected_values.items()
        )
        results.append(
            {
                "year": year,
                "municipality_code": municipality_code,
                "territory_id": expected["territory_id"],
                "territory_name": expected["territory_name"],
                "expected": dict(expected_values),
                "actual": actual,
                "matches_fixture": matches,
            }
        )
    return results


def missing_source_year_report(year: int) -> dict[str, Any]:
    return {
        "year": year,
        "status": REPORT_STATUS_INVALID_SOURCE,
        "status_reasons": ["source_file_missing"],
        "missing_required_fields": list(REQUIRED_CONTACT_FIELDS),
        "selection": empty_selection(),
        "lab_confirmation_components": empty_lab_components(),
        "municipalities": [],
    }


def invalid_fields_year_report(
    year: int,
    *,
    source_record_count: int,
    year_record_count: int,
    scope_record_count: int,
    missing_fields: Sequence[str],
) -> dict[str, Any]:
    selection = empty_selection()
    selection.update(
        {
            "source_record_count": source_record_count,
            "year_record_count": year_record_count,
            "scope_record_count": scope_record_count,
        }
    )
    return {
        "year": year,
        "status": REPORT_STATUS_INVALID_SOURCE,
        "status_reasons": ["required_fields_missing"],
        "missing_required_fields": list(missing_fields),
        "selection": selection,
        "lab_confirmation_components": empty_lab_components(),
        "municipalities": [],
    }


def empty_selection() -> dict[str, int]:
    return {
        "source_record_count": 0,
        "year_record_count": 0,
        "scope_record_count": 0,
        "candidate_universe_count": 0,
        "eligible_case_count": 0,
        "blank_closure_count": 0,
    }


def empty_lab_components() -> dict[str, int]:
    return {
        "initial_smear_positive": 0,
        "second_smear_positive": 0,
        "culture_positive": 0,
        "trm_tb_detected": 0,
    }


def write_sinan_contact_audit_report(report: Mapping[str, Any], output_dir: Path) -> Path:
    scope = cast(Mapping[str, Any], report["scope"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (
        "sinan_contact_investigation_"
        f"{str(scope['uf']).lower()}_{scope['year_from']}_{scope['year_to']}.json"
    )
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
