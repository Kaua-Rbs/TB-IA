from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from tbia.domain.history import build_indicator_history
from tbia.domain.history_comparability import build_history_comparability_report
from tbia.domain.models import IndicatorValue
from tbia.incidence_history_fixture import FIXTURE_INDICATOR_ID
from tbia.storage import load_indicator_history_values, load_territories

CE_HEADLINE_TERRITORY_IDS = (
    "2304400",
    "2303709",
    "2312908",
    "2307650",
    "2311306",
)


def build_stored_incidence_comparability_report(
    session: Session,
    *,
    geographic_scope: str,
    start_year: int,
    end_year: int,
    source_bundle_sha256: str | None = None,
) -> dict[str, Any]:
    territories = load_territories(session, geographic_scope)
    if not territories:
        raise ValueError(f"no municipalities available for scope {geographic_scope}")
    territory_ids = {territory.territory_id for territory in territories}
    values = load_indicator_history_values(
        session,
        indicator_id=FIXTURE_INDICATOR_ID,
        start_year=start_year,
        end_year=end_year,
        territory_ids=territory_ids,
    )
    values_by_territory: defaultdict[str, list[IndicatorValue]] = defaultdict(list)
    for value in values:
        values_by_territory[value.territory_id].append(value)
    histories = [
        build_indicator_history(
            values_by_territory[territory.territory_id],
            indicator_id=FIXTURE_INDICATOR_ID,
            territory_id=territory.territory_id,
            start_year=start_year,
            end_year=end_year,
        )
        for territory in territories
    ]
    headline_ids = CE_HEADLINE_TERRITORY_IDS if geographic_scope.upper() == "CE" else ()
    return build_history_comparability_report(
        histories,
        {territory.territory_id: territory.name for territory in territories},
        geographic_scope=geographic_scope.upper(),
        headline_territory_ids=headline_ids,
        source_bundle_sha256=source_bundle_sha256,
    )
