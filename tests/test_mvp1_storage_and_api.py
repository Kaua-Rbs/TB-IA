from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from tbia.domain.models import (
    CaseAggregate,
    Facility,
    ImportRun,
    IndicatorValue,
    MortalityAggregate,
    PopulationDenominator,
    ScenarioSeverity,
    SourceProvenance,
    Territory,
    TerritoryScenario,
)
from tbia.geography import UF_SIGLAS
from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    compute_and_store_indicators,
    seed_reference_data,
)
from tbia.preparation import TerritorialPreparationResult
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    dashboard_context,
    initialize_database,
    latest_import_runs_for_scope,
    load_cases,
    load_indicator_values,
    load_populations,
    load_territories,
    load_territory_scenarios,
    save_case_aggregates,
    save_facilities,
    save_import_run,
    save_indicator_history_values,
    save_indicator_values,
    save_mortalities,
    save_populations,
    save_territories,
    save_territory_scenarios,
)
from tbia.web import app as web_app
from tbia.web.app import create_app
from tbia.web.i18n import localize_dashboard_context


def test_public_aggregate_savers_replace_only_target_territories(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        save_case_aggregates(
            session,
            [
                CaseAggregate(territory_id="2304400", year=2023, notified_cases=1),
                CaseAggregate(territory_id="2607901", year=2023, notified_cases=1),
            ],
        )
        session.commit()
        save_case_aggregates(
            session,
            [CaseAggregate(territory_id="2607901", year=2023, notified_cases=2)],
            replace_territory_ids={"2607901"},
        )
        session.commit()
        rows = sorted(load_cases(session, 2023), key=lambda row: row.territory_id)
    engine.dispose()

    assert [(row.territory_id, row.notified_cases) for row in rows] == [
        ("2304400", 1),
        ("2607901", 2),
    ]


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


def test_dimension_scoring_is_consistent_in_context_map_and_report(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'dimensions.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    scenarios = [
        TerritoryScenario(
            territory_id="2304400",
            year=2023,
            rule_id="diagnostic_signal_a",
            scenario_id="diagnostic_signal_a",
            severity=ScenarioSeverity.HIGH,
            score=5,
            explanation="Signal A",
            indicator_id="indicator_a",
            indicator_value=20,
            threshold_value=30,
            ranking_dimension="diagnostic_access",
        ),
        TerritoryScenario(
            territory_id="2304400",
            year=2023,
            rule_id="diagnostic_signal_b",
            scenario_id="diagnostic_signal_b",
            severity=ScenarioSeverity.MODERATE,
            score=3,
            explanation="Signal B",
            indicator_id="indicator_b",
            indicator_value=25,
            threshold_value=35,
            ranking_dimension="diagnostic_access",
        ),
    ]
    with session_factory() as session:
        save_territories(
            session,
            [Territory("2304400", "Fortaleza", "municipality", "23", "CE")],
        )
        save_territory_scenarios(
            session,
            scenarios,
            2023,
            replace_territory_ids={"2304400"},
        )
        session.commit()
        context = dashboard_context(session, 2023, "CE")
    engine.dispose()

    ranking = context["ranking"][0]
    assert ranking["score"] == 5
    assert ranking["scenario_count"] == 2
    assert ranking["ranking_dimension_count"] == 1
    assert {row["ranking_dimension"] for row in ranking["top_scenarios"]} == {"diagnostic_access"}

    with TestClient(create_app(database_url)) as client:
        map_response = client.get("/api/territorial/map?uf=CE&year=2023")
        report_response = client.get("/api/territories/2304400/report?year=2023")

    assert map_response.status_code == 200
    properties = map_response.json()["features"][0]["properties"]
    assert properties["priority_score"] == 5
    assert properties["scenario_count"] == 2
    assert properties["ranking_dimension_count"] == 1
    assert report_response.status_code == 200
    assert {row["ranking_dimension"] for row in report_response.json()["scenarios"]} == {
        "diagnostic_access"
    }


def test_product_readiness_is_localized_from_structured_fields(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'readiness.db'}"
    populate_database(database_url)
    timestamp = datetime(2023, 12, 31, tzinfo=UTC)
    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        save_import_run(
            session,
            ImportRun(
                source_id="sih_sus",
                status="partial",
                started_at=timestamp,
                finished_at=timestamp,
                row_count=3,
                message="fixture",
                year=2023,
                geographic_scope="CE",
                loaded_months=(1, 2, 3),
            ),
        )
        session.commit()
        raw_context = dashboard_context(session, 2023, "CE")
        raw_context["readiness"]["future_readiness"] = {
            "label": "Future readiness",
            "status": "partial",
            "detail": "Original detail",
        }
        fallback = localize_dashboard_context(raw_context, "pt")["readiness"]["future_readiness"]
    engine.dispose()

    with TestClient(create_app(database_url)) as client:
        pt_response = client.get("/api/territorial/context?uf=CE&year=2023&lang=pt")
        en_response = client.get("/api/territorial/context?uf=CE&year=2023&lang=en")

    assert pt_response.status_code == 200
    assert en_response.status_code == 200
    pt_payload = pt_response.json()
    en_payload = en_response.json()
    pt_readiness = pt_payload["readiness"]
    en_readiness = en_payload["readiness"]

    assert {key: item["label"] for key, item in pt_readiness.items()} == {
        "public_sources": "Fontes públicas",
        "hospitalization_coverage": "Cobertura anual do SIH/SUS",
        "geometry": "Geometria",
        "indicator_validation": "Validação dos indicadores",
        "generated_scenarios": "Sinais gerados",
        "diagnostic_scenario_rules": "Priorização da cobertura diagnóstica",
    }
    assert {key: item["label"] for key, item in en_readiness.items()} == {
        "public_sources": "Public sources",
        "hospitalization_coverage": "Annual SIH/SUS coverage",
        "geometry": "Geometry",
        "indicator_validation": "Indicator validation",
        "generated_scenarios": "Generated signals",
        "diagnostic_scenario_rules": "Diagnostic coverage prioritization",
    }
    assert pt_readiness["hospitalization_coverage"]["detail"] == (
        "3/12 meses do SIH/SUS carregados; faltam 04, 05, 06, 07, 08, 09, 10, 11, 12"
    )
    assert en_readiness["hospitalization_coverage"]["detail"] == (
        "3/12 SIH/SUS months loaded; missing 04, 05, 06, 07, 08, 09, 10, 11, 12"
    )
    assert pt_readiness["geometry"]["detail"] == "6/6 municípios com geometria"
    assert en_readiness["geometry"]["detail"] == "6/6 municipalities with geometry"
    assert pt_readiness["generated_scenarios"]["detail"].endswith("territórios")
    assert en_readiness["generated_scenarios"]["detail"].endswith("territories")
    assert {key: item["status"] for key, item in pt_readiness.items()} == {
        key: item["status"] for key, item in en_readiness.items()
    }

    pt_health = pt_payload["health_territory_readiness"]
    en_health = en_payload["health_territory_readiness"]
    assert {key: item["label"] for key, item in pt_health.items()} == {
        "public_subterritory_geometry": "Geometria pública de referência",
        "cnes_facility_context": "Contexto CNES de unidades",
        "official_health_territory_boundaries": ("Limites oficiais de territórios de saúde"),
        "tb_health_territory_indicators": ("Indicadores de TB por território de saúde"),
    }
    assert {key: item["label"] for key, item in en_health.items()} == {
        "public_subterritory_geometry": "Public reference geometry",
        "cnes_facility_context": "CNES facility context",
        "official_health_territory_boundaries": ("Official health-territory boundaries"),
        "tb_health_territory_indicators": "TB indicators by health territory",
    }
    assert (
        "fontes exclusivamente públicas"
        in (pt_health["official_health_territory_boundaries"]["detail"])
    )
    assert "public-only sources" in (en_health["official_health_territory_boundaries"]["detail"])
    assert fallback == {
        "label": "Future readiness",
        "status": "partial",
        "detail": "Original detail",
    }


def test_import_run_readiness_is_scoped_by_year_and_geography(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    timestamp = datetime(2023, 12, 31, tzinfo=UTC)
    with session_factory() as session:
        seed_reference_data(session)
        runs = [
            ImportRun("sim", "success", timestamp, timestamp, 99, "legacy"),
            ImportRun("sinan_tb", "success", timestamp, timestamp, 100, "national", 2023, "BR"),
            ImportRun("cnes", "failed", timestamp, timestamp, 1, "older", 2023, "CE"),
            ImportRun("cnes", "success", timestamp, timestamp, 3, "current", 2023, "CE"),
            ImportRun("cnes", "failed", timestamp, timestamp, 2, "offline", 2023, "PE"),
            ImportRun("sih_sus", "success", timestamp, timestamp, 5, "legacy", 2023, "CE"),
            ImportRun(
                "indicator_validation",
                "success",
                timestamp,
                timestamp,
                10,
                "validated",
                2023,
                "CE",
            ),
            ImportRun("cnes", "failed", timestamp, timestamp, 4, "prior year", 2022, "CE"),
        ]
        for run in runs:
            save_import_run(session, run)
        session.commit()

        ce_rows = {
            row["source_id"]: row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="ce")
        }
        pe_rows = {
            row["source_id"]: row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="PE")
        }
        prior_year_rows = {
            row["source_id"]: row
            for row in latest_import_runs_for_scope(session, year=2022, geographic_scope="CE")
        }
        national_rows = {
            row["source_id"]: row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="BR")
        }
    engine.dispose()

    assert ce_rows["cnes"]["status"] == "success"
    assert ce_rows["cnes"]["row_count"] == 3
    assert ce_rows["cnes"]["geographic_scope"] == "CE"
    assert ce_rows["sih_sus"]["status"] == "partial"
    assert ce_rows["sih_sus"]["month_coverage"]["loaded_months"] is None
    assert ce_rows["sinan_tb"]["geographic_scope"] == "BR"
    assert ce_rows["sinan_tb"]["scope_inherited"] is True
    assert ce_rows["indicator_validation"]["scope_inherited"] is False
    assert "sim" not in ce_rows
    assert "indicator_validation" not in pe_rows
    assert pe_rows["cnes"]["status"] == "failed"
    assert prior_year_rows["cnes"]["message"] == "prior year"
    assert national_rows["cnes"]["status"] == "failed"
    assert national_rows["cnes"]["row_count"] == 5
    assert national_rows["cnes"]["geographic_scope"] == "BR"
    assert "failed=PE" in national_rows["cnes"]["message"]
    assert "missing=" in national_rows["cnes"]["message"]


