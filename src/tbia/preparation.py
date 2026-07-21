from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date
from typing import Any, cast

from sqlalchemy.orm import Session

from tbia.geography import ufs_for_scope
from tbia.incidence_history_fixture import (
    FIXTURE_END_YEAR,
    FIXTURE_UF,
    prepare_bundled_incidence_history,
)
from tbia.ingest.datasus import datasus_demo_files, download_datasus_file
from tbia.mvp2 import (
    Mvp2Config,
    build_and_store_operational_alerts,
    generate_mvp2_sample_data,
    ingest_local_data,
)
from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    compute_and_store_indicators,
    ingest_public_data,
)
from tbia.storage import complete_sih_scopes, dashboard_context, mvp2_summary

SessionProvider = Callable[[], Session]
ProgressCallback = Callable[[dict[str, Any]], None]
TERRITORIAL_PREPARATION_STEP_COUNT = 5


@dataclass(frozen=True)
class TerritorialPreparationResult:
    download: dict[str, Any]
    result_status: str
    indicator_count: int
    scenario_count: int
    recommendation_count: int
    sih_coverage_complete: bool

    @property
    def usable(self) -> bool:
        return self.result_status in {"ready", "warning"}


@dataclass(frozen=True)
class DemoPreparationResult:
    territorial: TerritorialPreparationResult
    sample_file_count: int
    local_source_counts: dict[str, int]
    territory_count: int
    local_case_count: int
    operational_alert_count: int
    incidence_history_value_count: int = 0

    @property
    def result_status(self) -> str:
        if not self.territorial.usable:
            return self.territorial.result_status
        if not self.usable:
            return "partial"
        return self.territorial.result_status

    @property
    def usable(self) -> bool:
        return (
            self.territorial.usable
            and self.territory_count > 0
            and self.local_case_count > 0
            and self.operational_alert_count > 0
        )


def emit_progress(
    progress: ProgressCallback | None,
    *,
    stage: str,
    step_index: int,
    message: str,
    **details: Any,
) -> None:
    if progress is None:
        return
    progress(
        {
            "stage": stage,
            "step_index": step_index,
            "message": message,
            **details,
        }
    )


def report_datasus_download_progress(
    progress: ProgressCallback | None,
    *,
    index: int,
    total: int,
    status: str,
    label: str,
) -> None:
    if progress is None:
        return
    status_messages = {
        "existing": "já disponível",
        "downloading": "baixando",
        "downloaded": "baixado",
        "failed": "falhou",
    }
    progress(
        {
            "index": index,
            "total": total,
            "status": status,
            "label": label,
            "message": f"{index}/{total} {status_messages[status]}: {label}",
        }
    )


