from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, cast
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from tbia.pipeline import Mvp1Config
from tbia.preparation import (
    TERRITORIAL_PREPARATION_STEP_COUNT,
    prepare_territorial_data,
    territorial_preparation_completion_message,
)
from tbia.storage import (
    api_indicator_rows,
    api_territory_rows,
    create_engine_for_url,
    create_session_factory,
    dashboard_context,
    geojson_for_subterritories,
    geojson_for_territories,
    initialize_database,
    latest_import_runs,
    map_geojson_for_municipalities,
    mvp2_alert_detail,
    mvp2_alert_rows,
    mvp2_dashboard_context,
    mvp2_summary,
    territory_report,
)
from tbia.web.i18n import (
    DEFAULT_LANGUAGE,
    FALLBACK_LANGUAGE,
    language_context,
    localize_dashboard_context,
    localize_map_payload,
    localize_mvp2_context,
    localize_product_alert,
    localize_subterritory_payload,
    localize_territory_report,
    normalize_language,
)

TEMPLATE_DIR = Path(__file__).parent / "templates"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_STATIC_PATH = "/static/app"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
SessionProvider = Callable[[], Session]
TERRITORIAL_LOAD_STEP_COUNT = TERRITORIAL_PREPARATION_STEP_COUNT
TERRITORIAL_LOAD_TERMINAL_STATUSES = {"complete", "failed"}
TERRITORIAL_LOAD_JOBS: dict[str, TerritorialLoadJob] = {}
TERRITORIAL_LOAD_LOCK = Lock()


@dataclass
class TerritorialLoadJob:
    job_id: str
    uf: str
    year: int
    sih_all_months: bool
    status: str = "queued"
    result_status: str | None = None
    stage: str = "queued"
    step_index: int = 0
    step_count: int = TERRITORIAL_LOAD_STEP_COUNT
    message: str = "Carga aguardando início."
    download: dict[str, Any] | None = None
    indicator_count: int = 0
    scenario_count: int = 0
    recommendation_count: int = 0
    error: str | None = None
    created_at: str = ""
    started_at: str | None = None
    updated_at: str = ""
    finished_at: str | None = None

    def to_api(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "uf": self.uf,
            "year": self.year,
            "sih_all_months": self.sih_all_months,
            "status": self.status,
            "result_status": self.result_status,
            "stage": self.stage,
            "step_index": self.step_index,
            "step_count": self.step_count,
            "message": self.message,
            "download": self.download,
            "indicator_count": self.indicator_count,
            "scenario_count": self.scenario_count,
            "recommendation_count": self.recommendation_count,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "finished_at": self.finished_at,
        }


def create_app(database_url: str = "sqlite:///data/tbia_mvp1.sqlite3") -> FastAPI:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="TB-IA",
        description="Tuberculosis territorial intelligence and operational follow-up.",
        version="0.1.0",
        lifespan=lifespan,
    )
    mount_frontend_assets(app)
    register_routes(app, session_factory)
    return app


def register_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    register_dashboard_routes(app, session_factory)
    register_api_routes(app, session_factory)