def test_national_hospitalization_scenarios_require_complete_sih_coverage(
    tmp_path: Path,
) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'national-coverage.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    timestamp = datetime(2023, 12, 31, tzinfo=UTC)

    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [
                *fixture_scope_territories("23", "CE", "23", [20, 19, 18, 17, 16]),
                *fixture_scope_territories("26", "PE", "26", [10, 9, 8, 7, 6]),
            ],
        )
        hospitalization_values = [
            IndicatorValue(
                "hospitalization_burden_per_100k",
                f"{prefix}{index:05d}",
                2023,
                float(value),
                value,
                100_000,
                False,
                ("sih_sus", "ibge_population"),
                "",
            )
            for prefix, values in (
                ("23", [20, 19, 18, 17, 16]),
                ("26", [10, 9, 8, 7, 6]),
            )
            for index, value in enumerate(values, start=1)
        ]
        save_indicator_values(session, hospitalization_values, 2023)
        for uf in UF_SIGLAS:
            loaded_months = (1,) if uf == "CE" else tuple(range(1, 13))
            save_import_run(
                session,
                ImportRun(
                    source_id="sih_sus",
                    status="partial" if uf == "CE" else "success",
                    started_at=timestamp,
                    finished_at=timestamp,
                    row_count=1,
                    message="fixture",
                    year=2023,
                    geographic_scope=uf,
                    loaded_months=loaded_months,
                ),
            )

        build_and_store_scenarios(session, Mvp1Config(uf="BR", year=2023))
        session.commit()
        national_source = next(
            row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="BR")
            if row["source_id"] == "sih_sus"
        )
        uf_scenarios = load_territory_scenarios(session, 2023, "uf")
        national_scenarios = load_territory_scenarios(session, 2023, "national")
    engine.dispose()

    assert national_source["status"] == "partial"
    assert national_source["month_coverage"]["complete"] is False
    assert national_source["month_coverage"]["scope_count"] == 27
    assert national_source["month_coverage"]["complete_scope_count"] == 26
    assert national_source["month_coverage"]["loaded_months"] == [1]
    assert len(uf_scenarios) == 2
    assert all(
        scenario.territory_id.startswith("26") and scenario.rule_id == "high_hospitalization_burden"
        for scenario in uf_scenarios
    )
    assert all(scenario.rule_id != "high_hospitalization_burden" for scenario in national_scenarios)


