from __future__ import annotations

from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from typer.testing import CliRunner

from tbia import cli, preparation
from tbia.cli import app
from tbia.domain.models import LocalTbCase, Territory
from tbia.mvp2 import Mvp2Config
from tbia.pipeline import Mvp1Config
from tbia.preparation import (
    DemoPreparationResult,
    TerritorialPreparationResult,
    download_missing_datasus_files,
    prepare_demo_environment,
    prepare_territorial_data,
    territorial_preparation_status,
)
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    initialize_database,
    load_local_tb_cases,
    load_territories,
    mvp2_summary,
    save_local_tb_cases,
    save_territories,
)


def download_result(*, failed: int = 0) -> dict[str, Any]:
    return {
        "requested_file_count": 4,
        "downloaded_file_count": 4 - failed,
        "existing_file_count": 0,
        "failed_file_count": failed,
        "failures": [],
        "sih_all_months": True,
    }


def territorial_result(status: str = "ready") -> TerritorialPreparationResult:
    return TerritorialPreparationResult(
        download=download_result(failed=1 if status == "warning" else 0),
        result_status=status,
        indicator_count=12 if status in {"ready", "warning", "partial"} else 0,
        scenario_count=5 if status in {"ready", "warning"} else 0,
        recommendation_count=5 if status in {"ready", "warning"} else 0,
        sih_coverage_complete=status in {"ready", "warning"},
    )


def test_territorial_preparation_status_requires_usable_outputs_for_warning() -> None:
    status = territorial_preparation_status
    assert status(download_result(), 12, 5, sih_coverage_complete=True) == "ready"
    assert status(download_result(failed=1), 12, 5, sih_coverage_complete=True) == "warning"
    assert status(download_result(), 12, 5, sih_coverage_complete=False) == "warning"
    assert status(download_result(failed=1), 12, 0, sih_coverage_complete=False) == "partial"
    assert status(download_result(failed=1), 0, 0, sih_coverage_complete=False) == "failed"
    assert status(download_result(), 0, 0, sih_coverage_complete=False) == "missing"
    missing_demo = DemoPreparationResult(
        territorial=territorial_result("missing"),
        sample_file_count=7,
        local_source_counts={"local_tb_cases": 3},
        territory_count=184,
        local_case_count=3,
        operational_alert_count=4,
    )
    assert missing_demo.result_status == "missing"
    assert missing_demo.usable is False


def test_download_missing_datasus_files_reuses_cache_and_reports_failures(
    tmp_path: Path, monkeypatch: Any
) -> None:
    config = Mvp1Config(raw_dir=tmp_path)
    config.datasus_sample_dir.mkdir(parents=True)
    cached_file = SimpleNamespace(
        local_name="cached.dbc",
        label="cached source",
        source_id="sinan_tb",
        ftp_url="ftp://example.test/cached.dbc",
    )
    missing_file = SimpleNamespace(
        local_name="missing.dbc",
        label="missing source",
        source_id="sim",
        ftp_url="ftp://example.test/missing.dbc",
    )
    (config.datasus_sample_dir / cached_file.local_name).write_bytes(b"cached")
    requested_months: list[tuple[int, ...]] = []

    def fake_files(
        uf: str, year: int, *, sih_months: tuple[int, ...]
    ) -> tuple[SimpleNamespace, ...]:
        assert (uf, year) == ("CE", 2023)
        requested_months.append(sih_months)
        return cached_file, missing_file

    def fail_download(file: Any, output_dir: Path, *, timeout: int) -> Path:
        assert file is missing_file
        assert output_dir == config.datasus_sample_dir
        assert timeout == 30
        raise RuntimeError("offline")

    events: list[dict[str, Any]] = []
    monkeypatch.setattr(preparation, "datasus_demo_files", fake_files)
    monkeypatch.setattr(preparation, "download_datasus_file", fail_download)

    result = download_missing_datasus_files(
        config, sih_all_months=True, timeout=30, progress=events.append
    )

    assert requested_months == [tuple(range(1, 13))]
    assert result["existing_file_count"] == 1
    assert result["failed_file_count"] == 1
    assert result["failures"][0]["message"] == "offline"
    assert [event["status"] for event in events] == [
        "existing",
        "downloading",
        "failed",
    ]


