from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from tbia.storage import (
    api_indicator_rows,
    api_territory_rows,
    create_engine_for_url,
    create_session_factory,
    dashboard_context,
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
    localize_territory_report,
    normalize_language,
)

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
SessionProvider = Callable[[], Session]


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
        title="TB-IA MVP 1",
        description="Public aggregate tuberculosis territorial intelligence dashboard.",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_routes(app, session_factory)
    return app


def register_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    register_dashboard_routes(app, session_factory)
    register_api_routes(app, session_factory)


def register_dashboard_routes(app: FastAPI, session_factory: SessionProvider) -> None:
    @app.get("/", response_class=HTMLResponse)
    def index(
        request: Request,
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(DEFAULT_LANGUAGE),
    ) -> HTMLResponse:
        language = normalize_language(lang)
        with session_factory() as session:
            context = localize_dashboard_context(
                dashboard_context(session, year, uf.upper()), language
            )
        return templates.TemplateResponse(
            request,
            "index.html",
            {"request": request, **language_context(language), **context},
        )

    @app.get("/mvp2", response_class=HTMLResponse)
    def mvp2(
        request: Request,
        year: int = Query(2023, ge=2000, le=2100),
        alert_type: str | None = Query(None),
        severity: str | None = Query(None),
        facility_id: str | None = Query(None),
        team_id: str | None = Query(None),
        status: str | None = Query(None),
        lang: str = Query(DEFAULT_LANGUAGE),
    ) -> HTMLResponse:
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
    register_mvp2_api_routes(app, session_factory)
    register_health_route(app)


def territory_report_or_404(session: Session, territory_id: str, year: int) -> dict[str, Any]:
    try:
        return territory_report(session, territory_id, year)
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
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            report = territory_report_or_404(session, territory_id, year)
        return localize_territory_report(report, language)

    @app.get("/api/geo/municipalities")
    def municipality_geojson(uf: str = Query("CE", min_length=2, max_length=2)) -> dict[str, Any]:
        with session_factory() as session:
            return geojson_for_territories(session, uf.upper())

    @app.get("/api/map/municipalities")
    def municipality_map_geojson(
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
        lang: str = Query(FALLBACK_LANGUAGE),
    ) -> dict[str, Any]:
        language = normalize_language(lang)
        with session_factory() as session:
            payload = map_geojson_for_municipalities(session, year, uf.upper())
        return localize_map_payload(payload, language)

    @app.get("/api/rankings")
    def rankings(
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
    ) -> list[dict[str, Any]]:
        with session_factory() as session:
            return cast(
                list[dict[str, Any]], dashboard_context(session, year, uf.upper())["ranking"]
            )


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
