from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    compute_and_store_indicators,
    ingest_public_data,
)
from tbia.storage import create_engine_for_url, create_session_factory, initialize_database

app = typer.Typer(help="TB-IA MVP 1 public-data pipeline.")

UfOption = Annotated[str, typer.Option(help="UF abbreviation for the demo scope.")]
UfCodeOption = Annotated[str, typer.Option(help="IBGE UF code.")]
YearOption = Annotated[int, typer.Option(help="Reference year.")]
RawDirOption = Annotated[Path, typer.Option(help="Raw data directory.")]
DatabaseUrlOption = Annotated[str, typer.Option(help="SQLAlchemy database URL.")]

DEFAULT_RAW_DIR = Path("data/raw/public_sources")
DEFAULT_DATABASE_URL = "sqlite:///data/tbia_mvp1.sqlite3"


def build_config(uf: str, uf_code: str, year: int, raw_dir: Path) -> Mvp1Config:
    return Mvp1Config(uf=uf.upper(), uf_code=uf_code, year=year, raw_dir=raw_dir)


@app.command()
def ingest(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        ingest_public_data(session, build_config(uf, uf_code, year, raw_dir))
        session.commit()
    typer.echo("Ingestion finished.")


@app.command("compute-indicators")
def compute_indicators(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        count = compute_and_store_indicators(session, build_config(uf, uf_code, year, raw_dir))
        session.commit()
    typer.echo(f"Computed {count} indicator values.")


@app.command("build-scenarios")
def build_scenarios(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        scenario_count, recommendation_count = build_and_store_scenarios(
            session,
            build_config(uf, uf_code, year, raw_dir),
        )
        session.commit()
    typer.echo(f"Built {scenario_count} scenarios and {recommendation_count} recommendations.")


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Host for the local dashboard.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port for the local dashboard.")] = 8000,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    import uvicorn

    from tbia.web.app import create_app

    uvicorn.run(
        create_app(database_url),
        host=host,
        port=port,
        reload=False,
    )