def test_prepare_territorial_data_emits_ordered_stages(tmp_path: Path, monkeypatch: Any) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'workflow.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    events: list[dict[str, Any]] = []
    calls: list[str] = []

    monkeypatch.setattr(
        preparation,
        "download_missing_datasus_files",
        lambda config, **kwargs: download_result(),
    )
    monkeypatch.setattr(
        preparation,
        "ingest_public_data",
        lambda session, config: calls.append("ingest"),
    )

    def fake_compute(session: Any, config: Mvp1Config) -> int:
        calls.append("indicators")
        return 12

    def fake_build(session: Any, config: Mvp1Config) -> tuple[int, int]:
        calls.append("scenarios")
        return 5, 5

    monkeypatch.setattr(
        preparation,
        "compute_and_store_indicators",
        fake_compute,
    )
    monkeypatch.setattr(
        preparation,
        "build_and_store_scenarios",
        fake_build,
    )

    monkeypatch.setattr(
        preparation,
        "complete_sih_scopes",
        lambda session, *, year, geographic_scopes: set(geographic_scopes),
    )
    result = prepare_territorial_data(
        session_factory,
        Mvp1Config(raw_dir=tmp_path),
        sih_all_months=True,
        timeout=60,
        progress=events.append,
    )
    engine.dispose()

    assert result.result_status == "ready"
    assert result.sih_coverage_complete is True
    assert calls == ["ingest", "indicators", "scenarios"]
    assert [event["stage"] for event in events] == [
        "download",
        "ingest",
        "indicators",
        "scenarios",
        "complete",
    ]
    assert events[-1]["step_index"] == 5


def test_prepare_demo_environment_regenerates_synthetic_data_idempotently(
    tmp_path: Path, monkeypatch: Any
) -> None:
    database_url = f"sqlite:///{tmp_path / 'demo.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        save_territories(
            session,
            [
                Territory("2304400", "Fortaleza", "municipality", "23", "CE"),
                Territory("2607901", "Jaboatao", "municipality", "26", "PE"),
            ],
        )
        save_local_tb_cases(
            session,
            [
                LocalTbCase(
                    local_case_id="OTHER-YEAR-001",
                    pseudonymized_patient_id="OTHER-PATIENT-001",
                    territory_id="T-OTHER",
                    facility_id="UBS-OTHER",
                    team_id="TEAM-OTHER",
                    year=2022,
                    notification_date=date(2022, 1, 10),
                    diagnosis_date=None,
                    treatment_start_date=None,
                    entry_type="new",
                    clinical_form="pulmonary",
                    closure_status="open",
                    closure_date=None,
                    rifampicin_resistance=False,
                    retreatment=False,
                    previous_treatment_failure=False,
                )
            ],
        )
        session.commit()

    monkeypatch.setattr(
        preparation,
        "prepare_territorial_data",
        lambda *args, **kwargs: territorial_result(),
    )
    territorial_config = Mvp1Config(raw_dir=tmp_path / "public")
    municipal_config = Mvp2Config(year=2023, raw_dir=tmp_path / "municipal")

    first = prepare_demo_environment(
        session_factory,
        territorial_config,
        municipal_config,
        date(2026, 6, 29),
        sih_all_months=True,
        timeout=60,
    )
    second = prepare_demo_environment(
        session_factory,
        territorial_config,
        municipal_config,
        date(2026, 6, 29),
        sih_all_months=True,
        timeout=60,
    )

    with session_factory() as session:
        summary = mvp2_summary(session, 2023)
        territories = load_territories(session, "BR")
        prior_year_cases = load_local_tb_cases(session, 2022)
    engine.dispose()

    assert first.usable is True
    assert second.usable is True
    assert second.sample_file_count == 7
    assert summary["case_count"] == 3
    assert summary["alert_count"] == second.operational_alert_count
    assert summary["alert_count"] >= 4
    assert {territory.uf_sigla for territory in territories} == {"CE", "PE"}
    assert [case.local_case_id for case in prior_year_cases] == ["OTHER-YEAR-001"]


