from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from click import BadParameter
from sqlalchemy.orm import Session

from tbia.domain.history_comparability import write_history_comparability_report
from tbia.history_validation import build_stored_incidence_comparability_report
from tbia.incidence_history_builder import generate_incidence_history_fixture
from tbia.incidence_history_fixture import (
    FIXTURE_END_YEAR,
    FIXTURE_START_YEAR,
    FIXTURE_UF,
    IncidenceHistoryPreparationResult,
    prepare_bundled_incidence_history,
)
from tbia.ingest.datasus import datasus_demo_files, download_datasus_file
from tbia.mvp2 import (
    Mvp2Config,
    build_and_store_operational_alerts,
    ingest_local_data,
)
from tbia.mvp2 import (
    generate_mvp2_sample_data as write_mvp2_sample_data,
)
from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    build_sinan_validation_report_file,
    compute_and_store_indicators,
    generate_diagnostic_ranking_impact_report,
    ingest_public_data,
)
from tbia.preparation import DemoPreparationResult, prepare_demo_environment
from tbia.storage import create_engine_for_url, create_session_factory, initialize_database

app = typer.Typer(help="TB-IA MVP public-data and municipal pilot pipeline.")

UfOption = Annotated[str, typer.Option(help="UF abbreviation for the demo scope.")]
UfCodeOption = Annotated[
    str | None, typer.Option(help="IBGE UF code. Inferred from --uf when omitted.")
]
YearOption = Annotated[int, typer.Option(help="Reference year.")]
PopulationSourceYearOption = Annotated[
    int | None,
    typer.Option(help="IBGE SIDRA population period to use as denominator source."),
]
RawDirOption = Annotated[Path, typer.Option(help="Raw data directory.")]
Mvp2RawDirOption = Annotated[Path, typer.Option(help="Synthetic municipal demo CSV directory.")]
DatabaseUrlOption = Annotated[str, typer.Option(help="SQLAlchemy database URL.")]
TimeoutOption = Annotated[int, typer.Option(help="FTP download timeout in seconds.")]
SihAllMonthsOption = Annotated[
    bool,
    typer.Option(help="Download all 12 SIH monthly files instead of only January."),
]
PrepareSihAllMonthsOption = Annotated[
    bool,
    typer.Option(
        "--sih-all-months/--sih-january-only",
        help="Use all 12 SIH months or only January for demo preparation.",
    ),
]
ReferenceDateOption = Annotated[str, typer.Option(help="Reference date for alert rules.")]
OutputDirOption = Annotated[Path, typer.Option(help="Output directory for generated files.")]

DEFAULT_RAW_DIR = Path("data/raw/public_sources")
DEFAULT_MVP2_RAW_DIR = Path("data/raw/municipal_demo")
DEFAULT_DATABASE_URL = "sqlite:///data/tbia_mvp1.sqlite3"
DEFAULT_REFERENCE_DATE = "2026-06-29"


def parse_reference_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BadParameter("reference date must use YYYY-MM-DD") from exc


def build_config(
    uf: str,
    uf_code: str | None,
    year: int,
    raw_dir: Path,
    population_source_year: int | None,
) -> Mvp1Config:
    return Mvp1Config(
        uf=uf.upper(),
        uf_code=uf_code or "",
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
    uf_code: UfCodeOption = None,
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
) -> None:
    output_path, row_count, acceptance_status = build_sinan_validation_report_file(
        build_config(uf, uf_code, year, raw_dir, population_source_year=None)
    )
    typer.echo(f"Generated SINAN mapping audit for {row_count} records: {output_path}")
    typer.echo(f"Diagnostic acceptance status: {acceptance_status}")
    if acceptance_status == "failed":
        raise typer.Exit(code=1)