def test_initialize_database_migrates_legacy_import_run_scope_columns(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE import_runs ("
                "import_run_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "source_id VARCHAR(64) NOT NULL, "
                "status VARCHAR(32) NOT NULL, "
                "started_at DATETIME NOT NULL, "
                "finished_at DATETIME, "
                "row_count INTEGER NOT NULL DEFAULT 0, "
                "message TEXT NOT NULL DEFAULT ''"
                ")"
            )
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO import_runs "
                "(source_id, status, started_at, row_count, message) "
                "VALUES (:source_id, :status, :started_at, :row_count, :message)"
            ),
            {
                "source_id": "sih_sus",
                "status": "success",
                "started_at": "2023-01-01",
                "row_count": 1,
                "message": "legacy",
            },
        )

    initialize_database(engine)
    with engine.connect() as connection:
        legacy_row = connection.execute(
            text("SELECT year, geographic_scope, loaded_months FROM import_runs")
        ).one()

    database_inspector = inspect(engine)
    column_names = {column["name"] for column in database_inspector.get_columns("import_runs")}
    index_names = {index["name"] for index in database_inspector.get_indexes("import_runs")}
    engine.dispose()

    assert {"year", "geographic_scope", "loaded_months"} <= column_names
    assert "ix_import_runs_source_year_scope" in index_names
    assert tuple(legacy_row) == (None, None, None)


def test_initialize_database_migrates_legacy_indicator_provenance(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'legacy-provenance.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE population_denominators ("
                "territory_id VARCHAR(20) NOT NULL, "
                "year INTEGER NOT NULL, "
                "stratifier VARCHAR(80) NOT NULL, "
                "population INTEGER NOT NULL, "
                "source_id VARCHAR(80) NOT NULL, "
                "PRIMARY KEY (territory_id, year, stratifier)"
                ")"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE indicator_values ("
                "indicator_id VARCHAR(120) NOT NULL, "
                "territory_id VARCHAR(20) NOT NULL, "
                "year INTEGER NOT NULL, "
                "value FLOAT, "
                "numerator_value FLOAT NOT NULL, "
                "denominator_value FLOAT NOT NULL, "
                "is_suppressed BOOLEAN NOT NULL, "
                "source_ids JSON NOT NULL, "
                "caveats TEXT NOT NULL, "
                "computed_at DATETIME NOT NULL, "
                "PRIMARY KEY (indicator_id, territory_id, year)"
                ")"
            )
        )
        connection.execute(
            text(
                "INSERT INTO population_denominators VALUES "
                "('2304400', 2023, 'total', 100000, 'ibge_population')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO indicator_values VALUES "
                "('tb_incidence_per_100k', '2304400', 2023, 10, 10, 100000, "
                "0, '[\"sinan_tb\", \"ibge_population\"]', '', '2023-12-31')"
            )
        )

    initialize_database(engine)
    with engine.connect() as connection:
        population_row = connection.execute(
            text("SELECT source_year, source_kind FROM population_denominators")
        ).one()
        indicator_row = connection.execute(
            text("SELECT denominator_year, source_provenance FROM indicator_values")
        ).one()
    engine.dispose()

    assert tuple(population_row) == (None, None)
    assert tuple(indicator_row) == (None, None)


def test_population_and_indicator_provenance_round_trip(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'provenance.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    population = PopulationDenominator(
        "2304400",
        2023,
        100_000,
        "ibge_population",
        source_year=2022,
        source_kind="census",
    )
    value = IndicatorValue(
        "tb_incidence_per_100k",
        "2304400",
        2023,
        10.0,
        10,
        100_000,
        False,
        ("sinan_tb", "ibge_population"),
        "fixture",
        denominator_year=2022,
        source_provenance=(
            SourceProvenance("sinan_tb", 2023, "preliminary", "notification", "a" * 64),
            SourceProvenance("ibge_population", 2022, "final", "census", "b" * 64),
        ),
    )
    with session_factory() as session:
        save_populations(session, [population])
        save_indicator_values(session, [value], 2023)
        session.commit()
        loaded_population = load_populations(session, 2023)[0]
        loaded_value = load_indicator_values(session, 2023)[0]
    engine.dispose()

    assert loaded_population == population
    assert loaded_value.denominator_year == 2022
    assert loaded_value.source_provenance == value.source_provenance


