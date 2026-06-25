from __future__ import annotations

from pathlib import Path

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
    engine.dispose()

    assert context["territory_count"] == 2
    assert context["indicator_count"] > 0
    assert context["scenario_count"] > 0
    assert context["ranking"][0]["territory_id"] == "2304400"


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


def populate_database(database_url: str) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [
                Territory("2304400", "Fortaleza", "municipality", "23", "CE"),
                Territory("2303709", "Caucaia", "municipality", "23", "CE"),
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
        compute_and_store_indicators(session, Mvp1Config(year=2023, minimum_count=1))
        build_and_store_scenarios(session, Mvp1Config(year=2023, minimum_count=1))
        session.commit()
    engine.dispose()
