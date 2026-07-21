from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from tbia import cli
from tbia.cli import app
from tbia.ingest import sinan_contacts_validation
from tbia.ingest.sinan_contacts_validation import (
    REPORT_STATUS_INVALID_SOURCE,
    REPORT_STATUS_PENDING_REVIEW,
    REPORT_STATUS_RECONCILIATION_REQUIRED,
    build_cached_sinan_contact_audit,
    build_contact_year_report,
    load_contact_audit_manifest,
    parse_contact_count,
)


def contact_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "NU_ANO": "2024",
        "ID_MN_RESI": "230440",
        "TRATAMENTO": "1",
        "FORMA": "1",
        "SITUA_ENCE": "1",
        "BACILOSC_E": "1",
        "BACILOS_E2": "2",
        "CULTURA_ES": "2",
        "TEST_MOLEC": "3",
        "NU_CONTATO": 2,
        "NU_COMU_EX": 1,
    }
    record.update(overrides)
    return record


def audit_manifest(source_hash: str, *, expected_examined: int = 1) -> dict[str, Any]:
    return {
        "manifest_id": "test_contact_audit",
        "review_status": "technical_acceptance_pending_domain_review",
        "candidate_contract": {"name": "candidate"},
        "source_artifacts": [
            {
                "year": 2024,
                "filename": "sinan_tb_br_2024.dbc",
                "sha256": source_hash,
            }
        ],
        "official_benchmarks": [
            {
                "uf": "CE",
                "year": 2024,
                "identified_contacts": 2,
                "examined_contacts": expected_examined,
                "proportion": expected_examined / 2 * 100,
                "publication": "Official fixture",
                "reference": "https://example.test/official",
            }
        ],
        "headline_municipalities": [],
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, (None, None)),
        ("", (None, None)),
        ("  ", (None, None)),
        (0, (0, None)),
        ("7", (7, None)),
        (3.0, (3, None)),
        (-1, (None, "negative")),
        ("1.5", (None, "not_integer")),
        ("invalid", (None, "not_numeric")),
    ],
)
def test_parse_contact_count_distinguishes_missing_and_invalid(
    value: object,
    expected: tuple[int | None, str | None],
) -> None:
    assert parse_contact_count(value) == expected


@pytest.mark.parametrize(
    "confirmation_fields",
    [
        {"BACILOSC_E": "1"},
        {"BACILOS_E2": "1"},
        {"CULTURA_ES": "1"},
        {"TEST_MOLEC": "1"},
        {"TEST_MOLEC": "2"},
    ],
)
def test_contact_audit_accepts_each_official_lab_confirmation_component(
    confirmation_fields: dict[str, str],
) -> None:
    record = contact_record(
        **{
            "BACILOSC_E": "2",
            "BACILOS_E2": "2",
            "CULTURA_ES": "2",
            "TEST_MOLEC": "3",
            **confirmation_fields,
        }
    )

    report = build_contact_year_report([record], year=2024, uf_code="23")

    assert report["selection"]["eligible_case_count"] == 1
    assert report["summary"]["recorded_values"] == {
        "identified_contacts": 2,
        "examined_contacts": 1,
        "proportion": 50.0,
    }


def test_contact_audit_filters_universe_year_and_geography() -> None:
    records = [
        contact_record(),
        contact_record(NU_ANO="2023"),
        contact_record(ID_MN_RESI="260790"),
        contact_record(TRATAMENTO="2"),
        contact_record(FORMA="2"),
        contact_record(SITUA_ENCE="6"),
        contact_record(
            BACILOSC_E="2",
            BACILOS_E2="2",
            CULTURA_ES="2",
            TEST_MOLEC="3",
        ),
    ]

    report = build_contact_year_report(records, year=2024, uf_code="23")

    assert report["selection"] == {
        "source_record_count": 7,
        "year_record_count": 6,
        "scope_record_count": 5,
        "candidate_universe_count": 2,
        "eligible_case_count": 1,
        "blank_closure_count": 0,
    }


def test_contact_audit_keeps_missingness_and_impossible_values_explicit() -> None:
    records = [
        contact_record(NU_CONTATO=2, NU_COMU_EX=1),
        contact_record(NU_CONTATO=None, NU_COMU_EX=1),
        contact_record(ID_MN_RESI="231290", NU_CONTATO=1, NU_COMU_EX=2),
    ]

    report = build_contact_year_report(records, year=2024, uf_code="23")

    assert report["status"] == REPORT_STATUS_RECONCILIATION_REQUIRED
    assert report["summary"]["recorded_values"] == {
        "identified_contacts": 3,
        "examined_contacts": 4,
        "proportion": pytest.approx(133.333333),
    }
    assert report["summary"]["complete_pairs"] == {
        "identified_contacts": 3,
        "examined_contacts": 3,
        "proportion": 100.0,
    }
    assert report["summary"]["missing_identified_count"] == 1
    assert report["summary"]["examined_above_identified_count"] == 1
    assert set(report["status_reasons"]) >= {
        "missing_contact_values",
        "case_examined_above_identified",
        "examined_without_identified",
        "municipality_examined_above_identified",
    }


def test_contact_audit_rejects_missing_required_fields() -> None:
    record = contact_record()
    del record["NU_COMU_EX"]

    report = build_contact_year_report([record], year=2024, uf_code="23")

    assert report["status"] == REPORT_STATUS_INVALID_SOURCE
    assert report["missing_required_fields"] == ["NU_COMU_EX"]
    assert "summary" not in report


