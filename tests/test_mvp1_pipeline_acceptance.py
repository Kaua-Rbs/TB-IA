from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from tbia.domain.models import Territory
from tbia.ingest.datasus import datasus_demo_files
from tbia.pipeline import Mvp1Config
from tbia.preparation import prepare_territorial_data
from tbia.storage import (
    api_indicator_rows,
    create_engine_for_url,
    create_session_factory,
    dashboard_context,
    initialize_database,
    latest_import_runs_for_scope,
    load_cases,
    load_hospitalizations,
    load_indicator_values,
    load_mortalities,
    load_territories,
    save_territories,
)
from tbia.web.app import create_app

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mvp1_acceptance"
CORE_SOURCE_IDS = {
    "ibge_localidades",
    "ibge_population",
    "sinan_tb",
    "sim",
    "sih_sus",
    "cnes",
}


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def prepare_cached_datasus_files(raw_dir: Path) -> None:
    sample_dir = raw_dir / "datasus_samples"
    sample_dir.mkdir(parents=True)
    files = datasus_demo_files("CE", 2023, sih_months=tuple(range(1, 13)))
    for file in files:
        (sample_dir / file.local_name).touch()


def fixture_fetch_json(url: str) -> object:
    if "/localidades/" in url:
        return load_fixture("ibge_localidades_ce.json")
    if "/malhas/" in url:
        return load_fixture("ibge_malhas_ce.geojson")
    if "apisidra.ibge.gov.br" in url:
        return load_fixture("ibge_population_ce_2022.json")
    raise AssertionError(f"unexpected public URL: {url}")


def fixture_datasus_records(
    path: Path, *, records: dict[str, list[dict[str, object]]]
) -> list[dict[str, object]]:
    name = path.name
    if name.startswith("sinan_tb_"):
        return records["sinan_tb"]
    if name.startswith("sim_"):
        return records["sim"]
    if name.startswith("cnes_"):
        return records["cnes"]
    if name.startswith("sih_"):
        return records["sih_sus"] if name.endswith("_01.dbc") else []
    raise AssertionError(f"unexpected DATASUS fixture path: {path}")


def configure_acceptance_io(
    monkeypatch: Any, datasus_records: dict[str, list[dict[str, object]]]
) -> None:
    monkeypatch.setattr("tbia.pipeline.fetch_json", fixture_fetch_json)
    monkeypatch.setattr(
        "tbia.pipeline.read_datasus_records",
        partial(fixture_datasus_records, records=datasus_records),
    )


def canonical_snapshot(session: Any) -> dict[str, Any]:
    context = dashboard_context(session, 2023, "CE")
    values = load_indicator_values(
        session,
        2023,
        {territory.territory_id for territory in load_territories(session, "CE")},
    )
    return {
        "territories": [
            (territory.territory_id, territory.geometry is not None)
            for territory in load_territories(session, "CE")
        ],
        "case_count": len(load_cases(session, 2023)),
        "mortality_count": len(load_mortalities(session, 2023)),
        "hospitalization_count": len(load_hospitalizations(session, 2023)),
        "indicators": sorted(
            (
                value.territory_id,
                value.indicator_id,
                value.value,
                value.is_suppressed,
            )
            for value in values
        ),
        "scenario_count": context["scenario_count"],
        "ranking": [
            (row["territory_id"], row["score"], row["scenario_count"]) for row in context["ranking"]
        ],
    }


def assert_preparation_result(result: Any) -> None:
    assert result.result_status == "ready"
    assert result.download["requested_file_count"] == 15
    assert result.download["existing_file_count"] == 15
    assert result.download["downloaded_file_count"] == 0
    assert result.download["failed_file_count"] == 0
    assert result.indicator_count > 0
    assert result.scenario_count > 0
    assert result.recommendation_count > 0


