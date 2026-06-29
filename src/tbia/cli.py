from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from tbia.ingest.datasus import datasus_demo_files, download_datasus_file
from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    build_sinan_validation_report_file,
    compute_and_store_indicators,
    ingest_public_data,
)
from tbia.storage import create_engine_for_url, create_session_factory, initialize_database

app = typer.Typer(help="TB-IA MVP 1 public-data pipeline.")

UfOption = Annotated[str, typer.Option(help="UF abbreviation for the demo scope.")]
UfCodeOption = Annotated[str, typer.Option(help="IBGE UF code.")]
YearOption = Annotated[int, typer.Option(help="Reference year.")]
PopulationSourceYearOption = Annotated[
    int | None,
    typer.Option(help="IBGE SIDRA population period to use as denominator source."),
]
RawDirOption = Annotated[Path, typer.Option(help="Raw data directory.")]
DatabaseUrlOption = Annotated[str, typer.Option(help="SQLAlchemy database URL.")]
TimeoutOption = Annotated[int, typer.Option(help="FTP download timeout in seconds.")]
SihAllMonthsOption = Annotated[
    bool,
    typer.Option(help="Download all 12 SIH monthly files instead of only January."),
]

DEFAULT_RAW_DIR = Path("data/raw/public_sources")
DEFAULT_DATABASE_URL = "sqlite:///data/tbia_mvp1.sqlite3"


def build_config(
    uf: str,
    uf_code: str,
    year: int,
    raw_dir: Path,
    population_source_year: int | None,
) -> Mvp1Config:
    return Mvp1Config(
        uf=uf.upper(),
        uf_code=uf_code,
        year=year,
        raw_dir=raw_dir,
        population_source_year=population_source_year,
    )


@app.command("download-datasus-samples")
def download_datasus_samples(
    uf: UfOption = "CE",
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    sih_all_months: SihAllMonthsOption = False,
    timeout: TimeoutOption = 60,
) -> None:
    config = Mvp1Config(uf=uf.upper(), year=year, raw_dir=raw_dir)
    sih_months = tuple(range(1, 13)) if sih_all_months else (1,)
    failures = 0

    for file in datasus_demo_files(config.uf, config.year, sih_months=sih_months):
        try:
            output_path = download_datasus_file(file, config.datasus_sample_dir, timeout=timeout)
        except Exception as exc:
            failures += 1
            typer.echo(f"failed {file.label} ({file.ftp_url}): {exc}", err=True)
        else:
            typer.echo(f"downloaded {file.label}: {output_path}")

    if failures:
        raise typer.Exit(code=1)


@app.command("validate-sinan-mappings")
def validate_sinan_mappings(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
) -> None:
    output_path, row_count = build_sinan_validation_report_file(
        build_config(uf, uf_code, year, raw_dir, population_source_year=None)
    )
    typer.echo(f"Generated SINAN mapping audit for {row_count} records: {output_path}")


@app.command()
def ingest(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    population_source_year: PopulationSourceYearOption = None,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        ingest_public_data(
            session,
            build_config(uf, uf_code, year, raw_dir, population_source_year),
        )
        session.commit()
    engine.dispose()
    typer.echo("Ingestion finished.")


@app.command("compute-indicators")
def compute_indicators(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    population_source_year: PopulationSourceYearOption = None,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        count = compute_and_store_indicators(
            session,
            build_config(uf, uf_code, year, raw_dir, population_source_year),
        )
        session.commit()
    engine.dispose()
    typer.echo(f"Computed {count} indicator values.")


@app.command("build-scenarios")
def build_scenarios(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = "23",
    year: YearOption = 2023,
    population_source_year: PopulationSourceYearOption = None,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        scenario_count, recommendation_count = build_and_store_scenarios(
            session,
            build_config(uf, uf_code, year, raw_dir, population_source_year),
        )
        session.commit()
    engine.dispose()
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
