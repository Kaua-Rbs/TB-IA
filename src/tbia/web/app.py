from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, Query, Request
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
    territory_report,
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
    ) -> HTMLResponse:
        with session_factory() as session:
            context = dashboard_context(session, year, uf.upper())
        return templates.TemplateResponse(
            request,
            "index.html",
            {"request": request, **context},
        )


def register_api_routes(app: FastAPI, session_factory: SessionProvider) -> None:
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
    ) -> dict[str, Any]:
        with session_factory() as session:
            return territory_report(session, territory_id, year)

    @app.get("/api/geo/municipalities")
    def municipality_geojson(uf: str = Query("CE", min_length=2, max_length=2)) -> dict[str, Any]:
        with session_factory() as session:
            return geojson_for_territories(session, uf.upper())

    @app.get("/api/rankings")
    def rankings(
        uf: str = Query("CE", min_length=2, max_length=2),
        year: int = Query(2023, ge=2000, le=2100),
    ) -> list[dict[str, Any]]:
        with session_factory() as session:
            return cast(
                list[dict[str, Any]], dashboard_context(session, year, uf.upper())["ranking"]
            )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}