@app.command("validate-diagnostic-ranking")
def validate_diagnostic_ranking(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = None,
    year: YearOption = 2023,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    config = build_config(uf, uf_code, year, raw_dir, population_source_year=None)
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        output_path = generate_diagnostic_ranking_impact_report(session, config)
    engine.dispose()
    typer.echo(f"Generated diagnostic ranking impact report: {output_path}")


@app.command()
def ingest(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = None,
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
    uf_code: UfCodeOption = None,
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
    uf_code: UfCodeOption = None,
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


@app.command("generate-mvp2-sample-data")
def generate_mvp2_sample_data(
    output_dir: OutputDirOption = DEFAULT_MVP2_RAW_DIR,
) -> None:
    paths = write_mvp2_sample_data(output_dir)
    typer.echo(f"Generated {len(paths)} MVP2 sample CSV files under {output_dir}.")


@app.command("ingest-local")
def ingest_local(
    raw_dir: RawDirOption = DEFAULT_MVP2_RAW_DIR,
    year: YearOption = 2023,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        counts = ingest_local_data(session, Mvp2Config(year=year, raw_dir=raw_dir))
        session.commit()
    engine.dispose()
    typer.echo(f"Loaded MVP2 local sources: {sum(counts.values())} rows.")


@app.command("build-operational-alerts")
def build_operational_alerts_command(
    year: YearOption = 2023,
    reference_date: ReferenceDateOption = DEFAULT_REFERENCE_DATE,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        count = build_and_store_operational_alerts(
            session, Mvp2Config(year=year), parse_reference_date(reference_date)
        )
        session.commit()
    engine.dispose()
    typer.echo(f"Generated {count} MVP2 operational alerts.")


def echo_demo_summary(
    result: DemoPreparationResult,
    *,
    uf: str,
    year: int,
    database_url: str,
) -> None:
    download = result.territorial.download
    typer.echo(f"Demo preparation status: {result.result_status}")
    typer.echo(
        "DATASUS files: "
        f"{download['downloaded_file_count']} downloaded, "
        f"{download['existing_file_count']} cached, "
        f"{download['failed_file_count']} failed."
    )
    typer.echo(
        f"Territorial {uf}/{year}: {result.territory_count} territories, "
        f"{result.territorial.indicator_count} indicators, "
        f"{result.territorial.scenario_count} scenarios, "
        f"{result.territorial.recommendation_count} recommendations."
    )
    typer.echo(
        f"Synthetic operations {year}: {sum(result.local_source_counts.values())} rows from "
        f"{result.sample_file_count} files, {result.local_case_count} cases, "
        f"{result.operational_alert_count} alerts."
    )
    typer.echo(
        "Historical incidence: "
        f"{result.incidence_history_value_count} bundled municipality-year values."
    )
    typer.echo(f"Database: {database_url}")
    if result.usable:
        typer.echo(f"Next: python -m tbia serve --database-url {database_url}")
    else:
        typer.echo("Demo is not usable; review the failed or incomplete stages above.", err=True)


def echo_incidence_history_summary(
    result: IncidenceHistoryPreparationResult,
) -> None:
    typer.echo(
        f"Prepared {result.value_count} incidence values for "
        f"{result.territory_count} municipalities, {result.start_year}-{result.end_year}."
    )
    typer.echo(f"Verified aggregate SHA-256: {result.aggregate_sha256}")


@app.command("prepare-incidence-history")
def prepare_incidence_history(
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    engine = create_engine_for_url(database_url)
    try:
        initialize_database(engine)
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            result = prepare_bundled_incidence_history(session)
            session.commit()
    finally:
        engine.dispose()
    echo_incidence_history_summary(result)


@app.command("build-incidence-history-fixture")
def build_incidence_history_fixture(
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    output_dir: OutputDirOption = Path("src/tbia/resources/demo"),
    timeout: TimeoutOption = 60,
) -> None:
    result = generate_incidence_history_fixture(
        raw_dir,
        output_dir,
        timeout=timeout,
    )
    typer.echo(
        f"Generated {result.row_count} municipality-year aggregates for "
        f"{result.territory_count} municipalities."
    )
    typer.echo(f"Aggregate: {result.aggregate_path}")
    typer.echo(f"Manifest: {result.manifest_path}")
    typer.echo(f"Aggregate SHA-256: {result.aggregate_sha256}")


@app.command("validate-incidence-history")
def validate_incidence_history(
    uf: UfOption = "CE",
    year_from: Annotated[int, typer.Option(help="First annual observation.")] = 2018,
    year_to: Annotated[int, typer.Option(help="Last annual observation.")] = 2023,
    output_dir: OutputDirOption = Path("data/processed/mvp1/validation"),
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
) -> None:
    if year_from > year_to:
        raise BadParameter("--year-from must not exceed --year-to")
    scope = uf.upper()
    engine = create_engine_for_url(database_url)
    try:
        initialize_database(engine)
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            source_bundle_sha256 = prepare_fixture_for_audit(
                session,
                geographic_scope=scope,
                start_year=year_from,
                end_year=year_to,
            )
            session.commit()
            report = build_stored_incidence_comparability_report(
                session,
                geographic_scope=scope,
                start_year=year_from,
                end_year=year_to,
                source_bundle_sha256=source_bundle_sha256,
            )
        output_path = write_history_comparability_report(report, output_dir)
    finally:
        engine.dispose()
    summary = report["summary"]
    typer.echo(f"Generated incidence comparability audit: {output_path}")
    typer.echo(
        f"Coverage: {summary['available_point_count']} available, "
        f"{summary['suppressed_point_count']} suppressed, "
        f"{summary['missing_point_count']} missing."
    )
    typer.echo(
        "Candidates for domain comparison: "
        f"{summary['candidate_for_domain_comparison_count']}/"
        f"{summary['territory_count']} municipalities."
    )
    typer.echo(f"Status: {report['status']}")


def prepare_fixture_for_audit(
    session: Session,
    *,
    geographic_scope: str,
    start_year: int,
    end_year: int,
) -> str | None:
    if (
        geographic_scope == FIXTURE_UF
        and start_year >= FIXTURE_START_YEAR
        and end_year <= FIXTURE_END_YEAR
    ):
        result = prepare_bundled_incidence_history(session)
        return result.aggregate_sha256
    return None


@app.command("prepare-demo")
def prepare_demo(
    uf: UfOption = "CE",
    uf_code: UfCodeOption = None,
    year: YearOption = 2023,
    population_source_year: PopulationSourceYearOption = None,
    raw_dir: RawDirOption = DEFAULT_RAW_DIR,
    mvp2_raw_dir: Mvp2RawDirOption = DEFAULT_MVP2_RAW_DIR,
    database_url: DatabaseUrlOption = DEFAULT_DATABASE_URL,
    reference_date: ReferenceDateOption = DEFAULT_REFERENCE_DATE,
    sih_all_months: PrepareSihAllMonthsOption = True,
    timeout: TimeoutOption = 60,
) -> None:
    territorial_config = build_config(uf, uf_code, year, raw_dir, population_source_year)
    municipal_config = Mvp2Config(year=year, raw_dir=mvp2_raw_dir)
    parsed_reference_date = parse_reference_date(reference_date)
    current_stage = "initialization"

    def report_progress(event: dict[str, object]) -> None:
        nonlocal current_stage
        current_stage = str(event["stage"])
        typer.echo(f"[{current_stage}] {event['message']}")

    engine = create_engine_for_url(database_url)
    try:
        initialize_database(engine)
        session_factory = create_session_factory(engine)
        result = prepare_demo_environment(
            session_factory,
            territorial_config,
            municipal_config,
            parsed_reference_date,
            sih_all_months=sih_all_months,
            timeout=timeout,
            progress=report_progress,
        )
    except Exception as exc:
        typer.echo(f"Demo preparation failed during {current_stage}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        engine.dispose()

    echo_demo_summary(
        result,
        uf=territorial_config.uf,
        year=year,
        database_url=database_url,
    )
    if not result.usable:
        raise typer.Exit(code=1)


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