def test_initialize_database_migrates_legacy_scenario_metadata(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'legacy-scenarios.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE scenario_rules ("
                "rule_id VARCHAR(120) PRIMARY KEY, "
                "name VARCHAR(200) NOT NULL, "
                "indicator_id VARCHAR(120) NOT NULL, "
                "threshold_method VARCHAR(80) NOT NULL, "
                "comparison_group VARCHAR(120) NOT NULL, "
                "severity VARCHAR(40) NOT NULL, "
                "direction VARCHAR(40) NOT NULL, "
                "explanation_template TEXT NOT NULL, "
                "strategy_ids JSON NOT NULL, "
                "minimum_count INTEGER NOT NULL"
                ")"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE territory_scenarios ("
                "territory_id VARCHAR(20) NOT NULL, "
                "year INTEGER NOT NULL, "
                "comparison_scope VARCHAR(20) NOT NULL, "
                "rule_id VARCHAR(120) NOT NULL, "
                "scenario_id VARCHAR(120) NOT NULL, "
                "severity VARCHAR(40) NOT NULL, "
                "score FLOAT NOT NULL, "
                "explanation TEXT NOT NULL, "
                "indicator_id VARCHAR(120) NOT NULL, "
                "indicator_value FLOAT NOT NULL, "
                "threshold_value FLOAT NOT NULL, "
                "PRIMARY KEY (territory_id, year, comparison_scope, rule_id)"
                ")"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE recommendations ("
                "territory_id VARCHAR(20) NOT NULL, "
                "year INTEGER NOT NULL, "
                "comparison_scope VARCHAR(20) NOT NULL, "
                "strategy_id VARCHAR(120) NOT NULL, "
                "rule_id VARCHAR(120) NOT NULL, "
                "priority VARCHAR(40) NOT NULL, "
                "explanation TEXT NOT NULL, "
                "PRIMARY KEY (territory_id, year, comparison_scope, strategy_id, rule_id)"
                ")"
            )
        )
        connection.execute(
            text(
                "INSERT INTO scenario_rules VALUES ("
                "'high_incidence', 'High incidence', 'tb_incidence_per_100k', "
                "'p75', 'selected_uf_year', 'high', 'high_bad', "
                "'fixture', '[]', 5)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO territory_scenarios VALUES ("
                "'2304400', 2023, 'uf', 'high_incidence', 'high_incidence', "
                "'high', 3.0, 'fixture', 'tb_incidence_per_100k', 90.0, 80.0)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO recommendations VALUES ("
                "'2304400', 2023, 'uf', 'active_case_finding', "
                "'high_incidence', 'high', 'fixture')"
            )
        )

    initialize_database(engine)

    inspector = inspect(engine)
    rule_columns = {item["name"] for item in inspector.get_columns("scenario_rules")}
    scenario_columns = {item["name"] for item in inspector.get_columns("territory_scenarios")}
    recommendation_columns = {item["name"] for item in inspector.get_columns("recommendations")}
    with engine.connect() as connection:
        rule_dimension = connection.execute(
            text("SELECT ranking_dimension FROM scenario_rules")
        ).scalar_one()
        scenario_dimension = connection.execute(
            text("SELECT ranking_dimension FROM territory_scenarios")
        ).scalar_one()
        trigger_rule_ids = connection.execute(
            text("SELECT trigger_rule_ids FROM recommendations")
        ).scalar_one()
        rule_metadata = connection.execute(
            text("SELECT minimum_coverage_ratio, review_status FROM scenario_rules")
        ).one()
        scenario_review_status = connection.execute(
            text("SELECT review_status FROM territory_scenarios")
        ).scalar_one()
    engine.dispose()

    assert "ranking_dimension" in rule_columns
    assert "ranking_dimension" in scenario_columns
    assert "trigger_rule_ids" in recommendation_columns
    assert "minimum_coverage_ratio" in rule_columns
    assert "review_status" in rule_columns
    assert "review_status" in scenario_columns
    assert "scenario_rule_evaluations" in inspector.get_table_names()
    assert rule_dimension == "high_incidence"
    assert scenario_dimension == "high_incidence"
    assert trigger_rule_ids == '["high_incidence"]'

    assert tuple(rule_metadata) == (0.0, None)
    assert scenario_review_status is None


def test_national_and_uf_scenario_scopes_coexist(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [
                *fixture_scope_territories("23", "CE", "23", [90, 80, 70, 60, 50]),
                *fixture_scope_territories("26", "PE", "26", [10, 9, 8, 7, 6]),
            ],
        )
        save_indicator_values(
            session,
            [
                *fixture_incidence_values("23", [90, 80, 70, 60, 50]),
                *fixture_incidence_values("26", [10, 9, 8, 7, 6]),
            ],
            2023,
        )
        scenario_count, recommendation_count = build_and_store_scenarios(
            session, Mvp1Config(uf="BR", year=2023, minimum_count=5)
        )
        session.commit()

        pe_uf_context = dashboard_context(session, 2023, "PE", "uf")
        pe_national_context = dashboard_context(session, 2023, "PE", "national")
        br_context = dashboard_context(session, 2023, "BR", "national")
    engine.dispose()

    assert scenario_count > 0
    assert recommendation_count > 0
    assert pe_uf_context["comparison_scope"] == "uf"
    assert pe_national_context["comparison_scope"] == "national"
    assert pe_uf_context["ranking"]
    assert pe_national_context["ranking"] == []
    assert br_context["territory_count"] == 10
    assert br_context["ranking"][0]["territory_id"].startswith("23")

    with TestClient(create_app(database_url)) as client:
        br_map = client.get("/api/map/municipalities?uf=BR&year=2023&comparison_scope=national")
        pe_map_uf = client.get("/api/map/municipalities?uf=PE&year=2023&comparison_scope=uf")
        pe_map_national = client.get(
            "/api/map/municipalities?uf=PE&year=2023&comparison_scope=national"
        )
        pe_report_uf = client.get("/api/territories/2600001/report?year=2023&comparison_scope=uf")
        pe_report_national = client.get(
            "/api/territories/2600001/report?year=2023&comparison_scope=national"
        )

    assert br_map.status_code == 200
    assert pe_map_uf.status_code == 200
    assert pe_map_national.status_code == 200
    assert pe_report_uf.status_code == 200
    assert pe_report_national.status_code == 200
    assert pe_report_uf.json()["resistance_surveillance"]["comparison_scope"] == "uf"
    assert pe_report_national.json()["resistance_surveillance"]["comparison_scope"] == "national"
    assert all(
        row["data_status"] == "missing"
        for row in pe_report_national.json()["resistance_surveillance"]["signals"]
    )
    assert br_map.json()["metadata"]["comparison_scope"] == "national"
    assert len(br_map.json()["features"]) == 10
    pe_uf_scores = [
        feature["properties"]["priority_score"] for feature in pe_map_uf.json()["features"]
    ]
    pe_national_scores = [
        feature["properties"]["priority_score"] for feature in pe_map_national.json()["features"]
    ]
    assert max(pe_uf_scores) > 0
    assert max(pe_national_scores) == 0


def test_public_api_returns_aggregate_indicators_and_ranking(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        indicators = client.get("/api/indicators?uf=CE&year=2023")
        rankings = client.get("/api/rankings?uf=CE&year=2023")
        report = client.get("/api/territories/2304400/report?year=2023")
        report_other_year = client.get("/api/territories/2304400/report?year=2022")
        report_pt = client.get("/api/territories/2304400/report?year=2023&lang=pt")
        missing_report = client.get("/api/territories/9999999/report?year=2023")

    assert indicators.status_code == 200
    assert rankings.status_code == 200
    assert report.status_code == 200
    assert report_pt.status_code == 200
    assert missing_report.status_code == 404
    assert report_other_year.status_code == 200
    incidence = next(
        row for row in indicators.json() if row["indicator_id"] == "tb_incidence_per_100k"
    )
    assert incidence["unit"] == "per_100k"
    assert incidence["direction"] == "high_bad"
    assert rankings.json()[0]["territory_id"] == "2304400"
    assert report.json()["territory_name"] == "Fortaleza"
    resistance_profile = report.json()["resistance_surveillance"]
    assert resistance_profile["ranking_effect"] == "none"
    assert (
        resistance_profile["confirmed_resistance_status"]
        == "not_available_in_public_aggregate_sources"
    )
    assert {row["signal_id"] for row in resistance_profile["signals"]} == {
        "high_retreatment",
        "low_culture_use_among_retreatment",
        "low_trm_tb_use",
    }
    assert all(
        row["data_status"] == "missing"
        for row in report_other_year.json()["resistance_surveillance"]["signals"]
    )
    resistance_profile_pt = report_pt.json()["resistance_surveillance"]
    assert resistance_profile_pt["confirmed_resistance_status_label"] == (
        "Não disponível nas fontes públicas agregadas"
    )
    assert resistance_profile_pt["ranking_effect_label"] == ("Não altera o ranking de priorização")
    incidence_pt = next(
        row
        for row in report_pt.json()["indicators"]
        if row["indicator_id"] == "tb_incidence_per_100k"
    )
    assert incidence_pt["indicator_name"] == "Incidência de TB"
    assert "Recomendado porque" in report_pt.json()["recommendations"][0]["explanation"]


def test_public_api_exposes_auditable_localized_indicator_history(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    history_values = [
        IndicatorValue(
            indicator_id="tb_incidence_per_100k",
            territory_id="2304400",
            year=2021,
            value=10.0,
            numerator_value=10,
            denominator_value=100_000,
            is_suppressed=False,
            source_ids=("sinan_tb", "ibge_population"),
            caveats="Annual public aggregate.",
            denominator_year=2021,
            source_provenance=(
                SourceProvenance(
                    "sinan_tb",
                    reference_year=2021,
                    release_status="preliminary",
                    dataset_kind="notification",
                    artifact_sha256="a" * 64,
                ),
                SourceProvenance(
                    "ibge_population",
                    reference_year=2021,
                    release_status="final",
                    dataset_kind="estimate",
                ),
            ),
        ),
        IndicatorValue(
            indicator_id="tb_incidence_per_100k",
            territory_id="2304400",
            year=2022,
            value=None,
            numerator_value=3,
            denominator_value=100_000,
            is_suppressed=True,
            source_ids=("sinan_tb", "ibge_population"),
            caveats="Annual public aggregate.",
            denominator_year=2022,
            source_provenance=(
                SourceProvenance(
                    "sinan_tb",
                    reference_year=2022,
                    release_status="preliminary",
                    dataset_kind="notification",
                ),
                SourceProvenance(
                    "ibge_population",
                    reference_year=2022,
                    release_status="final",
                    dataset_kind="estimate",
                ),
            ),
        ),
        IndicatorValue(
            indicator_id="tb_incidence_per_100k",
            territory_id="2304400",
            year=2023,
            value=12.0,
            numerator_value=12,
            denominator_value=100_000,
            is_suppressed=False,
            source_ids=("sinan_tb", "ibge_population"),
            caveats="Annual public aggregate.",
            denominator_year=2022,
            source_provenance=(
                SourceProvenance(
                    "sinan_tb",
                    reference_year=2023,
                    release_status="final",
                    dataset_kind="notification",
                ),
                SourceProvenance(
                    "ibge_population",
                    reference_year=2022,
                    release_status="final",
                    dataset_kind="census",
                ),
            ),
        ),
    ]
    with session_factory() as session:
        save_indicator_history_values(
            session,
            history_values,
            indicator_id="tb_incidence_per_100k",
            start_year=2018,
            end_year=2023,
            replace_territory_ids={"2304400"},
        )
        session.commit()
    engine.dispose()

    history_url = (
        "/api/territorial/history?territory_id=2304400&"
        "indicator_id=tb_incidence_per_100k&year_from=2018&year_to=2023&lang=pt"
    )
    with TestClient(create_app(database_url)) as client:
        history_response = client.get(history_url)
        report_response = client.get("/api/territories/2304400/report?year=2023&lang=pt")
        reversed_range = client.get(history_url.replace("year_from=2018", "year_from=2024"))
        oversized_range = client.get(history_url.replace("year_from=2018", "year_from=2000"))
        unknown_indicator = client.get(history_url.replace("tb_incidence_per_100k", "unknown"))
        unknown_territory = client.get(history_url.replace("2304400", "9999999"))

    assert history_response.status_code == 200
    assert report_response.status_code == 200
    history = history_response.json()
    assert report_response.json()["incidence_history"] == history
    assert history["indicator_name"] == "Incidência de TB"
    assert history["coverage"]["status"] == "partial"
    assert history["coverage"]["status_label"] == "parcial"
    assert [point["status"] for point in history["points"]] == [
        "missing",
        "missing",
        "missing",
        "available",
        "suppressed",
        "available",
    ]
    suppressed = history["points"][4]
    assert suppressed["value"] is None
    assert suppressed["numerator_value"] is None
    assert suppressed["denominator_value"] == 100_000
    assert suppressed["status_label"] == "suprimido"
    assert history["points"][3]["source_provenance"][0]["source_label"] == ("SINAN-TB / DATASUS")
    assert history["points"][3]["source_provenance"][0]["release_status_label"] == ("preliminar")
    flags = {flag["code"]: flag for flag in history["comparability_flags"]}
    assert flags["missing_year"]["years"] == [2018, 2019, 2020]
    assert "observação armazenada" in flags["missing_year"]["detail"]
    assert flags["suppressed_year"]["years"] == [2022]
    assert flags["denominator_year_mismatch"]["years"] == [2023]
    assert flags["source_release_changed"]["years"] == [2023]
    assert flags["denominator_method_changed"]["years"] == [2023]
    assert reversed_range.status_code == 422
    assert oversized_range.status_code == 422
    assert unknown_indicator.status_code == 404
    assert unknown_territory.status_code == 404


def test_public_api_returns_geometry_and_enriched_map_properties(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    with TestClient(create_app(database_url)) as client:
        geometry = client.get("/api/geo/municipalities?uf=CE")
        map_response = client.get("/api/map/municipalities?uf=CE&year=2023")
        map_response_pt = client.get("/api/map/municipalities?uf=CE&year=2023&lang=pt")
        product_context = client.get("/api/territorial/context?uf=CE&year=2023&lang=pt")
        product_map = client.get("/api/territorial/map?uf=CE&year=2023&lang=pt")

    assert geometry.status_code == 200
    assert map_response.status_code == 200
    assert map_response_pt.status_code == 200
    assert product_context.status_code == 200
    assert product_map.status_code == 200
    assert product_context.json()["territory_count"] == 6
    assert product_map.json()["metadata"]["feature_count"] == 6
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


def test_public_subterritories_do_not_pollute_municipality_context(tmp_path: Path) -> None:
    database_path = tmp_path / "mvp1.db"
    database_url = f"sqlite:///{database_path}"
    populate_database(database_url)

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        save_reference_subterritories(session)
        save_facilities(
            session,
            [
                Facility("cnes-001", "2304400", "UBS Centro", "UBS", True),
                Facility("cnes-002", "2303709", "UBS Caucaia", "UBS", True),
            ],
        )
        session.commit()
        context = dashboard_context(session, 2023, "CE")
    engine.dispose()

    readiness = context["readiness"]
    health_readiness = context["health_territory_readiness"]
    assert context["territory_count"] == 6
    assert readiness["geometry"]["geometry_count"] == 6
    assert readiness["geometry"]["territory_count"] == 6
    assert context["ranking"][0]["territory_id"] == "2304400"
    assert health_readiness["public_subterritory_geometry"]["status"] == "ready"
    assert health_readiness["public_subterritory_geometry"]["feature_count"] == 2
    assert health_readiness["cnes_facility_context"]["status"] == "ready"
    assert health_readiness["cnes_facility_context"]["facility_count"] == 2
    assert health_readiness["official_health_territory_boundaries"]["status"] == "missing"
    assert health_readiness["tb_health_territory_indicators"]["status"] == "missing"

    with TestClient(create_app(database_url)) as client:
        territories = client.get("/api/territories?uf=CE")
        geometry = client.get("/api/geo/municipalities?uf=CE")
        municipalities = client.get("/api/map/municipalities?uf=CE&year=2023")
        subterritories = client.get(
            "/api/map/subterritories?parent_id=2304400&"
            "territory_type=neighborhood_reference&lang=pt"
        )
        missing_subterritories = client.get(
            "/api/map/subterritories?parent_id=2312908&territory_type=neighborhood_reference"
        )
        subterritory_report = client.get("/api/territories/2304400-bairro-001/report?year=2023")

    assert territories.status_code == 200
    assert geometry.status_code == 200
    assert municipalities.status_code == 200
    assert subterritories.status_code == 200
    assert missing_subterritories.status_code == 200
    assert subterritory_report.status_code == 404
    assert len(territories.json()) == 6
    assert len(geometry.json()["features"]) == 6
    assert len(municipalities.json()["features"]) == 6
    assert all(
        feature["properties"]["territory_id"] != "2304400-bairro-001"
        for feature in municipalities.json()["features"]
    )

    payload = subterritories.json()
    assert payload["metadata"] == {
        "parent_id": "2304400",
        "territory_type": "neighborhood_reference",
        "feature_count": 2,
        "drawable_geometry_count": 2,
        "status": "ready",
        "data_level": "public_reference",
        "caveat": (
            "Bairros são referência geográfica pública; indicadores e priorização de TB "
            "permanecem no nível municipal."
        ),
    }
    assert [feature["properties"]["territory_id"] for feature in payload["features"]] == [
        "2304400-bairro-001",
        "2304400-bairro-002",
    ]
    assert "indicators" not in payload["features"][0]["properties"]
    assert missing_subterritories.json()["features"] == []
    assert missing_subterritories.json()["metadata"]["status"] == "missing"


def test_dashboard_renders_product_shell_controls_and_existing_sections(
    tmp_path: Path, monkeypatch: Any
) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    monkeypatch.setattr(web_app, "FRONTEND_DIST_DIR", tmp_path / "missing-dist")
    with TestClient(create_app(database_url)) as client:
        default_response = client.get("/")
        response = client.get("/territorios?uf=CE&year=2023")
        english_response = client.get("/territorios?uf=CE&year=2023&lang=en")

    assert default_response.status_code == 200
    assert response.status_code == 200
    assert english_response.status_code == 200
    assert "BR 2023" in default_response.text
    html = response.text
    english_html = english_response.text
    assert "Análise territorial" in html
    assert "Acompanhamento da atenção" in html
    assert "MVP1" not in html
    assert "MVP2" not in html
    assert "English" in html
    assert 'id="uf-control"' in html
    assert 'id="year-control"' in html
    assert "dado público agregado" in html
    assert "Dados e governança" in html
    assert "Prontidão dos dados" in html
    assert "Fontes públicas" in html
    assert "Geometria" in html
    assert "Validação dos indicadores" in html
    assert "Sinais gerados" in html
    assert "Territórios de saúde" in html
    assert "Limites oficiais de territórios de saúde" in html
    assert "Indicadores de TB por território de saúde" in html
    assert "Visualização do mapa" in html
    assert "Prioridade municipal" in html
    assert "Bairros de referência" in html
    assert (
        "Bairros são referência geográfica pública; indicadores e priorização de TB "
        "permanecem no nível municipal."
    ) in html
    assert "Territorial analysis" in english_html
    assert "Care follow-up" in english_html
    assert "MVP1" not in english_html
    assert "MVP2" not in english_html
    assert "public aggregate" in english_html
    assert "Data readiness" in english_html
    assert "Health territories" in english_html
    assert "Reference neighborhoods" in english_html
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
    assert "Municípios prioritários" in html
    assert "Atualização das fontes" in html
    assert "selectTerritory" in html
    assert "highlightRankingRow" in html
    assert "highlightPolygon" in html
    assert "searchMunicipality" in html
    assert "syncSubterritoriesForSelection" in html
    assert "styleSubterritoryFeature" in html
    assert "/api/map/subterritories" in html
    assert "Por que foi sinalizado" in html
    assert "Resposta recomendada" in html
    assert "Indicadores" in html
    assert "Ressalvas" in html


def test_legacy_concept_routes_redirect_without_built_spa(tmp_path: Path, monkeypatch: Any) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    monkeypatch.setattr(web_app, "FRONTEND_DIST_DIR", tmp_path / "missing-dist")

    with TestClient(create_app(database_url)) as client:
        territorial_redirect = client.get(
            "/conceito/territorios?uf=CE&year=2023&lang=en",
            follow_redirects=False,
        )
        operations_redirect = client.get(
            "/conceito/acompanhamento?year=2023&severity=high&lang=pt",
            follow_redirects=False,
        )
        territorial_page = client.get("/territorios?uf=CE&year=2023")
        operations_page = client.get("/acompanhamento?year=2023")
        api_response = client.get("/api/territorial/context?uf=CE&year=2023&lang=pt")

    assert territorial_redirect.status_code == 307
    assert territorial_redirect.headers["location"] == ("/territorios?uf=CE&year=2023&lang=en")
    assert operations_redirect.status_code == 307
    assert operations_redirect.headers["location"] == (
        "/acompanhamento?year=2023&severity=high&lang=pt"
    )
    assert territorial_page.status_code == 200
    assert operations_page.status_code == 200
    assert api_response.status_code == 200


def test_territorial_load_year_endpoint_runs_public_pipeline_without_auto_navigation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    calls: list[tuple[str, int]] = []

    def fake_prepare_territorial_data(
        session_factory: Any,
        config: Any,
        *,
        sih_all_months: bool,
        timeout: int,
        progress: Any | None = None,
    ) -> TerritorialPreparationResult:
        calls.append((config.uf, config.year))
        if progress is not None:
            progress(
                {
                    "stage": "download",
                    "step_index": 1,
                    "message": "1/4 baixando: SINAN-TB Brazil 2024 preliminary",
                }
            )
        return TerritorialPreparationResult(
            download={
                "requested_file_count": 4,
                "downloaded_file_count": 2,
                "existing_file_count": 2,
                "failed_file_count": 0,
                "failures": [],
                "sih_all_months": sih_all_months,
                "timeout": timeout,
            },
            result_status="ready",
            indicator_count=12,
            scenario_count=5,
            recommendation_count=5,
            sih_coverage_complete=True,
        )

    monkeypatch.setattr(web_app, "prepare_territorial_data", fake_prepare_territorial_data)

    with TestClient(create_app(database_url)) as client:
        response = client.post("/api/territorial/load-year?uf=CE&year=2024&lang=pt")
        job_id = response.json()["job_id"]
        status_response = client.get(f"/api/territorial/load-year/{job_id}")

    assert response.status_code == 200
    start_payload = response.json()
    assert start_payload["status"] == "queued"
    assert start_payload["uf"] == "CE"
    assert start_payload["year"] == 2024
    assert start_payload["sih_all_months"] is True

    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["status"] == "complete"
    assert payload["result_status"] == "ready"
    assert payload["download"]["downloaded_file_count"] == 2
    assert payload["indicator_count"] == 12
    assert payload["scenario_count"] == 5
    assert payload["step_index"] == payload["step_count"]
    assert calls == [("CE", 2024)]


def test_fastapi_serves_built_spa_without_capturing_api_routes(
    tmp_path: Path, monkeypatch: Any
) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    populate_database(database_url)
    dist_dir = tmp_path / "dist"
    asset_dir = dist_dir / "assets"
    asset_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text(
        '<!doctype html><div id="root">SPA TB-IA</div>'
        '<script type="module" src="/static/app/assets/app.js"></script>',
        encoding="utf-8",
    )
    (asset_dir / "app.js").write_text("console.log('tbia');", encoding="utf-8")
    monkeypatch.setattr(web_app, "FRONTEND_DIST_DIR", dist_dir)

    with TestClient(web_app.create_app(database_url)) as client:
        territorial_page = client.get("/territorios?uf=CE&year=2023")
        operations_page = client.get("/acompanhamento?year=2023")
        concept_territorial_page = client.get(
            "/conceito/territorios?uf=BR&year=2023",
            follow_redirects=False,
        )
        concept_operations_page = client.get(
            "/conceito/acompanhamento?year=2023",
            follow_redirects=False,
        )
        asset_response = client.get("/static/app/assets/app.js")
        api_response = client.get("/api/territorial/context?uf=CE&year=2023&lang=pt")

    assert territorial_page.status_code == 200
    assert operations_page.status_code == 200
    assert concept_territorial_page.status_code == 307
    assert concept_territorial_page.headers["location"] == ("/territorios?uf=BR&year=2023")
    assert concept_operations_page.status_code == 307
    assert concept_operations_page.headers["location"] == ("/acompanhamento?year=2023")
    assert asset_response.status_code == 200
    assert api_response.status_code == 200
    assert "SPA TB-IA" in territorial_page.text
    assert "SPA TB-IA" in operations_page.text
    assert api_response.json()["territory_count"] == 6


def save_reference_subterritories(session: Any) -> None:
    save_territories(
        session,
        [
            Territory(
                "2304400-bairro-001",
                "Centro",
                "neighborhood_reference",
                "23",
                "CE",
                parent_id="2304400",
                geometry=fixture_geometry(0.01),
            ),
            Territory(
                "2304400-bairro-002",
                "Mucuripe",
                "neighborhood_reference",
                "23",
                "CE",
                parent_id="2304400",
                geometry=fixture_geometry(0.02),
            ),
        ],
    )


def fixture_scope_territories(
    prefix: str, uf: str, uf_code: str, values: list[int]
) -> list[Territory]:
    return [
        Territory(
            f"{prefix}{index:05d}",
            f"{uf} Municipio {index}",
            "municipality",
            uf_code,
            uf,
            geometry=fixture_geometry(index / 100),
        )
        for index, _ in enumerate(values, start=1)
    ]


def fixture_incidence_values(prefix: str, values: list[int]) -> list[IndicatorValue]:
    return [
        IndicatorValue(
            indicator_id="tb_incidence_per_100k",
            territory_id=f"{prefix}{index:05d}",
            year=2023,
            value=float(value),
            numerator_value=float(value),
            denominator_value=100_000.0,
            is_suppressed=False,
            source_ids=("fixture",),
            caveats="fixture",
        )
        for index, value in enumerate(values, start=1)
    ]


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


def test_diagnostic_scenario_readiness_is_persisted_and_localized(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'diagnostic-readiness.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    territory_values = list(range(20))
    diagnostic_values = [
        IndicatorValue(
            indicator_id=indicator_id,
            territory_id=f"23{index:05d}",
            year=2023,
            value=float(100 - index),
            numerator_value=float(100 - index),
            denominator_value=100.0,
            is_suppressed=False,
            source_ids=("fixture",),
            caveats="fixture",
        )
        for indicator_id, count in (
            ("hiv_testing_proportion", 20),
            ("trm_tb_use_proportion", 10),
            ("culture_use_among_retreatment", 9),
        )
        for index in range(1, count + 1)
    ]

    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            fixture_scope_territories("23", "CE", "23", territory_values),
        )
        save_indicator_values(session, diagnostic_values, 2023)
        build_and_store_scenarios(session, Mvp1Config(uf="CE", year=2023))
        session.commit()
        context = dashboard_context(session, 2023, "CE")
        scenarios = load_territory_scenarios(session, 2023, "uf")
    engine.dispose()

    diagnostic_evaluations = {
        row["rule_id"]: row
        for row in context["scenario_rule_evaluations"]
        if row["rule_id"]
        in {
            "low_hiv_testing",
            "low_trm_tb_use",
            "low_culture_use_among_retreatment",
        }
    }
    assert {rule_id: row["status"] for rule_id, row in diagnostic_evaluations.items()} == {
        "low_hiv_testing": "ready",
        "low_trm_tb_use": "ready",
        "low_culture_use_among_retreatment": "insufficient_comparison",
    }
    assert diagnostic_evaluations["low_hiv_testing"]["available_count"] == 20
    assert diagnostic_evaluations["low_trm_tb_use"]["available_count"] == 10
    assert diagnostic_evaluations["low_culture_use_among_retreatment"]["available_count"] == 9
    assert context["readiness"]["diagnostic_scenario_rules"] == {
        "label": "Diagnostic coverage prioritization",
        "status": "partial",
        "ready_count": 2,
        "evaluation_count": 3,
        "insufficient_count": 1,
        "missing_count": 0,
        "detail": (
            "2/3 diagnostic rule evaluations ready; "
            "1 with insufficient comparison coverage; 0 missing indicators"
        ),
    }
    diagnostic_scenarios = [
        scenario
        for scenario in scenarios
        if scenario.rule_id
        in {
            "low_hiv_testing",
            "low_trm_tb_use",
            "low_culture_use_among_retreatment",
        }
    ]
    assert {scenario.rule_id for scenario in diagnostic_scenarios} == {
        "low_hiv_testing",
        "low_trm_tb_use",
    }
    assert all(
        scenario.review_status == "pending_domain_review" for scenario in diagnostic_scenarios
    )

    with TestClient(create_app(database_url)) as client:
        response = client.get("/api/territorial/context?uf=CE&year=2023&lang=pt")

    assert response.status_code == 200
    localized_evaluations = {
        row["rule_id"]: row for row in response.json()["scenario_rule_evaluations"]
    }
    assert localized_evaluations["low_hiv_testing"]["rule_name"] == ("baixa testagem para HIV")
    assert localized_evaluations["low_hiv_testing"]["status_label"] == "pronto"
    assert localized_evaluations["low_hiv_testing"]["review_status_label"] == (
        "revisão de domínio pendente"
    )


def test_diagnostic_rules_are_ready_for_uf_and_national_comparisons(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{tmp_path / 'diagnostic-national.db'}"
    processed_dir = tmp_path / "processed"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    diagnostic_rule_ids = {
        "low_hiv_testing",
        "low_trm_tb_use",
        "low_culture_use_among_retreatment",
    }
    indicator_ids = {
        "hiv_testing_proportion",
        "trm_tb_use_proportion",
        "culture_use_among_retreatment",
    }
    diagnostic_values = [
        IndicatorValue(
            indicator_id=indicator_id,
            territory_id=f"{prefix}{index:05d}",
            year=2023,
            value=float(21 - index),
            numerator_value=float(21 - index),
            denominator_value=100.0,
            is_suppressed=False,
            source_ids=("fixture",),
            caveats="fixture",
        )
        for prefix in ("23", "26")
        for indicator_id in indicator_ids
        for index in range(1, 21)
    ]

    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [
                *fixture_scope_territories("23", "CE", "23", list(range(20))),
                *fixture_scope_territories("26", "PE", "26", list(range(20))),
            ],
        )
        save_indicator_values(session, diagnostic_values, 2023)
        build_and_store_scenarios(
            session,
            Mvp1Config(uf="BR", year=2023, processed_dir=processed_dir),
        )
        session.commit()
        ce_context = dashboard_context(session, 2023, "CE", "uf")
        pe_context = dashboard_context(session, 2023, "PE", "uf")
        national_context = dashboard_context(session, 2023, "BR", "national")
        uf_scenarios = load_territory_scenarios(session, 2023, "uf")
        national_scenarios = load_territory_scenarios(session, 2023, "national")
    engine.dispose()

    for expected_scope, context in (
        ("CE", ce_context),
        ("PE", pe_context),
        ("BR", national_context),
    ):
        diagnostic_evaluations = [
            row
            for row in context["scenario_rule_evaluations"]
            if row["rule_id"] in diagnostic_rule_ids
        ]
        assert {row["rule_id"] for row in diagnostic_evaluations} == diagnostic_rule_ids
        assert {row["geographic_scope"] for row in diagnostic_evaluations} == {expected_scope}
        assert all(row["status"] == "ready" for row in diagnostic_evaluations)
        assert all(row["available_count"] >= 20 for row in diagnostic_evaluations)

    assert {
        scenario.rule_id for scenario in uf_scenarios if scenario.rule_id in diagnostic_rule_ids
    } == diagnostic_rule_ids
    assert {
        scenario.rule_id
        for scenario in national_scenarios
        if scenario.rule_id in diagnostic_rule_ids
    } == diagnostic_rule_ids
    assert all(
        scenario.review_status == "pending_domain_review"
        for scenario in [*uf_scenarios, *national_scenarios]
        if scenario.rule_id in diagnostic_rule_ids
    )

    impact_path = processed_dir / "validation" / "diagnostic_ranking_impact_br_2023.json"
    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    assert set(impact["comparisons"]) == {"uf", "national"}
    assert impact["comparisons"]["uf"]["scenario_counts"]["diagnostic"] > 0
    assert impact["comparisons"]["national"]["scenario_counts"]["diagnostic"] > 0
