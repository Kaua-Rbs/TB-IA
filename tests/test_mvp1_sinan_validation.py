from __future__ import annotations

from datetime import UTC, datetime

from tbia.ingest.sinan_validation import build_sinan_mapping_report


def test_build_sinan_mapping_report_counts_values_and_unmapped_codes() -> None:
    records = [
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "1",
            "SITUA_ENCE": "1",
            "FORMA": "1",
            "HIV": "1",
            "AGRAVAIDS": "2",
            "BACILOSC_E": "1",
            "CULTURA_ES": "4",
            "TEST_MOLEC": "1",
            "RIFAMPICIN": "",
        },
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "9",
            "SITUA_ENCE": "2",
            "FORMA": "3",
            "HIV": "4",
            "AGRAVAIDS": "1",
            "BACILOSC_E": "3",
            "CULTURA_ES": "2",
            "TEST_MOLEC": "5",
            "RIFAMPICIN": "2",
        },
        {"NU_ANO": "2022", "ID_MN_RESI": "230440", "TRATAMENTO": "1"},
        {"NU_ANO": "2023", "ID_MN_RESI": "260790", "TRATAMENTO": "1"},
    ]

    report = build_sinan_mapping_report(
        records,
        year=2023,
        uf_code="23",
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert report["status"] == "technical_audit_pending_domain_review"
    assert report["record_count"] == 2
    tratamento = next(field for field in report["fields"] if field["field"] == "TRATAMENTO")
    assert tratamento["unmapped_values"] == ["9"]
    assert {item["value"]: item["count"] for item in tratamento["frequencies"]} == {
        "1": 1,
        "9": 1,
    }
    test_molec = next(field for field in report["fields"] if field["field"] == "TEST_MOLEC")
    assert test_molec["mapped_codes"]["1"] == ("counted as TRM-TB use and laboratory confirmation")
    assert test_molec["mapped_codes"]["5"] == "not counted as TRM-TB use"
    rifampicin = next(field for field in report["fields"] if field["field"] == "RIFAMPICIN")
    assert rifampicin["mapped_codes"]["<blank>"].startswith("audited only")
