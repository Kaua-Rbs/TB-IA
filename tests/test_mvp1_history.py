from __future__ import annotations

from pathlib import Path

import pytest

from tbia.domain.history import (
    HistoryCoverageStatus,
    HistoryPointStatus,
    build_indicator_history,
)
from tbia.domain.models import IndicatorValue, SourceProvenance
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    initialize_database,
    load_indicator_history_values,
    save_indicator_history_values,
)


def value(
    indicator_id: str,
    territory_id: str,
    year: int,
    amount: float | None,
    *,
    numerator: float = 10,
    suppressed: bool = False,
    release_status: str = "preliminary",
    denominator_kind: str = "estimate",
    denominator_year: int | None = None,
) -> IndicatorValue:
    reference_year = denominator_year if denominator_year is not None else year
    return IndicatorValue(
        indicator_id=indicator_id,
        territory_id=territory_id,
        year=year,
        value=amount,
        numerator_value=numerator,
        denominator_value=100_000,
        is_suppressed=suppressed,
        source_ids=("sinan_tb", "ibge_population"),
        caveats="fixture",
        denominator_year=reference_year,
        source_provenance=(
            SourceProvenance(
                "sinan_tb",
                reference_year=year,
                release_status=release_status,
                dataset_kind="notification",
            ),
            SourceProvenance(
                "ibge_population",
                reference_year=reference_year,
                release_status="final",
                dataset_kind=denominator_kind,
            ),
        ),
    )


def test_history_builder_preserves_gaps_suppression_and_comparability_flags() -> None:
    history = build_indicator_history(
        [
            value("tb_incidence_per_100k", "2304400", 2018, 10, release_status="final"),
            value(
                "tb_incidence_per_100k",
                "2304400",
                2020,
                None,
                numerator=3,
                suppressed=True,
            ),
            value(
                "tb_incidence_per_100k",
                "2304400",
                2021,
                12,
                denominator_kind="census",
                denominator_year=2020,
            ),
            value(
                "tb_incidence_per_100k",
                "2304400",
                2022,
                13,
                release_status="final",
                denominator_kind="census",
            ),
        ],
        indicator_id="tb_incidence_per_100k",
        territory_id="2304400",
        start_year=2018,
        end_year=2022,
    )

    assert [point.status for point in history.points] == [
        HistoryPointStatus.AVAILABLE,
        HistoryPointStatus.MISSING,
        HistoryPointStatus.SUPPRESSED,
        HistoryPointStatus.AVAILABLE,
        HistoryPointStatus.AVAILABLE,
    ]
    assert history.points[1].value is None
    assert history.points[2].numerator_value == 3
    assert history.coverage.status == HistoryCoverageStatus.PARTIAL
    assert history.coverage.available_year_count == 3
    assert history.coverage.suppressed_year_count == 1
    assert history.coverage.missing_year_count == 1
    assert {flag.code: flag.years for flag in history.flags} == {
        "missing_year": (2019,),
        "suppressed_year": (2020,),
        "denominator_year_mismatch": (2021,),
        "source_release_changed": (2022,),
        "denominator_method_changed": (2021,),
    }


def test_history_builder_rejects_mixed_or_duplicate_series() -> None:
    duplicate = value("tb_incidence_per_100k", "2304400", 2020, 10)
    with pytest.raises(ValueError, match="duplicate"):
        build_indicator_history(
            [duplicate, duplicate],
            indicator_id="tb_incidence_per_100k",
            territory_id="2304400",
            start_year=2020,
            end_year=2021,
        )

    with pytest.raises(ValueError, match="unexpected territory"):
        build_indicator_history(
            [value("tb_incidence_per_100k", "2607901", 2020, 10)],
            indicator_id="tb_incidence_per_100k",
            territory_id="2304400",
            start_year=2020,
            end_year=2021,
        )


def test_history_storage_scopes_queries_and_replacements(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'history.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    incidence_values = [
        value("tb_incidence_per_100k", "2304400", 2019, 10),
        value("tb_incidence_per_100k", "2304400", 2020, 11),
        value("tb_incidence_per_100k", "2607901", 2019, 20),
        value("tb_incidence_per_100k", "2607901", 2020, 21),
    ]
    mortality = value("tb_mortality_per_100k", "2304400", 2020, 2)

    with session_factory() as session:
        save_indicator_history_values(
            session,
            incidence_values,
            indicator_id="tb_incidence_per_100k",
            start_year=2019,
            end_year=2020,
        )
        save_indicator_history_values(
            session,
            [mortality],
            indicator_id="tb_mortality_per_100k",
            start_year=2020,
            end_year=2020,
        )
        session.commit()

        ce_rows = load_indicator_history_values(
            session,
            indicator_id="tb_incidence_per_100k",
            start_year=2019,
            end_year=2020,
            territory_ids={"2304400"},
        )
        save_indicator_history_values(
            session,
            [value("tb_incidence_per_100k", "2304400", 2020, 15)],
            indicator_id="tb_incidence_per_100k",
            start_year=2019,
            end_year=2020,
            replace_territory_ids={"2304400"},
        )
        session.commit()
        all_incidence = load_indicator_history_values(
            session,
            indicator_id="tb_incidence_per_100k",
            start_year=2019,
            end_year=2020,
        )
        mortality_rows = load_indicator_history_values(
            session,
            indicator_id="tb_mortality_per_100k",
            start_year=2020,
            end_year=2020,
        )
    engine.dispose()

    assert [(row.territory_id, row.year) for row in ce_rows] == [
        ("2304400", 2019),
        ("2304400", 2020),
    ]
    assert [(row.territory_id, row.year, row.value) for row in all_incidence] == [
        ("2304400", 2020, 15),
        ("2607901", 2019, 20),
        ("2607901", 2020, 21),
    ]
    assert [(row.territory_id, row.value) for row in mortality_rows] == [("2304400", 2)]


def test_history_storage_rejects_invalid_ranges(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'invalid-history.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session, pytest.raises(ValueError, match="start year"):
        load_indicator_history_values(
            session,
            indicator_id="tb_incidence_per_100k",
            start_year=2023,
            end_year=2022,
        )
    engine.dispose()
