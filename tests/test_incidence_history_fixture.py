from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from tbia.cli import app
from tbia.incidence_history_builder import (
    denominator_reference_year,
    historical_sinan_file,
)
from tbia.incidence_history_fixture import (
    AGGREGATE_FILENAME,
    FIXTURE_ID,
    FIXTURE_INDICATOR_ID,
    MANIFEST_FILENAME,
    load_incidence_history_bundle,
    prepare_bundled_incidence_history,
)
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    initialize_database,
    load_indicator_history_values,
    load_territories,
    territory_indicator_history,
)


def test_bundled_ce_incidence_fixture_is_complete_and_auditable() -> None:
    bundle = load_incidence_history_bundle()

    assert bundle.fixture_id == FIXTURE_ID
    assert len(bundle.rows) == 1104
    assert bundle.territory_count == 184
    assert len(bundle.source_artifacts) == 12
    assert {row.year for row in bundle.rows} == set(range(2018, 2024))
    fortaleza = {row.year: row for row in bundle.rows if row.territory_id == "2304400"}
    assert {
        year: (row.new_cases, row.population, row.population_source_year)
        for year, row in fortaleza.items()
    } == {
        2018: (1593, 2_643_247, 2018),
        2019: (1591, 2_669_342, 2019),
        2020: (1313, 2_686_612, 2020),
        2021: (1281, 2_703_391, 2021),
        2022: (1447, 2_428_708, 2022),
        2023: (1467, 2_428_708, 2022),
    }
    releases = {
        artifact.analysis_year: artifact.release_status
        for artifact in bundle.source_artifacts
        if artifact.source_id == "sinan_tb"
    }
    assert releases == {
        2018: "final",
        2019: "final",
        2020: "preliminary",
        2021: "preliminary",
        2022: "preliminary",
        2023: "preliminary",
    }


def test_bundled_fixture_rejects_checksum_tampering(tmp_path: Path) -> None:
    resource_dir = Path("src/tbia/resources/demo")
    aggregate_path = tmp_path / AGGREGATE_FILENAME
    manifest_path = tmp_path / MANIFEST_FILENAME
    aggregate_path.write_bytes((resource_dir / AGGREGATE_FILENAME).read_bytes() + b" ")
    manifest_path.write_bytes((resource_dir / MANIFEST_FILENAME).read_bytes())

    with pytest.raises(ValueError, match="checksum"):
        load_incidence_history_bundle(aggregate_path, manifest_path)


def test_bundled_fixture_preparation_is_idempotent(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'history.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        first = prepare_bundled_incidence_history(session)
        session.commit()
        second = prepare_bundled_incidence_history(session)
        session.commit()
        values = load_indicator_history_values(
            session,
            indicator_id=FIXTURE_INDICATOR_ID,
            start_year=2018,
            end_year=2023,
        )
        territories = load_territories(session, "CE")
        history = territory_indicator_history(
            session,
            "2304400",
            FIXTURE_INDICATOR_ID,
            2018,
            2023,
        )
    engine.dispose()

    assert first == second
    assert first.value_count == 1104
    assert len(values) == 1104
    assert len(territories) == 184
    assert history["coverage"]["status"] == "complete"
    assert [point["numerator_value"] for point in history["points"]] == [
        1593,
        1591,
        1313,
        1281,
        1447,
        1467,
    ]
    flags = {flag["code"]: flag["years"] for flag in history["comparability_flags"]}
    assert flags["source_release_changed"] == [2020]
    assert flags["denominator_method_changed"] == [2022]
    assert flags["denominator_year_mismatch"] == [2023]


def test_fixture_builder_uses_declared_releases_and_denominator_policy() -> None:
    assert "/FINAIS/TUBEBR18.dbc" in historical_sinan_file(2018).ftp_url
    assert "/PRELIM/TUBEBR23.dbc" in historical_sinan_file(2023).ftp_url
    assert [denominator_reference_year(year) for year in range(2018, 2024)] == [
        2018,
        2019,
        2020,
        2021,
        2022,
        2022,
    ]
    with pytest.raises(ValueError, match="outside"):
        historical_sinan_file(2017)


def test_prepare_incidence_history_cli_uses_bundled_data_offline(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cli.db'}"
    result = CliRunner().invoke(
        app,
        ["prepare-incidence-history", "--database-url", database_url],
    )

    assert result.exit_code == 0, result.output
    assert "Prepared 1104 incidence values for 184 municipalities, 2018-2023." in result.output
    assert "Verified aggregate SHA-256:" in result.output