def test_prepare_demo_cli_uses_full_year_defaults_and_reports_summary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    captured: dict[str, Any] = {}

    def fake_prepare(
        session_factory: Any,
        territorial_config: Mvp1Config,
        municipal_config: Mvp2Config,
        reference_date: date,
        *,
        sih_all_months: bool,
        timeout: int,
        progress: Any,
    ) -> DemoPreparationResult:
        captured.update(
            {
                "territorial_config": territorial_config,
                "municipal_config": municipal_config,
                "reference_date": reference_date,
                "sih_all_months": sih_all_months,
                "timeout": timeout,
            }
        )
        progress({"stage": "complete", "message": "done"})
        return DemoPreparationResult(
            territorial=territorial_result(),
            sample_file_count=7,
            local_source_counts={"local_tb_cases": 3},
            territory_count=184,
            local_case_count=3,
            operational_alert_count=4,
        )

    monkeypatch.setattr(cli, "prepare_demo_environment", fake_prepare)
    database_url = f"sqlite:///{tmp_path / 'cli.db'}"
    result = CliRunner().invoke(
        app,
        [
            "prepare-demo",
            "--database-url",
            database_url,
            "--raw-dir",
            str(tmp_path / "public"),
            "--mvp2-raw-dir",
            str(tmp_path / "municipal"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["territorial_config"].uf == "CE"
    assert captured["territorial_config"].year == 2023
    assert captured["municipal_config"].year == 2023
    assert captured["reference_date"] == date(2026, 6, 29)
    assert captured["sih_all_months"] is True
    assert "Demo preparation status: ready" in result.output
    assert f"python -m tbia serve --database-url {database_url}" in result.output


def test_prepare_demo_cli_exits_nonzero_for_unusable_result(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(
        cli,
        "prepare_demo_environment",
        lambda *args, **kwargs: DemoPreparationResult(
            territorial=territorial_result("partial"),
            sample_file_count=7,
            local_source_counts={"local_tb_cases": 3},
            territory_count=184,
            local_case_count=3,
            operational_alert_count=4,
        ),
    )

    result = CliRunner().invoke(
        app,
        [
            "prepare-demo",
            "--database-url",
            f"sqlite:///{tmp_path / 'partial.db'}",
        ],
    )

    assert result.exit_code == 1
    assert "Demo preparation status: partial" in result.output
    assert "Demo is not usable" in result.output
    assert "Next:" not in result.output


def test_prepare_demo_cli_accepts_usable_warning(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setattr(
        cli,
        "prepare_demo_environment",
        lambda *args, **kwargs: DemoPreparationResult(
            territorial=territorial_result("warning"),
            sample_file_count=7,
            local_source_counts={"local_tb_cases": 3},
            territory_count=184,
            local_case_count=3,
            operational_alert_count=4,
        ),
    )

    result = CliRunner().invoke(
        app,
        [
            "prepare-demo",
            "--database-url",
            f"sqlite:///{tmp_path / 'warning.db'}",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Demo preparation status: warning" in result.output


def test_prepare_demo_cli_reports_failed_stage(tmp_path: Path, monkeypatch: Any) -> None:
    def fail_during_ingest(*args: Any, **kwargs: Any) -> DemoPreparationResult:
        kwargs["progress"]({"stage": "ingest", "message": "loading"})
        raise RuntimeError("fixture failure")

    monkeypatch.setattr(cli, "prepare_demo_environment", fail_during_ingest)

    result = CliRunner().invoke(
        app,
        [
            "prepare-demo",
            "--database-url",
            f"sqlite:///{tmp_path / 'failed.db'}",
        ],
    )

    assert result.exit_code == 1
    assert "Demo preparation failed during ingest: fixture failure" in result.output
