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
    load_territories,
    save_case_aggregates,
    save_mortalities,
    save_populations,
    save_territories,
)
from tbia.web.app import create_app


def test_storage_pipeline_persists_dashboard_context(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        context = dashboard_context(session, 2023, "CE")

    assert context["territory_count"] == 3
    assert context["indicator_count"] > 0
    assert context["scenario_count"] > 0
    assert context["ranking"][0]["territory_id"] == "2304400"

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

    assert indicators.status_code == 200
    assert rankings.status_code == 200
    assert report.status_code == 200
    assert any(row["indicator_id"] == "tb_incidence_per_100k" for row in indicators.json())
    assert rankings.json()[0]["territory_id"] == "2304400"
    assert report.json()["territory_name"] == "Fortaleza"


def test_public_api_returns_geometry_and_enriched_map_properties(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        geometry = client.get("/api/geo/municipalities?uf=CE")
        map_response = client.get("/api/map/municipalities?uf=CE&year=2023")

    assert geometry.status_code == 200
    assert map_response.status_code == 200
    geometry_features = geometry.json()["features"]
    assert len(geometry_features) == 3
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
    assert fortaleza["data_status"] == "complete"
    assert "tb_incidence_per_100k" in fortaleza["indicators"]

    mortality = caucaia["indicators"]["tb_mortality_per_100k"]
    assert mortality["value"] is None
    assert mortality["is_suppressed"] is True
    assert sobral["data_status"] == "missing"


def test_dashboard_renders_map_panel_and_existing_sections(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        response = client.get("/?uf=CE&year=2023")

    assert response.status_code == 200
    html = response.text
    assert 'id="municipality-map"' in html
    assert 'id="map-layer"' in html
    assert "https://unpkg.com/leaflet" in html
    assert "Priority ranking" in html
    assert "Source freshness" in html


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
            ],
        )
        save_populations(
            session,
            [
                PopulationDenominator("2304400", 2023, 1_000_000, "ibge_population"),
                PopulationDenominator("2303709", 2023, 100_000, "ibge_population"),
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
            ],
        )
        save_mortalities(
            session,
            [
                MortalityAggregate("2304400", 2023, 15),
                MortalityAggregate("2303709", 2023, 1),
            ],
        )
        compute_and_store_indicators(session, Mvp1Config(year=2023, minimum_count=5))
        build_and_store_scenarios(session, Mvp1Config(year=2023, minimum_count=5))
        session.commit()
    engine.dispose()
