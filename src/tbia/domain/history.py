from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from tbia.domain.models import IndicatorValue, SourceProvenance


class HistoryPointStatus(StrEnum):
    AVAILABLE = "available"
    SUPPRESSED = "suppressed"
    MISSING = "missing"


class HistoryCoverageStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    EMPTY = "empty"


@dataclass(frozen=True)
class IndicatorHistoryPoint:
    year: int
    status: HistoryPointStatus
    value: float | None = None
    numerator_value: float | None = None
    denominator_value: float | None = None
    denominator_year: int | None = None
    source_provenance: tuple[SourceProvenance, ...] = ()
    caveats: str = ""


@dataclass(frozen=True)
class IndicatorHistoryCoverage:
    requested_year_count: int
    available_year_count: int
    suppressed_year_count: int
    missing_year_count: int
    provenance_incomplete_year_count: int
    status: HistoryCoverageStatus


@dataclass(frozen=True)
class IndicatorHistoryFlag:
    code: str
    years: tuple[int, ...]


@dataclass(frozen=True)
class IndicatorHistory:
    indicator_id: str
    territory_id: str
    start_year: int
    end_year: int
    coverage: IndicatorHistoryCoverage
    flags: tuple[IndicatorHistoryFlag, ...]
    points: tuple[IndicatorHistoryPoint, ...]


def build_indicator_history(
    values: Iterable[IndicatorValue],
    *,
    indicator_id: str,
    territory_id: str,
    start_year: int,
    end_year: int,
) -> IndicatorHistory:
    validate_history_range(start_year, end_year)
    value_by_year: dict[int, IndicatorValue] = {}
    for value in values:
        validate_history_value(value, indicator_id, territory_id, start_year, end_year)
        if value.year in value_by_year:
            raise ValueError(f"duplicate indicator history year: {value.year}")
        value_by_year[value.year] = value

    points = tuple(
        history_point(year, value_by_year.get(year)) for year in range(start_year, end_year + 1)
    )
    coverage = history_coverage(points)
    return IndicatorHistory(
        indicator_id=indicator_id,
        territory_id=territory_id,
        start_year=start_year,
        end_year=end_year,
        coverage=coverage,
        flags=history_flags(points),
        points=points,
    )


def validate_history_range(start_year: int, end_year: int) -> None:
    if start_year > end_year:
        raise ValueError("history start year must not exceed end year")


def validate_history_value(
    value: IndicatorValue,
    indicator_id: str,
    territory_id: str,
    start_year: int,
    end_year: int,
) -> None:
    if value.indicator_id != indicator_id:
        raise ValueError(f"unexpected indicator in history: {value.indicator_id}")
    if value.territory_id != territory_id:
        raise ValueError(f"unexpected territory in history: {value.territory_id}")
    if value.year < start_year or value.year > end_year:
        raise ValueError(f"indicator history year outside requested range: {value.year}")


def history_point(year: int, value: IndicatorValue | None) -> IndicatorHistoryPoint:
    if value is None:
        return IndicatorHistoryPoint(year=year, status=HistoryPointStatus.MISSING)
    status = (
        HistoryPointStatus.SUPPRESSED
        if value.is_suppressed or value.value is None
        else HistoryPointStatus.AVAILABLE
    )
    return IndicatorHistoryPoint(
        year=year,
        status=status,
        value=value.value,
        numerator_value=value.numerator_value,
        denominator_value=value.denominator_value,
        denominator_year=value.denominator_year,
        source_provenance=value.source_provenance,
        caveats=value.caveats,
    )


def history_coverage(
    points: tuple[IndicatorHistoryPoint, ...],
) -> IndicatorHistoryCoverage:
    available = sum(point.status == HistoryPointStatus.AVAILABLE for point in points)
    suppressed = sum(point.status == HistoryPointStatus.SUPPRESSED for point in points)
    missing = sum(point.status == HistoryPointStatus.MISSING for point in points)
    incomplete = sum(
        point.status != HistoryPointStatus.MISSING and provenance_incomplete(point)
        for point in points
    )
    if available == len(points):
        status = HistoryCoverageStatus.COMPLETE
    elif available or suppressed:
        status = HistoryCoverageStatus.PARTIAL
    else:
        status = HistoryCoverageStatus.EMPTY
    return IndicatorHistoryCoverage(
        requested_year_count=len(points),
        available_year_count=available,
        suppressed_year_count=suppressed,
        missing_year_count=missing,
        provenance_incomplete_year_count=incomplete,
        status=status,
    )


def provenance_incomplete(point: IndicatorHistoryPoint) -> bool:
    if not point.source_provenance:
        return True
    return any(
        source.reference_year is None
        or source.release_status == "unknown"
        or source.dataset_kind == "unknown"
        for source in point.source_provenance
    )


def history_flags(
    points: tuple[IndicatorHistoryPoint, ...],
) -> tuple[IndicatorHistoryFlag, ...]:
    flags = [
        flag_for_points("missing_year", points, HistoryPointStatus.MISSING),
        flag_for_points("suppressed_year", points, HistoryPointStatus.SUPPRESSED),
        flag_for_years(
            "provenance_incomplete",
            (
                point.year
                for point in points
                if point.status != HistoryPointStatus.MISSING and provenance_incomplete(point)
            ),
        ),
        flag_for_years(
            "denominator_year_mismatch",
            (
                point.year
                for point in points
                if point.denominator_year is not None and point.denominator_year != point.year
            ),
        ),
        transition_flag("source_release_changed", points, release_signature),
        transition_flag("denominator_method_changed", points, denominator_kind),
        transition_flag("source_set_changed", points, source_set),
    ]
    return tuple(flag for flag in flags if flag is not None)


def flag_for_points(
    code: str,
    points: tuple[IndicatorHistoryPoint, ...],
    status: HistoryPointStatus,
) -> IndicatorHistoryFlag | None:
    return flag_for_years(code, (point.year for point in points if point.status == status))


def flag_for_years(code: str, years: Iterable[int]) -> IndicatorHistoryFlag | None:
    collected = tuple(years)
    return IndicatorHistoryFlag(code, collected) if collected else None


def transition_flag(
    code: str,
    points: tuple[IndicatorHistoryPoint, ...],
    signature: Callable[[tuple[SourceProvenance, ...]], object],
) -> IndicatorHistoryFlag | None:
    changed_years = tuple(
        current.year
        for previous, current in pairwise(points)
        if previous.status != HistoryPointStatus.MISSING
        and current.status != HistoryPointStatus.MISSING
        and signature(previous.source_provenance) != signature(current.source_provenance)
    )
    return IndicatorHistoryFlag(code, changed_years) if changed_years else None


def release_signature(
    sources: tuple[SourceProvenance, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((source.source_id, source.release_status) for source in sources))


def denominator_kind(sources: tuple[SourceProvenance, ...]) -> str | None:
    population = next(
        (source for source in sources if source.source_id == "ibge_population"),
        None,
    )
    return population.dataset_kind if population is not None else None


def source_set(sources: tuple[SourceProvenance, ...]) -> tuple[str, ...]:
    return tuple(sorted(source.source_id for source in sources))
