from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from tbia.cli import app
from tbia.mvp2 import (
    Mvp2Config,
    build_and_store_operational_alerts,
    generate_mvp2_sample_data,
    ingest_local_data,
)
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    initialize_database,
    load_local_tb_cases,
    load_operational_alerts,
    mvp2_summary,
)
from tbia.web.app import create_app


def test_mvp2_storage_and_api_expose_operational_alerts_without_patient_pseudonyms(
    tmp_path: Path,
) -> None:
    database_url = populate_mvp2_database(tmp_path)

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        cases = load_local_tb_cases(session, 2023)
        alerts = load_operational_alerts(session, 2023)
        summary = mvp2_summary(session, 2023)
    engine.dispose()

    assert len(cases) == 3
    assert len(alerts) >= 4
    assert summary["alert_count"] == len(alerts)
    assert summary["open_alert_count"] == len(alerts)

    with TestClient(create_app(database_url)) as client:
        summary_response = client.get("/api/mvp2/summary?year=2023")
        alerts_response = client.get("/api/mvp2/alerts?year=2023&severity=high")
        page_response = client.get("/mvp2?year=2023&severity=high")
        english_page_response = client.get("/mvp2?year=2023&severity=high&lang=en")

    assert summary_response.status_code == 200
    assert alerts_response.status_code == 200
    assert page_response.status_code == 200
    assert english_page_response.status_code == 200
    assert summary_response.json()["alert_count"] == len(alerts)
    assert all(row["severity"] == "high" for row in alerts_response.json())
    assert "pseudonymized_patient_id" not in alerts_response.text
    assert "PAT-" not in alerts_response.text
    assert "MVP1 Territorial" in page_response.text
    assert "MVP2 Operações" in page_response.text
    assert "demonstração sintética/pseudonimizada" in page_response.text
    assert "MVP2 Operations" in english_page_response.text
    assert "synthetic/pseudonymized demo" in english_page_response.text

    first_alert_id = alerts_response.json()[0]["alert_id"]
    with TestClient(create_app(database_url)) as client:
        detail_response = client.get(f"/api/mvp2/alerts/{first_alert_id}")
        missing_response = client.get("/api/mvp2/alerts/missing-alert")

    assert detail_response.status_code == 200
    assert detail_response.json()["alert_id"] == first_alert_id
    assert missing_response.status_code == 404


def test_mvp2_cli_smoke_generates_ingests_and_builds_alerts(tmp_path: Path) -> None:
    runner = CliRunner()
    raw_dir = tmp_path / "municipal_demo"
    database_url = f"sqlite:///{tmp_path / 'cli.db'}"

    generated = runner.invoke(app, ["generate-mvp2-sample-data", "--output-dir", str(raw_dir)])
    ingested = runner.invoke(
        app,
        [
            "ingest-local",
            "--raw-dir",
            str(raw_dir),
            "--year",
            "2023",
            "--database-url",
            database_url,
        ],
    )
    built = runner.invoke(
        app,
        [
            "build-operational-alerts",
            "--year",
            "2023",
            "--reference-date",
            "2026-06-29",
            "--database-url",
            database_url,
        ],
    )

    assert generated.exit_code == 0, generated.output
    assert ingested.exit_code == 0, ingested.output
    assert built.exit_code == 0, built.output
    assert (raw_dir / "local_tb_cases.csv").exists()

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        summary = mvp2_summary(session, 2023)
    engine.dispose()

    assert summary["case_count"] == 3
    assert summary["alert_count"] >= 4


def populate_mvp2_database(tmp_path: Path) -> str:
    raw_dir = tmp_path / "municipal_demo"
    generate_mvp2_sample_data(raw_dir)
    database_url = f"sqlite:///{tmp_path / 'mvp2.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        ingest_local_data(session, Mvp2Config(year=2023, raw_dir=raw_dir))
        build_and_store_operational_alerts(session, Mvp2Config(year=2023), date(2026, 6, 29))
        session.commit()
    engine.dispose()
    return database_url