def test_contact_audit_marks_invalid_numeric_values_as_invalid_source() -> None:
    report = build_contact_year_report(
        [contact_record(NU_CONTATO=-1)],
        year=2024,
        uf_code="23",
    )

    assert report["status"] == REPORT_STATUS_INVALID_SOURCE
    assert report["summary"]["invalid_identified_count"] == 1
    assert "invalid_contact_values" in report["status_reasons"]


def test_cached_audit_matches_hash_and_official_benchmark(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_dir = tmp_path / "datasus_samples"
    sample_dir.mkdir()
    source = sample_dir / "sinan_tb_br_2024.dbc"
    source.write_bytes(b"contact-source")
    source_hash = sha256(b"contact-source").hexdigest()
    monkeypatch.setattr(
        sinan_contacts_validation,
        "read_datasus_records",
        lambda path: [contact_record()],
    )
    manifest = audit_manifest(source_hash)
    manifest["headline_municipalities"] = [
        {
            "year": 2024,
            "municipality_code": "230440",
            "territory_id": "2304400",
            "territory_name": "Fortaleza",
            "expected": {
                "recorded_values": {
                    "identified_contacts": 2,
                    "examined_contacts": 1,
                    "proportion": 50.0,
                }
            },
        }
    ]

    report = build_cached_sinan_contact_audit(
        raw_dir=tmp_path,
        uf="CE",
        uf_code="23",
        year_from=2024,
        year_to=2024,
        manifest=manifest,
        generated_at=datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert report["status"] == REPORT_STATUS_PENDING_REVIEW
    assert report["source_artifacts"][0]["matches_manifest"] is True
    assert report["official_benchmark_comparisons"][0]["matches_official"] is True
    assert report["headline_acceptance"][0]["matches_fixture"] is True


def test_cached_audit_reports_benchmark_and_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_dir = tmp_path / "datasus_samples"
    sample_dir.mkdir()
    (sample_dir / "sinan_tb_br_2024.dbc").write_bytes(b"changed")
    monkeypatch.setattr(
        sinan_contacts_validation,
        "read_datasus_records",
        lambda path: [contact_record()],
    )

    report = build_cached_sinan_contact_audit(
        raw_dir=tmp_path,
        uf="CE",
        uf_code="23",
        year_from=2024,
        year_to=2024,
        manifest=audit_manifest("expected-hash", expected_examined=2),
    )

    assert report["status"] == REPORT_STATUS_RECONCILIATION_REQUIRED
    assert set(report["status_reasons"]) >= {
        "source_artifact_mismatch",
        "official_benchmark_mismatch",
    }


def test_cached_audit_reports_missing_year_without_aborting(tmp_path: Path) -> None:
    report = build_cached_sinan_contact_audit(
        raw_dir=tmp_path,
        uf="CE",
        uf_code="23",
        year_from=2024,
        year_to=2024,
        manifest=audit_manifest("unused"),
    )

    assert report["status"] == REPORT_STATUS_INVALID_SOURCE
    assert report["annual_reports"][0]["status_reasons"] == ["source_file_missing"]


def test_validate_sinan_contacts_cli_writes_report_before_mismatch_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = {
        "status": REPORT_STATUS_RECONCILIATION_REQUIRED,
        "scope": {
            "uf": "CE",
            "uf_code": "23",
            "year_from": 2024,
            "year_to": 2024,
        },
        "official_benchmark_comparisons": [{"year": 2024, "matches_official": False}],
    }
    monkeypatch.setattr(cli, "build_cached_sinan_contact_audit", lambda **kwargs: report)
    output_dir = tmp_path / "validation"

    result = CliRunner().invoke(
        app,
        [
            "validate-sinan-contacts",
            "--year-from",
            "2024",
            "--year-to",
            "2024",
            "--output-dir",
            str(output_dir),
        ],
    )

    output_path = output_dir / "sinan_contact_investigation_ce_2024_2024.json"
    assert result.exit_code == 1
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == (
        REPORT_STATUS_RECONCILIATION_REQUIRED
    )
    assert "CE/2024 official benchmark: mismatch" in result.output


def test_validate_sinan_contacts_cli_rejects_reversed_range(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "validate-sinan-contacts",
            "--year-from",
            "2024",
            "--year-to",
            "2023",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2
    assert "--year-from must not exceed --year-to" in result.output
    assert list(tmp_path.iterdir()) == []


def test_packaged_contact_manifest_records_sources_and_benchmarks() -> None:
    manifest = load_contact_audit_manifest()

    assert manifest["manifest_id"] == "sinan_contact_audit_ce_2018_2024_v1"
    assert manifest["scope"] == {
        "uf": "CE",
        "uf_code": "23",
        "year_from": 2018,
        "year_to": 2024,
    }
    years = {artifact["year"] for artifact in manifest["source_artifacts"]}
    assert years == set(range(2018, 2025))
    benchmarks = {item["year"]: item for item in manifest["official_benchmarks"]}
    assert benchmarks[2022]["examined_contacts"] / benchmarks[2022][
        "identified_contacts"
    ] * 100 == pytest.approx(benchmarks[2022]["proportion"], abs=0.1)
    assert benchmarks[2024]["examined_contacts"] / benchmarks[2024][
        "identified_contacts"
    ] * 100 == pytest.approx(benchmarks[2024]["proportion"], abs=0.1)
    assert len(manifest["headline_municipalities"]) == 5
