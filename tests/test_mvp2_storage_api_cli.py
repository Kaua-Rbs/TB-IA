from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from typer.testing import CliRunner

from tbia.cli import app
from tbia.ingest.local import LOCAL_RESISTANCE_EVIDENCE_FIELDS
from tbia.mvp2 import (
    Mvp2Config,
    build_and_store_operational_alerts,
    generate_mvp2_sample_data,
    ingest_local_data,
    sample_resistance_evidence,
    write_csv,
)
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    initialize_database,
    latest_import_runs,
    load_local_resistance_evidence,
    load_local_tb_cases,
    load_operational_alerts,
    mvp2_summary,
)
from tbia.web import app as web_app
from tbia.web.app import create_app


def test_mvp2_storage_and_api_expose_operational_alerts_without_patient_pseudonyms(
    tmp_path: Path, monkeypatch: Any
) -> None:
    database_url = populate_mvp2_database(tmp_path)

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        cases = load_local_tb_cases(session, 2023)
        resistance_evidence = load_local_resistance_evidence(session, 2023)
        alerts = load_operational_alerts(session, 2023)
        summary = mvp2_summary(session, 2023)
        import_runs = latest_import_runs(session)
    engine.dispose()

    assert len(cases) == 3
    assert len(resistance_evidence) == 1
    assert len(alerts) >= 4
    assert summary["alert_count"] == len(alerts)
    assert summary["open_alert_count"] == len(alerts)
    assert import_runs
    assert all(run["year"] == 2023 for run in import_runs)
    assert all(run["geographic_scope"] is None for run in import_runs)
    monkeypatch.setattr(web_app, "FRONTEND_DIST_DIR", tmp_path / "missing-dist")

    with TestClient(create_app(database_url)) as client:
        summary_response = client.get("/api/mvp2/summary?year=2023")
        alerts_response = client.get("/api/mvp2/alerts?year=2023&severity=high")
        all_alerts_response = client.get("/api/mvp2/alerts?year=2023")
        legacy_alerts_with_lang = client.get("/api/mvp2/alerts?year=2023&lang=pt")
        product_summary_response = client.get("/api/operations/summary?year=2023")
        product_alerts_response = client.get("/api/operations/alerts?year=2023")
        english_product_alerts_response = client.get("/api/operations/alerts?year=2023&lang=en")
        confirmed_signal_response = client.get(
            "/api/operations/alerts?year=2023&signal_kind=confirmed_resistance"
        )
        risk_signal_response = client.get(
            "/api/mvp2/alerts?year=2023&signal_kind=resistance_risk_history"
        )
        page_response = client.get("/mvp2?year=2023&severity=high")
        product_page_response = client.get("/acompanhamento?year=2023&severity=high")
        english_page_response = client.get("/acompanhamento?year=2023&severity=high&lang=en")

    assert summary_response.status_code == 200
    assert alerts_response.status_code == 200
    assert all_alerts_response.status_code == 200
    assert legacy_alerts_with_lang.status_code == 200
    assert product_summary_response.status_code == 200
    assert product_alerts_response.status_code == 200
    assert english_product_alerts_response.status_code == 200
    assert confirmed_signal_response.status_code == 200
    assert risk_signal_response.status_code == 200
    assert page_response.status_code == 200
    assert product_page_response.status_code == 200
    assert english_page_response.status_code == 200
    assert summary_response.json()["alert_count"] == len(alerts)
    assert product_summary_response.json()["alert_count"] == len(alerts)
    summary_by_signal = {
        row["signal_kind"]: row["count"]
        for row in product_summary_response.json()["by_signal_kind"]
    }
    assert summary_by_signal == {
        "confirmed_resistance": 1,
        "resistance_risk_history": 1,
        "resistance_surveillance_gap": 1,
    }
    assert [row["local_case_id"] for row in confirmed_signal_response.json()] == ["LC-001"]
    assert [row["local_case_id"] for row in risk_signal_response.json()] == ["LC-002"]
    assert all(row["severity"] == "high" for row in alerts_response.json())
    assert legacy_alerts_with_lang.json() == all_alerts_response.json()
    assert len(product_alerts_response.json()) == len(all_alerts_response.json())
    assert "pseudonymized_patient_id" not in alerts_response.text
    assert "PAT-" not in alerts_response.text
    assert "Análise territorial" in page_response.text
    assert "Acompanhamento da atenção" in page_response.text
    assert "MVP1" not in page_response.text
    assert "MVP2" not in page_response.text
    assert "demonstração sintética/pseudonimizada" in page_response.text
    assert "Fila operacional de alertas" in product_page_response.text
    assert "Territorial analysis" in english_page_response.text
    assert "Care follow-up" in english_page_response.text
    assert "synthetic/pseudonymized demo" in english_page_response.text

    templates = {
        "pt": {
            "pending_lab_result": "Resultado laboratorial pendente para o caso {case_id}.",
            "medication_pickup_delay": (
                "Retirada de medicamento atrasada para o caso aberto {case_id}."
            ),
            "contact_pending_evaluation": (
                "Avaliação de contato pendente para o caso índice {case_id}."
            ),
            "resistance_vigilance": "Vigilância de resistência para o caso {case_id}.",
        },
        "en": {
            "pending_lab_result": "Laboratory result pending for case {case_id}.",
            "medication_pickup_delay": ("Medication pickup is delayed for open case {case_id}."),
            "contact_pending_evaluation": (
                "Contact evaluation is pending for index case {case_id}."
            ),
            "resistance_vigilance": "Resistance vigilance for case {case_id}.",
        },
    }
    legacy_by_id = {row["alert_id"]: row for row in all_alerts_response.json()}
    for language, rows in (
        ("pt", product_alerts_response.json()),
        ("en", english_product_alerts_response.json()),
    ):
        assert {row["alert_type"] for row in rows} == set(templates[language])
        for row in rows:
            legacy = legacy_by_id[row["alert_id"]]
            assert_localized_alert_preserves_raw_fields(row, legacy)
            assert row["message"] == templates[language][row["alert_type"]].format(
                case_id=row["local_case_id"]
            )

    confirmed_product_alert = next(
        row
        for row in product_alerts_response.json()
        if "confirmed_resistance" in row["signal_kinds"]
    )
    assert confirmed_product_alert["signal_kind_labels"] == [
        "Evidência final explícita de resistência"
    ]
    assert (
        confirmed_product_alert["review_status_label"]
        == "Pendente de validação por profissional de saúde"
    )
    assert confirmed_product_alert["evidence"][0]["code_label"] == (
        "Registro final marcado como confirmado"
    )
    assert confirmed_product_alert["evidence"][0]["source_labels"] == [
        "Evidência sintética de resistência"
    ]

    first_alert_id = all_alerts_response.json()[0]["alert_id"]
    with TestClient(create_app(database_url)) as client:
        detail_response = client.get(f"/api/mvp2/alerts/{first_alert_id}")
        legacy_detail_with_lang = client.get(f"/api/mvp2/alerts/{first_alert_id}?lang=pt")
        product_detail_response = client.get(f"/api/operations/alerts/{first_alert_id}")
        english_product_detail_response = client.get(
            f"/api/operations/alerts/{first_alert_id}?lang=en"
        )
        missing_response = client.get("/api/mvp2/alerts/missing-alert")
        product_missing_response = client.get("/api/operations/alerts/missing-alert")

    assert detail_response.status_code == 200
    assert legacy_detail_with_lang.status_code == 200
    assert product_detail_response.status_code == 200
    assert english_product_detail_response.status_code == 200
    assert detail_response.json()["alert_id"] == first_alert_id
    assert legacy_detail_with_lang.json() == detail_response.json()
    detail_type = detail_response.json()["alert_type"]
    detail_case_id = detail_response.json()["local_case_id"]
    assert product_detail_response.json()["message"] == templates["pt"][detail_type].format(
        case_id=detail_case_id
    )
    assert english_product_detail_response.json()["message"] == templates["en"][detail_type].format(
        case_id=detail_case_id
    )
    assert_localized_alert_preserves_raw_fields(
        product_detail_response.json(), detail_response.json()
    )
    assert missing_response.status_code == 404
    assert product_missing_response.status_code == 404