def assert_persisted_acceptance_state(session: Any, expected: dict[str, Any]) -> dict[str, Any]:
    snapshot = canonical_snapshot(session)
    context = dashboard_context(session, 2023, "CE")
    source_rows = {
        row["source_id"]: row
        for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="CE")
    }
    indicator_rows = api_indicator_rows(session, 2023, "CE")

    assert len(load_territories(session, "PE")) == 1
    assert len(snapshot["territories"]) == expected["territory_count"]
    assert all(has_geometry for _, has_geometry in snapshot["territories"])
    assert snapshot["case_count"] == expected["territory_count"]
    assert snapshot["mortality_count"] == expected["territory_count"]
    assert snapshot["hospitalization_count"] == expected["territory_count"]
    assert context["readiness"]["public_sources"]["status"] == "ready"
    assert context["readiness"]["geometry"]["status"] == "ready"
    assert context["readiness"]["indicator_validation"]["status"] == "ready"
    assert context["ranking"][0]["territory_id"] == expected["top_territory_id"]
    assert source_rows.keys() >= CORE_SOURCE_IDS
    assert all(source_rows[source_id]["status"] == "success" for source_id in CORE_SOURCE_IDS)
    assert source_rows["indicator_validation"]["status"] == "success"
    assert source_rows["cnes"]["row_count"] == expected["territory_count"]

    by_indicator = {(row["territory_id"], row["indicator_id"]): row for row in indicator_rows}
    for indicator_id, value in expected["fortaleza_indicators"].items():
        assert by_indicator[("2304400", indicator_id)]["value"] == pytest.approx(value)
    for suppressed in expected["suppressed"]:
        row = by_indicator[(suppressed["territory_id"], suppressed["indicator_id"])]
        assert row["value"] is None
        assert row["is_suppressed"] is True
    return snapshot


def assert_validation_report(processed_dir: Path) -> None:
    validation_path = processed_dir / "validation" / "indicator_validation_ce_2023.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert validation["status"] == "success"
    assert validation["scope"] == {"year": 2023, "geographic_scope": "CE"}
    assert validation["violation_count"] == 0


def assert_api_consistency(
    database_url: str, expected: dict[str, Any], snapshot: dict[str, Any]
) -> None:
    with TestClient(create_app(database_url)) as client:
        context_response = client.get("/api/territorial/context?uf=CE&year=2023")
        map_response = client.get("/api/territorial/map?uf=CE&year=2023")
        report_response = client.get(
            f"/api/territories/{expected['top_territory_id']}/report?year=2023"
        )

    assert context_response.status_code == 200
    assert map_response.status_code == 200
    assert report_response.status_code == 200
    context_payload = context_response.json()
    map_payload = map_response.json()
    report_payload = report_response.json()
    assert context_payload["territory_count"] == expected["territory_count"]
    assert context_payload["scenario_count"] == snapshot["scenario_count"]
    assert len(map_payload["features"]) == expected["territory_count"]
    assert map_payload["metadata"]["drawable_geometry_count"] == expected["territory_count"]
    assert report_payload["territory_id"] == expected["top_territory_id"]
    assert {scenario["rule_id"] for scenario in report_payload["scenarios"]} == set(
        expected["fortaleza_scenarios"]
    )

    map_by_id = {
        feature["properties"]["territory_id"]: feature for feature in map_payload["features"]
    }
    assert (
        map_by_id[expected["top_territory_id"]]["properties"]["priority_score"]
        == context_payload["ranking"][0]["score"]
    )
    suppressed_lab = map_by_id["2306405"]["properties"]["indicators"][
        "laboratory_confirmation_proportion"
    ]
    assert suppressed_lab["value"] is None
    assert suppressed_lab["is_suppressed"] is True


def test_ce_territorial_pipeline_runs_end_to_end_without_network(
    tmp_path: Path, monkeypatch: Any
) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    prepare_cached_datasus_files(raw_dir)
    datasus_records = cast(dict[str, list[dict[str, object]]], load_fixture("datasus_records.json"))
    expected = cast(dict[str, Any], load_fixture("expected.json"))
    configure_acceptance_io(monkeypatch, datasus_records)

    database_url = f"sqlite:///{tmp_path / 'acceptance.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    config = Mvp1Config(
        uf="CE",
        year=2023,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        minimum_count=5,
    )
    with session_factory() as session:
        save_territories(
            session,
            [Territory("2607901", "Jaboatao", "municipality", "26", "PE")],
        )
        session.commit()

    first = prepare_territorial_data(
        session_factory,
        config,
        sih_all_months=True,
        timeout=1,
    )
    assert_preparation_result(first)

    with session_factory() as session:
        first_snapshot = assert_persisted_acceptance_state(session, expected)
    assert_validation_report(processed_dir)

    second = prepare_territorial_data(
        session_factory,
        config,
        sih_all_months=True,
        timeout=1,
    )
    with session_factory() as session:
        second_snapshot = canonical_snapshot(session)
        assert len(load_territories(session, "PE")) == 1
    engine.dispose()

    assert second.result_status == "ready"
    assert second.indicator_count == first.indicator_count
    assert second.scenario_count == first.scenario_count
    assert second.recommendation_count == first.recommendation_count
    assert second_snapshot == first_snapshot
    assert_api_consistency(database_url, expected, first_snapshot)
