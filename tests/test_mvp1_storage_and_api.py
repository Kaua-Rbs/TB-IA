from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tbia.domain.models import CaseAggregate, MortalityAggregate, PopulationDenominator, Territory
from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    compute_and_store_indicators,
    seed_reference_data,
)
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    dashboard_context,
    initialize_database,
    load_cases,
    load_territories,
    save_case_aggregates,
    save_mortalities,
    save_populations,
    save_territories,
)
from tbia.web.app import create_app


def test_public_aggregate_savers_replace_year_rows(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        save_case_aggregates(
            session,
            [
                CaseAggregate(territory_id="2304400", year=2023, notified_cases=1),
                CaseAggregate(territory_id="2303709", year=2023, notified_cases=1),
            ],
        )
        session.commit()
        save_case_aggregates(
            session,
            [CaseAggregate(territory_id="2304400", year=2023, notified_cases=2)],
        )
        session.commit()
        rows = load_cases(session, 2023)
    engine.dispose()

    assert [(row.territory_id, row.notified_cases) for row in rows] == [("2304400", 2)]


def test_storage_pipeline_persists_dashboard_context(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        context = dashboard_context(session, 2023, "CE")

    assert context["territory_count"] == 6
    assert context["indicator_count"] > 0
    assert context["scenario_count"] > 0
    readiness = context["readiness"]
    assert readiness["public_sources"]["expected_count"] > 0
    assert readiness["geometry"]["geometry_count"] == 6
    assert readiness["geometry"]["territory_count"] == 6
    assert readiness["geometry"]["status"] == "ready"
    assert readiness["indicator_validation"]["source_status"] == "success"
    assert readiness["indicator_validation"]["warning_count"] >= 0
    assert readiness["generated_scenarios"]["scenario_count"] == context["scenario_count"]
    assert context["ranking"][0]["territory_id"] == "2304400"
    assert context["ranking"][0]["top_scenarios"]
    validation_source = next(
        source for source in context["sources"] if source["source_id"] == "indicator_validation"
    )
    assert validation_source["status"] == "success"

    with session_factory() as session:
        territories = load_territories(session, "CE")
    engine.dispose()
    assert all(territory.geometry is not None for territory in territories)


def test_public_api_returns_aggregate_indicators_and_ranking(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        indicators = client.get("/api/indicators?uf=CE&year=2023")
        rankings = client.get("/api/rankings?uf=CE&year=2023")
        report = client.get("/api/territories/2304400/report?year=2023")
        report_pt = client.get("/api/territories/2304400/report?year=2023&lang=pt")
        missing_report = client.get("/api/territories/9999999/report?year=2023")

    assert indicators.status_code == 200
    assert rankings.status_code == 200
    assert report.status_code == 200
    assert report_pt.status_code == 200
    assert missing_report.status_code == 404
    incidence = next(
        row for row in indicators.json() if row["indicator_id"] == "tb_incidence_per_100k"
    )
    assert incidence["unit"] == "per_100k"
    assert incidence["direction"] == "high_bad"
    assert rankings.json()[0]["territory_id"] == "2304400"
    assert report.json()["territory_name"] == "Fortaleza"
    incidence_pt = next(
        row
        for row in report_pt.json()["indicators"]
        if row["indicator_id"] == "tb_incidence_per_100k"
    )
    assert incidence_pt["indicator_name"] == "Incidência de TB"
    assert "Recomendado porque" in report_pt.json()["recommendations"][0]["explanation"]


def test_public_api_returns_geometry_and_enriched_map_properties(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        geometry = client.get("/api/geo/municipalities?uf=CE")
        map_response = client.get("/api/map/municipalities?uf=CE&year=2023")
        map_response_pt = client.get("/api/map/municipalities?uf=CE&year=2023&lang=pt")

    assert geometry.status_code == 200
    assert map_response.status_code == 200
    assert map_response_pt.status_code == 200
    geometry_features = geometry.json()["features"]
    assert len(geometry_features) == 6
    assert "indicators" not in geometry_features[0]["properties"]

    map_features = {
        feature["properties"]["territory_id"]: feature
        for feature in map_response.json()["features"]
    }
    fortaleza = map_features["2304400"]["properties"]
    caucaia = map_features["2303709"]["properties"]
    sobral = map_features["2312908"]["properties"]

    assert fortaleza["priority_score"] > 0
    assert fortaleza["scenario_count"] > 0
    assert fortaleza["top_severity"] in {"high", "moderate"}
    assert fortaleza["top_scenarios"]
    assert {"rule_id", "indicator_id", "severity", "score", "explanation"}.issubset(
        fortaleza["top_scenarios"][0]
    )
    assert fortaleza["top_explanations"][0] == fortaleza["top_scenarios"][0]["explanation"]
    assert fortaleza["data_status"] == "complete"
    assert "tb_incidence_per_100k" in fortaleza["indicators"]
    assert fortaleza["indicators"]["tb_incidence_per_100k"]["unit"] == "per_100k"
    assert fortaleza["indicators"]["cure_proportion"]["direction"] == "low_bad"

    metadata = map_response.json()["metadata"]
    assert metadata["feature_count"] == 6
    assert metadata["drawable_geometry_count"] == 6
    assert metadata["layers"]["cure_proportion"]["direction"] == "low_bad"
    metadata_pt = map_response_pt.json()["metadata"]
    assert metadata_pt["layers"]["tb_incidence_per_100k"]["label"] == "Incidência de TB"
    fortaleza_pt = {
        feature["properties"]["territory_id"]: feature
        for feature in map_response_pt.json()["features"]
    }["2304400"]["properties"]
    assert "limiar" in fortaleza_pt["top_scenarios"][0]["explanation"]

    mortality = caucaia["indicators"]["tb_mortality_per_100k"]
    assert mortality["value"] is None
    assert mortality["is_suppressed"] is True
    assert caucaia["data_status"] == "partial"
    assert sobral["data_status"] == "missing"
    assert sobral["top_scenarios"] == []


def test_dashboard_renders_workbench_controls_and_existing_sections(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        response = client.get("/?uf=CE&year=2023")
        english_response = client.get("/?uf=CE&year=2023&lang=en")

    assert response.status_code == 200
    assert english_response.status_code == 200
    html = response.text
    english_html = english_response.text
    assert "MVP1 Territorial" in html
    assert "MVP2 Operações" in html
    assert "English" in html
    assert 'id="uf-control"' in html
    assert 'id="year-control"' in html
    assert "dado público agregado" in html
    assert "Prontidão dos dados" in html
    assert "Fontes públicas" in html
    assert "Geometria" in html
    assert "Validação dos indicadores" in html
    assert "Cenários gerados" in html
    assert "MVP2 Operations" in english_html
    assert "public aggregate" in english_html
    assert "Data readiness" in english_html
    assert "Why flagged" in english_html
    assert 'id="municipality-map"' in html
    assert 'id="map-layer"' in html
    assert 'id="municipality-search"' in html
    assert 'id="severity-filter"' in html
    assert 'id="data-status-filter"' in html
    assert 'id="ranking-body"' in html
    assert "https://unpkg.com/leaflet" in html
    assert 'id="map-status"' in html
    assert "Legenda do mapa" in html
    assert "CDN do Leaflet" in html
    assert "Ranking de prioridade" in html
    assert "Atualização das fontes" in html
    assert "selectTerritory" in html
    assert "highlightRankingRow" in html
    assert "highlightPolygon" in html
    assert "searchMunicipality" in html
    assert "Por que foi sinalizado" in html
    assert "Resposta recomendada" in html
    assert "Indicadores" in html
    assert "Ressalvas" in html


def fixture_geometry(offset: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [-39.0 + offset, -5.0],
                [-38.9 + offset, -5.0],
                [-38.9 + offset, -4.9],
                [-39.0 + offset, -5.0],
            ]
        ],
    }


def populate_database(database_url: str) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [
                Territory(
                    "2304400",
                    "Fortaleza",
                    "municipality",
                    "23",
                    "CE",
                    geometry=fixture_geometry(0.0),
                ),
                Territory(
                    "2303709",
                    "Caucaia",
                    "municipality",
                    "23",
                    "CE",
                    geometry=fixture_geometry(0.2),
                ),
                Territory(
                    "2312908",
                    "Sobral",
                    "municipality",
                    "23",
                    "CE",
                    geometry=fixture_geometry(0.4),
                ),
                Territory(
                    "2304202",
                    "Crato",
                    "municipality",
                    "23",
                    "CE",
                    geometry=fixture_geometry(0.6),
                ),
                Territory(
                    "2307304",
                    "Juazeiro do Norte",
                    "municipality",
                    "23",
                    "CE",
                    geometry=fixture_geometry(0.8),
                ),
                Territory(
                    "2306405",
                    "Itapipoca",
                    "municipality",
                    "23",
                    "CE",
                    geometry=fixture_geometry(1.0),
                ),
            ],
        )
        save_populations(
            session,
            [
                PopulationDenominator("2304400", 2023, 100_000, "ibge_population"),
                PopulationDenominator("2303709", 2023, 100_000, "ibge_population"),
                PopulationDenominator("2304202", 2023, 130_000, "ibge_population"),
                PopulationDenominator("2307304", 2023, 270_000, "ibge_population"),
                PopulationDenominator("2306405", 2023, 130_000, "ibge_population"),
            ],
        )
        save_case_aggregates(
            session,
            [
                CaseAggregate(
                    territory_id="2304400",
                    year=2023,
                    notified_cases=100,
                    new_cases=80,
                    closed_cases=50,
                    cured_cases=35,
                    treatment_interruption_cases=10,
                    retreatment_cases=12,
                    new_pulmonary_cases=70,
                    lab_confirmed_pulmonary_cases=30,
                    hiv_tested_cases=55,
                    tb_hiv_cases=8,
                    trm_tb_cases=25,
                    retreatment_pulmonary_cases=10,
                    culture_retreated_cases=5,
                ),
                CaseAggregate(
                    territory_id="2303709",
                    year=2023,
                    notified_cases=30,
                    new_cases=20,
                    closed_cases=20,
                    cured_cases=18,
                    treatment_interruption_cases=1,
                    retreatment_cases=3,
                    new_pulmonary_cases=18,
                    lab_confirmed_pulmonary_cases=16,
                    hiv_tested_cases=18,
                    tb_hiv_cases=1,
                    trm_tb_cases=15,
                    retreatment_pulmonary_cases=3,
                    culture_retreated_cases=2,
                ),
                CaseAggregate(
                    territory_id="2304202",
                    year=2023,
                    notified_cases=35,
                    new_cases=30,
                    closed_cases=20,
                    cured_cases=15,
                    treatment_interruption_cases=5,
                    retreatment_cases=5,
                    new_pulmonary_cases=28,
                    lab_confirmed_pulmonary_cases=25,
                    hiv_tested_cases=24,
                    tb_hiv_cases=5,
                    trm_tb_cases=20,
                    retreatment_pulmonary_cases=5,
                    culture_retreated_cases=5,
                ),
                CaseAggregate(
                    territory_id="2307304",
                    year=2023,
                    notified_cases=55,
                    new_cases=50,
                    closed_cases=30,
                    cured_cases=20,
                    treatment_interruption_cases=5,
                    retreatment_cases=5,
                    new_pulmonary_cases=45,
                    lab_confirmed_pulmonary_cases=35,
                    hiv_tested_cases=40,
                    tb_hiv_cases=6,
                    trm_tb_cases=32,
                    retreatment_pulmonary_cases=5,
                    culture_retreated_cases=5,
                ),
                CaseAggregate(
                    territory_id="2306405",
                    year=2023,
                    notified_cases=30,
                    new_cases=25,
                    closed_cases=20,
                    cured_cases=10,
                    treatment_interruption_cases=6,
                    retreatment_cases=5,
                    new_pulmonary_cases=20,
                    lab_confirmed_pulmonary_cases=10,
                    hiv_tested_cases=18,
                    tb_hiv_cases=5,
                    trm_tb_cases=12,
                    retreatment_pulmonary_cases=5,
                    culture_retreated_cases=5,
                ),
            ],
        )
        save_mortalities(
            session,
            [
                MortalityAggregate("2304400", 2023, 15),
                MortalityAggregate("2303709", 2023, 1),
                MortalityAggregate("2304202", 2023, 5),
                MortalityAggregate("2307304", 2023, 6),
                MortalityAggregate("2306405", 2023, 5),
            ],
        )
        compute_and_store_indicators(session, Mvp1Config(year=2023, minimum_count=5))
        build_and_store_scenarios(session, Mvp1Config(year=2023, minimum_count=5))
        session.commit()
    engine.dispose()