def test_initialize_database_migrates_operational_alert_evidence_columns(
    tmp_path: Path,
) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'legacy-alerts.db'}")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE operational_alerts (alert_id VARCHAR(200) PRIMARY KEY)")
        )

    initialize_database(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("operational_alerts")}
    engine.dispose()
    assert {"signal_kinds", "review_status", "evidence"} <= columns


def test_resistance_evidence_file_is_optional(tmp_path: Path) -> None:
    raw_dir = tmp_path / "municipal_demo"
    generated_files = generate_mvp2_sample_data(raw_dir)
    (raw_dir / "local_resistance_evidence.csv").unlink()
    database_url = f"sqlite:///{tmp_path / 'optional.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        counts = ingest_local_data(session, Mvp2Config(year=2023, raw_dir=raw_dir))
        session.commit()
        evidence = load_local_resistance_evidence(session, 2023)
        import_runs = latest_import_runs(session)

    engine.dispose()
    assert len(generated_files) == 8
    assert counts["local_resistance_evidence"] == 0
    assert evidence == []
    resistance_run = next(
        row for row in import_runs if row["source_id"] == "local_resistance_evidence"
    )
    assert resistance_run["status"] == "skipped"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"local_case_id": "LC-999"}, "unknown local_case_id"),
        ({"pseudonymized_patient_id": "PAT-999"}, "pseudonym does not match"),
        ({"recorded_date": "2022-12-31"}, "year must match"),
    ],
)
def test_resistance_evidence_ingest_validates_case_link_and_year(
    tmp_path: Path, changes: dict[str, str], message: str
) -> None:
    raw_dir = tmp_path / "municipal_demo"
    generate_mvp2_sample_data(raw_dir)
    row = {**sample_resistance_evidence()[0], **changes}
    write_csv(
        raw_dir / "local_resistance_evidence.csv",
        LOCAL_RESISTANCE_EVIDENCE_FIELDS,
        [row],
    )
    database_url = f"sqlite:///{tmp_path / 'invalid-link.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session, pytest.raises(ValueError, match=message):
        ingest_local_data(session, Mvp2Config(year=2023, raw_dir=raw_dir))

    engine.dispose()


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
    assert (raw_dir / "local_resistance_evidence.csv").exists()

    engine = create_engine_for_url(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        summary = mvp2_summary(session, 2023)
    engine.dispose()

    assert summary["case_count"] == 3
    assert summary["alert_count"] >= 4


def assert_localized_alert_preserves_raw_fields(
    localized: dict[str, Any], raw: dict[str, Any]
) -> None:
    for key, value in raw.items():
        if key == "message":
            continue
        if key == "evidence":
            assert len(localized[key]) == len(value)
            for localized_item, raw_item in zip(localized[key], value, strict=True):
                assert all(
                    localized_item[raw_key] == raw_value for raw_key, raw_value in raw_item.items()
                )
            continue
        assert localized[key] == value


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