def download_missing_datasus_files(
    config: Mvp1Config,
    *,
    sih_all_months: bool = False,
    timeout: int = 60,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    sih_months = tuple(range(1, 13)) if sih_all_months else (1,)
    files = datasus_demo_files(config.uf, config.year, sih_months=sih_months)
    result: dict[str, Any] = {
        "requested_file_count": len(files),
        "downloaded_file_count": 0,
        "existing_file_count": 0,
        "failed_file_count": 0,
        "failures": [],
        "sih_all_months": sih_all_months,
    }
    failures = cast(list[dict[str, str]], result["failures"])
    for index, file in enumerate(files, start=1):
        output_path = config.datasus_sample_dir / file.local_name
        if output_path.exists():
            result["existing_file_count"] = int(result["existing_file_count"]) + 1
            report_datasus_download_progress(
                progress,
                index=index,
                total=len(files),
                status="existing",
                label=file.label,
            )
            continue

        report_datasus_download_progress(
            progress,
            index=index,
            total=len(files),
            status="downloading",
            label=file.label,
        )
        try:
            download_datasus_file(file, config.datasus_sample_dir, timeout=timeout)
        except Exception as exc:
            result["failed_file_count"] = int(result["failed_file_count"]) + 1
            report_datasus_download_progress(
                progress,
                index=index,
                total=len(files),
                status="failed",
                label=file.label,
            )
            failures.append(
                {
                    "source_id": file.source_id,
                    "label": file.label,
                    "url": file.ftp_url,
                    "message": str(exc),
                }
            )
        else:
            result["downloaded_file_count"] = int(result["downloaded_file_count"]) + 1
            report_datasus_download_progress(
                progress,
                index=index,
                total=len(files),
                status="downloaded",
                label=file.label,
            )
    return result


def territorial_preparation_status(
    download_result: dict[str, Any],
    indicator_count: int,
    scenario_count: int,
    *,
    sih_coverage_complete: bool,
) -> str:
    failed_downloads = int(download_result["failed_file_count"])
    if indicator_count and scenario_count:
        return "warning" if failed_downloads or not sih_coverage_complete else "ready"
    if indicator_count:
        return "partial"
    if failed_downloads:
        return "failed"
    return "missing"


def territorial_preparation_completion_message(result_status: str) -> str:
    if result_status == "ready":
        return "Carga concluída; indicadores e cenários foram atualizados."
    if result_status == "warning":
        return "Carga concluída com fontes incompletas; confira a prontidão dos dados."
    if result_status == "partial":
        return (
            "Carga parcial; indicadores foram gerados, mas cenários ainda exigem revisão dos dados."
        )
    if result_status == "missing":
        return "Carga executada, mas não foram produzidos indicadores para o ano selecionado."
    return "Carga automática não concluiu dados utilizáveis para o ano selecionado."


def prepare_territorial_data(
    session_factory: SessionProvider,
    config: Mvp1Config,
    *,
    sih_all_months: bool,
    timeout: int,
    progress: ProgressCallback | None = None,
) -> TerritorialPreparationResult:
    emit_progress(
        progress,
        stage="download",
        step_index=1,
        message="Verificando e baixando arquivos públicos DATASUS necessários.",
    )

    def update_download_progress(event: dict[str, Any]) -> None:
        emit_progress(
            progress,
            stage="download",
            step_index=1,
            message=str(event["message"]),
            download_event=event,
        )

    download_result = download_missing_datasus_files(
        config,
        sih_all_months=sih_all_months,
        timeout=timeout,
        progress=update_download_progress,
    )
    emit_progress(
        progress,
        stage="ingest",
        step_index=2,
        message=(
            "Ingerindo fontes públicas e atualizando território, população, geometria e agregados."
        ),
        download=download_result,
    )
    with session_factory() as session:
        ingest_public_data(session, config)
        session.commit()

        emit_progress(
            progress,
            stage="indicators",
            step_index=3,
            message="Calculando indicadores municipais de TB para o ano selecionado.",
        )
        indicator_count = compute_and_store_indicators(session, config)
        session.commit()

        emit_progress(
            progress,
            stage="scenarios",
            step_index=4,
            message="Gerando cenários, ranking e recomendações transparentes.",
            indicator_count=indicator_count,
        )
        scenario_count, recommendation_count = build_and_store_scenarios(session, config)
        session.commit()
        expected_sih_scopes = set(ufs_for_scope(config.uf))
        sih_coverage_complete = (
            complete_sih_scopes(
                session,
                year=config.year,
                geographic_scopes=expected_sih_scopes,
            )
            == expected_sih_scopes
        )

    result_status = territorial_preparation_status(
        download_result,
        indicator_count,
        scenario_count,
        sih_coverage_complete=sih_coverage_complete,
    )
    result = TerritorialPreparationResult(
        download=download_result,
        result_status=result_status,
        indicator_count=indicator_count,
        scenario_count=scenario_count,
        recommendation_count=recommendation_count,
        sih_coverage_complete=sih_coverage_complete,
    )
    emit_progress(
        progress,
        stage="complete" if result.usable else result_status,
        step_index=TERRITORIAL_PREPARATION_STEP_COUNT,
        message=territorial_preparation_completion_message(result_status),
        download=download_result,
        indicator_count=indicator_count,
        scenario_count=scenario_count,
        recommendation_count=recommendation_count,
        sih_coverage_complete=sih_coverage_complete,
        result_status=result_status,
    )
    return result


def prepare_demo_environment(
    session_factory: SessionProvider,
    territorial_config: Mvp1Config,
    municipal_config: Mvp2Config,
    reference_date: date,
    *,
    sih_all_months: bool,
    timeout: int,
    progress: ProgressCallback | None = None,
) -> DemoPreparationResult:
    territorial = prepare_territorial_data(
        session_factory,
        territorial_config,
        sih_all_months=sih_all_months,
        timeout=timeout,
        progress=progress,
    )
    incidence_history_value_count = 0
    if supports_bundled_incidence_history(territorial_config):
        emit_progress(
            progress,
            stage="incidence_history",
            step_index=6,
            message="Carregando série histórica municipal de incidência com manifesto verificado.",
        )
        with session_factory() as session:
            history_result = prepare_bundled_incidence_history(session)
            scenario_count, recommendation_count = build_and_store_scenarios(
                session, territorial_config
            )
            session.commit()
        incidence_history_value_count = history_result.value_count
        territorial = replace(
            territorial,
            scenario_count=scenario_count,
            recommendation_count=recommendation_count,
        )

    emit_progress(
        progress,
        stage="local_samples",
        step_index=7,
        message="Regenerando arquivos municipais sintéticos da demonstração.",
    )
    sample_paths = generate_mvp2_sample_data(municipal_config.raw_dir)

    emit_progress(
        progress,
        stage="local_ingest",
        step_index=8,
        message="Ingerindo fontes municipais sintéticas e pseudonimizadas.",
    )
    with session_factory() as session:
        local_source_counts = ingest_local_data(session, municipal_config)
        session.commit()

        emit_progress(
            progress,
            stage="operational_alerts",
            step_index=9,
            message="Gerando alertas operacionais transparentes para revisão humana.",
        )
        operational_alert_count = build_and_store_operational_alerts(
            session, municipal_config, reference_date
        )
        session.commit()

        territorial_context = dashboard_context(
            session, territorial_config.year, territorial_config.uf
        )
        local_summary = mvp2_summary(session, municipal_config.year)

    return DemoPreparationResult(
        territorial=territorial,
        sample_file_count=len(sample_paths),
        local_source_counts=local_source_counts,
        territory_count=int(territorial_context["territory_count"]),
        local_case_count=int(local_summary["case_count"]),
        operational_alert_count=operational_alert_count,
        incidence_history_value_count=incidence_history_value_count,
    )


def supports_bundled_incidence_history(config: Mvp1Config) -> bool:
    return (
        config.uf == FIXTURE_UF
        and config.year == FIXTURE_END_YEAR
        and config.population_source_year in {None, 2022}
    )
