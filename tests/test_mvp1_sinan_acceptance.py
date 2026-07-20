from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from tbia.ingest.sinan_acceptance import (
    build_sinan_diagnostic_acceptance_report,
    load_sinan_acceptance_fixture,
)


def acceptance_fixture(source_hash: str) -> dict[str, Any]:
    indicator = {
        "numerator": 5,
        "denominator": 5,
        "raw_value": 100.0,
        "value": 100.0,
        "is_suppressed": False,
    }
    return {
        "fixture_id": "test_fixture",
        "scope": {"uf": "CE", "uf_code": "23", "year": 2023},
        "minimum_count": 5,
        "source_artifacts": [{"filename": "sample.dbf", "sha256": source_hash}],
        "cases": [
            {
                "territory_id": "2304400",
                "territory_name": "Fortaleza",
                "indicators": {
                    "hiv_testing_proportion": dict(indicator),
                    "trm_tb_use_proportion": dict(indicator),
                    "culture_use_among_retreatment": dict(indicator),
                },
            }
        ],
    }


def matching_records() -> list[dict[str, object]]:
    new_cases: list[dict[str, object]] = [
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "1",
            "FORMA": "1",
            "HIV": "1",
            "BACILOSC_E": "2",
            "CULTURA_ES": "4",
            "TEST_MOLEC": "1",
        }
        for _ in range(5)
    ]
    retreatments: list[dict[str, object]] = [
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "2",
            "FORMA": "1",
            "HIV": "4",
            "BACILOSC_E": "2",
            "CULTURA_ES": "2",
            "TEST_MOLEC": "5",
        }
        for _ in range(5)
    ]
    return new_cases + retreatments


def test_diagnostic_acceptance_matches_production_transform(tmp_path: Path) -> None:
    source = tmp_path / "sample.dbf"
    source.write_bytes(b"fixture")
    fixture = acceptance_fixture(sha256(b"fixture").hexdigest())

    report = build_sinan_diagnostic_acceptance_report(
        matching_records(),
        fixture,
        source_paths=[source],
    )

    assert report["status"] == "passed"
    assert report["check_count"] == 3
    assert report["differences"] == []
    assert all(check["status"] == "passed" for check in report["checks"])
    assert report["source_artifacts"][0]["matches_fixture"] is True


def test_diagnostic_acceptance_reports_source_and_indicator_differences(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.dbf"
    source.write_bytes(b"unexpected")
    fixture = acceptance_fixture(sha256(b"fixture").hexdigest())
    fixture["cases"][0]["indicators"]["trm_tb_use_proportion"]["numerator"] = 4

    report = build_sinan_diagnostic_acceptance_report(
        matching_records(),
        fixture,
        source_paths=[source],
    )

    assert report["status"] == "failed"
    assert "source artifact mismatch: sample.dbf" in report["differences"]
    assert "2304400/trm_tb_use_proportion: numerator" in report["differences"]


def test_packaged_ce_2023_fixture_records_scope_and_suppression_cases() -> None:
    fixture = load_sinan_acceptance_fixture("CE", 2023)

    assert fixture is not None
    assert fixture["fixture_id"] == "sinan_diagnostic_coverage_ce_2023_v1"
    assert fixture["scope"] == {"uf": "CE", "uf_code": "23", "year": 2023}
    cases = {case["territory_id"]: case for case in fixture["cases"]}
    assert set(cases) == {"2303709", "2304400", "2307650", "2311306", "2312908"}
    assert cases["2307650"]["indicators"]["culture_use_among_retreatment"]["is_suppressed"] is True
    assert cases["2311306"]["indicators"]["trm_tb_use_proportion"]["value"] is None