def register_dashboard_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/", response_class=HTMLResponse)
    @app.get("/conceito/territorios", response_class=HTMLResponse)
    @app.get("/territorios", response_class=HTMLResponse)
    def index(
        request: Request,
        uf: str = Query("BR", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(DEFAULT_LANGUAGE),
        comparison_scope: str | None = Query(None),
    ) -> Response:
        spa_response = frontend_spa_response()
        if spa_response is not None:
            return spa_response

        language = normalize_language(lang)
        with session_factory() as session:
            context = localize_dashboard_context(
                dashboard_context(session, year, uf.upper(), comparison_scope), language
            )
        return templates.TemplateResponse(
            request,
            "index.html",
            {"request": request, **language_context(language), **context},
        )

    @app.get("/mvp2", response_class=HTMLResponse)
    @app.get("/conceito/acompanhamento", response_class=HTMLResponse)
    @app.get("/acompanhamento", response_class=HTMLResponse)
    def mvp2(
        request: Request,
        year: int = Query(2023, ge=2000, le=2100),
        alert_type: str | None = Query(None),
        severity: str | None = Query(None),
        facility_id: str | None = Query(None),
        team_id: str | None = Query(None),
        status: str | None = Query(None),
        lang: str = Query(DEFAULT_LANGUAGE),
    ) -> Response:
        spa_response = frontend_spa_response()
        if spa_response is not None:
            return spa_response

        language = normalize_language(lang)
        with session_factory() as session:
            context = localize_mvp2_context(
                mvp2_dashboard_context(
                    session,
                    year,
                    alert_type=alert_type,
                    severity=severity,
                    facility_id=facility_id,
                    team_id=team_id,
                    status=status,
                ),
                language,
            )
        return templates.TemplateResponse(
            request,
            "mvp2.html",
            {"request": request, **language_context(language), **context},
        )


def register_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    register_mvp1_api_routes(app, session_factory)
    register_product_territorial_api_routes(app, session_factory)
    register_product_operations_api_routes(app, session_factory)
    register_mvp2_api_routes(app, session_factory)
    register_health_route(app)


def mount_frontend_assets(app: FastAPI) -> None:
    if FRONTEND_DIST_DIR.is_dir():
        app.mount(
            FRONTEND_STATIC_PATH,
            StaticFiles(directory=str(FRONTEND_DIST_DIR)),
            name="frontend",
        )


def frontend_spa_response() -> FileResponse | None:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.is_file():
        return None
    return FileResponse(index_file)


def utc_now_text() -> str:
    return datetime.now(UTC).isoformat()


def create_territorial_load_job(
    uf: str, year: int, sih_all_months: bool
) -> tuple[dict[str, Any], bool]:
    with TERRITORIAL_LOAD_LOCK:
        for job in TERRITORIAL_LOAD_JOBS.values():
            if (
                job.uf == uf
                and job.year == year
                and job.status not in TERRITORIAL_LOAD_TERMINAL_STATUSES
            ):
                return job.to_api(), False

        now = utc_now_text()
        job = TerritorialLoadJob(
            job_id=uuid4().hex,
            uf=uf,
            year=year,
            sih_all_months=sih_all_months,
            created_at=now,
            updated_at=now,
        )
        TERRITORIAL_LOAD_JOBS[job.job_id] = job
        prune_territorial_load_jobs_locked()
        return job.to_api(), True


def get_territorial_load_job(job_id: str) -> dict[str, Any]:
    with TERRITORIAL_LOAD_LOCK:
        job = TERRITORIAL_LOAD_JOBS.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job.to_api()


def update_territorial_load_job(job_id: str, **updates: Any) -> dict[str, Any]:
    with TERRITORIAL_LOAD_LOCK:
        job = TERRITORIAL_LOAD_JOBS[job_id]
        for key, value in updates.items():
            setattr(job, key, value)
        job.updated_at = utc_now_text()
        if job.status in TERRITORIAL_LOAD_TERMINAL_STATUSES and job.finished_at is None:
            job.finished_at = job.updated_at
        return job.to_api()


def prune_territorial_load_jobs_locked(limit: int = 30) -> None:
    overflow_count = len(TERRITORIAL_LOAD_JOBS) - limit
    if overflow_count <= 0:
        return
    finished_jobs = sorted(
        (
            job
            for job in TERRITORIAL_LOAD_JOBS.values()
            if job.status in TERRITORIAL_LOAD_TERMINAL_STATUSES
        ),
        key=lambda job: job.updated_at,
    )
    for job in finished_jobs[:overflow_count]:
        TERRITORIAL_LOAD_JOBS.pop(job.job_id, None)


def run_territorial_load_job(
    job_id: str,
    session_factory: SessionProvider,
    config: Mvp1Config,
    *,
    sih_all_months: bool,
    timeout: int,
) -> None:
    update_territorial_load_job(
        job_id,
        status="running",
        stage="download",
        step_index=1,
        started_at=utc_now_text(),
        message="Verificando e baixando arquivos públicos DATASUS necessários.",
    )

    def update_progress(event: dict[str, Any]) -> None:
        updates = {
            key: event[key]
            for key in (
                "stage",
                "step_index",
                "message",
                "download",
                "indicator_count",
                "scenario_count",
                "recommendation_count",
                "result_status",
            )
            if key in event
        }
        update_territorial_load_job(job_id, **updates)

    try:
        result = prepare_territorial_data(
            session_factory,
            config,
            sih_all_months=sih_all_months,
            timeout=timeout,
            progress=update_progress,
        )
        status = "failed" if result.result_status == "failed" else "complete"
        update_territorial_load_job(
            job_id,
            status=status,
            result_status=result.result_status,
            stage="complete" if status == "complete" else "failed",
            step_index=TERRITORIAL_LOAD_STEP_COUNT,
            download=result.download,
            indicator_count=result.indicator_count,
            scenario_count=result.scenario_count,
            recommendation_count=result.recommendation_count,
            message=territorial_preparation_completion_message(result.result_status),
        )
    except Exception as exc:
        update_territorial_load_job(
            job_id,
            status="failed",
            result_status="failed",
            stage="failed",
            error=str(exc),
            message="A carga foi interrompida por erro. Consulte o detalhe técnico do job.",
        )


def territory_report_or_404(
    session: Session, territory_id: str, year: int, comparison_scope: str | None = None
) -> dict[str, Any]:
    try:
        return territory_report(session, territory_id, year, comparison_scope)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def register_mvp1_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/api/sources")
    def sources() -> list[dict[str, Any]]:
        with session_factory() as session:
            return latest_import_runs(session)

    @app.get("/api/territories")
    def territories(uf: str = Query("CE", min_length=2, max_length=2)) -> list[dict[str, Any]]:
        with session_factory() as session:
            return api_territory_rows(session, uf.upper())

    @app.get("/api/indicators")
    def indicators(
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
    ) -> list[dict[str, Any]]:
        with session_factory() as session:
            return api_indicator_rows(session, year, uf.upper())

    @app.get("/api/territories/{territory_id}/report")
    def territory_detail(
        territory_id: str,
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(FALLBACK_LANGUAGE),
        comparison_scope: str | None = Query(None),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            report = territory_report_or_404(session, territory_id, year, comparison_scope)
        return localize_territory_report(report, language)

    register_mvp1_map_api_routes(app, session_factory)

    @app.get("/api/rankings")
    def rankings(
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        comparison_scope: str | None = Query(None),
    ) -> list[dict[str, Any]]:
        with session_factory() as session:
            return cast(
                list[dict[str, Any]],
                dashboard_context(session, year, uf.upper(), comparison_scope)["ranking"],
            )


def register_mvp1_map_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/api/geo/municipalities")
    def municipality_geojson(uf: str = Query("CE", min_length=2, max_length=2)) -> dict[str, Any]:
        with session_factory() as session:
            return geojson_for_territories(session, uf.upper())

    @app.get("/api/map/municipalities")
    def municipality_map_geojson(
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(FALLBACK_LANGUAGE),
        comparison_scope: str | None = Query(None),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            payload = map_geojson_for_municipalities(session, year, uf.upper(), comparison_scope)
        return localize_map_payload(payload, language)

    @app.get("/api/map/subterritories")
    def subterritory_map_geojson(
        parent_id: str = Query(..., min_length=1),
        territory_type: str = Query("neighborhood_reference", min_length=1),
        lang: str = Query(FALLBACK_LANGUAGE),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            payload = geojson_for_subterritories(session, parent_id, territory_type)
        return localize_subterritory_payload(payload, language)


def register_product_territorial_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/api/territorial/context")
    def territorial_context(
        uf: str = Query("BR", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(DEFAULT_LANGUAGE),
        comparison_scope: str | None = Query(None),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            context = dashboard_context(session, year, uf.upper(), comparison_scope)
        return localize_dashboard_context(context, language)

    @app.get("/api/territorial/map")
    def territorial_map_geojson(
        uf: str = Query("BR", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(FALLBACK_LANGUAGE),
        comparison_scope: str | None = Query(None),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            payload = map_geojson_for_municipalities(session, year, uf.upper(), comparison_scope)
        return localize_map_payload(payload, language)

    @app.get("/api/territorial/subterritories")
    def territorial_subterritory_geojson(
        parent_id: str = Query(..., min_length=1),
        territory_type: str = Query("neighborhood_reference", min_length=1),
        lang: str = Query(FALLBACK_LANGUAGE),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            payload = geojson_for_subterritories(session, parent_id, territory_type)
        return localize_subterritory_payload(payload, language)

    @app.post("/api/territorial/load-year")
    def territorial_load_year(
        background_tasks: BackgroundTasks,
        uf: str = Query("BR", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        sih_all_months: bool = Query(True),
        timeout: int = Query(60, ge=1, le=300),
    ) -> dict[str, Any]:
        config = Mvp1Config(uf=uf.upper(), year=year)
        job, created = create_territorial_load_job(config.uf, year, sih_all_months)
        if created:
            background_tasks.add_task(
                run_territorial_load_job,
                str(job["job_id"]),
                session_factory,
                config,
                sih_all_months=sih_all_months,
                timeout=timeout,
            )
        return job

    @app.get("/api/territorial/load-year/{job_id}")
    def territorial_load_year_status(job_id: str) -> dict[str, Any]:
        try:
            return get_territorial_load_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="load job not found") from exc


def register_product_operations_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/api/operations/summary")
    def operations_summary(year: int = Query(2023, ge=2000, le=2100)) -> dict[str, Any]:
        with session_factory() as session:
            return mvp2_summary(session, year)

    @app.get("/api/operations/alerts")
    def operations_alerts(
        year: int = Query(2023, ge=2000, le=2100),
        alert_type: str | None = Query(None),
        severity: str | None = Query(None),
        facility_id: str | None = Query(None),
        team_id: str | None = Query(None),
        status: str | None = Query(None),
        lang: str = Query(DEFAULT_LANGUAGE),
    ) -> list[dict[str, Any]]:
        language = normalize_language(lang)
        with session_factory() as session:
            rows = mvp2_alert_rows(
                session,
                year,
                alert_type=alert_type,
                severity=severity,
                facility_id=facility_id,
                team_id=team_id,
                status=status,
            )
        return [localize_product_alert(row, language) for row in rows]

    @app.get("/api/operations/alerts/{alert_id}")
    def operations_alert(
        alert_id: str,
        lang: str = Query(DEFAULT_LANGUAGE),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            row = mvp2_alert_detail(session, alert_id)
        if row is None:
            raise HTTPException(status_code=404, detail="alert not found")
        return localize_product_alert(row, language)


def register_mvp2_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/api/mvp2/summary")
    def mvp2_summary_endpoint(year: int = Query(2023, ge=2000, le=2100)) -> dict[str, Any]:
        with session_factory() as session:
            return mvp2_summary(session, year)

    @app.get("/api/mvp2/alerts")
    def mvp2_alerts_endpoint(
        year: int = Query(2023, ge=2000, le=2100),
        alert_type: str | None = Query(None),
        severity: str | None = Query(None),
        facility_id: str | None = Query(None),
        team_id: str | None = Query(None),
        status: str | None = Query(None),
    ) -> list[dict[str, Any]]:
        with session_factory() as session:
            return mvp2_alert_rows(
                session,
                year,
                alert_type=alert_type,
                severity=severity,
                facility_id=facility_id,
                team_id=team_id,
                status=status,
            )

    @app.get("/api/mvp2/alerts/{alert_id}")
    def mvp2_alert_endpoint(alert_id: str) -> dict[str, Any]:
        with session_factory() as session:
            row = mvp2_alert_detail(session, alert_id)
        if row is None:
            raise HTTPException(status_code=404, detail="alert not found")
        return row


def register_health_route(app: FastAPI) -> None:
    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}
