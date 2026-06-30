from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from tbia.domain.models import (
    CaseAggregate,
    Facility,
    HospitalizationAggregate,
    MortalityAggregate,
    Territory,
)

Record = Mapping[str, Any]
NEW_CASE_ENTRY_TYPES = frozenset({"1", "4", "6"})
RETREATMENT_ENTRY_TYPES = frozenset({"2", "3"})
OUTCOME_DENOMINATOR_CLOSURES = frozenset({"1", "2", "3", "4", "5", "10"})
TREATMENT_INTERRUPTION_CLOSURES = frozenset({"2", "10"})


def build_datasus_municipality_map(territories: Iterable[Territory]) -> dict[str, str]:
    return {
        territory.territory_id[:6]: territory.territory_id
        for territory in territories
        if territory.territory_type == "municipality"
    }


def transform_sinan_tb_records(
    records: Iterable[Record],
    municipality_map: Mapping[str, str],
    *,
    year: int,
) -> list[CaseAggregate]:
    rows: dict[str, dict[str, int]] = defaultdict(case_metrics)
    for record in records:
        if record_year(record.get("NU_ANO")) != year:
            continue
        territory_id = municipality_map.get(record_text(record, "ID_MN_RESI"))
        if territory_id is None:
            continue

        apply_sinan_record_metrics(rows[territory_id], record)

    return [
        case_aggregate_from_metrics(territory_id, year, metrics)
        for territory_id, metrics in sorted(rows.items())
    ]


def case_aggregate_from_metrics(
    territory_id: str, year: int, metrics: Mapping[str, int]
) -> CaseAggregate:
    return CaseAggregate(
        territory_id=territory_id,
        year=year,
        notified_cases=metrics["notified_cases"],
        new_cases=metrics["new_cases"],
        closed_cases=metrics["closed_cases"],
        cured_cases=metrics["cured_cases"],
        treatment_interruption_cases=metrics["treatment_interruption_cases"],
        retreatment_cases=metrics["retreatment_cases"],
        new_pulmonary_cases=metrics["new_pulmonary_cases"],
        lab_confirmed_pulmonary_cases=metrics["lab_confirmed_pulmonary_cases"],
        hiv_tested_cases=metrics["hiv_tested_cases"],
        tb_hiv_cases=metrics["tb_hiv_cases"],
        trm_tb_cases=metrics["trm_tb_cases"],
        retreatment_pulmonary_cases=metrics["retreatment_pulmonary_cases"],
        culture_retreated_cases=metrics["culture_retreated_cases"],
    )


def apply_sinan_record_metrics(metrics: dict[str, int], record: Record) -> None:
    entry_type = record_text(record, "TRATAMENTO")
    closure = record_text(record, "SITUA_ENCE")
    pulmonary = is_pulmonary_tb(record)
    new_case = is_new_case_entry_type(entry_type)

    metrics["notified_cases"] += 1
    increment_entry_type_metrics(metrics, entry_type)

    if new_case:
        increment_closure_metrics(metrics, closure)
        increment_hiv_metrics(metrics, record)

    if new_case and pulmonary:
        increment_new_pulmonary_metrics(metrics, record)
    if is_retreatment_entry_type(entry_type) and pulmonary:
        increment_retreatment_pulmonary_metrics(metrics, record)


def increment_entry_type_metrics(metrics: dict[str, int], entry_type: str) -> None:
    if is_new_case_entry_type(entry_type):
        metrics["new_cases"] += 1
    if is_retreatment_entry_type(entry_type):
        metrics["retreatment_cases"] += 1


def increment_closure_metrics(metrics: dict[str, int], closure: str) -> None:
    if closure in OUTCOME_DENOMINATOR_CLOSURES:
        metrics["closed_cases"] += 1
    if closure == "1":
        metrics["cured_cases"] += 1
    if closure in TREATMENT_INTERRUPTION_CLOSURES:
        metrics["treatment_interruption_cases"] += 1


def increment_hiv_metrics(metrics: dict[str, int], record: Record) -> None:
    hiv = record_text(record, "HIV")
    if hiv in {"1", "2"}:
        metrics["hiv_tested_cases"] += 1
    if hiv == "1":
        metrics["tb_hiv_cases"] += 1


def is_new_case_entry_type(entry_type: str) -> bool:
    return entry_type in NEW_CASE_ENTRY_TYPES


def is_retreatment_entry_type(entry_type: str) -> bool:
    return entry_type in RETREATMENT_ENTRY_TYPES


def increment_new_pulmonary_metrics(metrics: dict[str, int], record: Record) -> None:
    metrics["new_pulmonary_cases"] += 1
    if has_lab_confirmation(record):
        metrics["lab_confirmed_pulmonary_cases"] += 1
    if record_text(record, "RIFAMPICIN"):
        metrics["trm_tb_cases"] += 1


def increment_retreatment_pulmonary_metrics(metrics: dict[str, int], record: Record) -> None:
    metrics["retreatment_pulmonary_cases"] += 1
    if record_text(record, "CULTURA_ES") in {"1", "2"}:
        metrics["culture_retreated_cases"] += 1


def transform_sim_records(
    records: Iterable[Record],
    municipality_map: Mapping[str, str],
    *,
    year: int,
) -> list[MortalityAggregate]:
    deaths_by_territory: defaultdict[str, int] = defaultdict(int)
    for record in records:
        death_year = death_date_year(record_text(record, "DTOBITO"))
        if death_year != year:
            continue
        if not is_tb_cid(record_text(record, "CAUSABAS")):
            continue
        territory_id = municipality_map.get(record_text(record, "CODMUNRES"))
        if territory_id is not None:
            deaths_by_territory[territory_id] += 1

    return [
        MortalityAggregate(territory_id=territory_id, year=year, tb_deaths=deaths)
        for territory_id, deaths in sorted(deaths_by_territory.items())
    ]


def transform_sih_records(
    records: Iterable[Record],
    municipality_map: Mapping[str, str],
    *,
    year: int,
) -> list[HospitalizationAggregate]:
    admissions_by_territory: defaultdict[str, int] = defaultdict(int)
    for record in records:
        if record_year(record.get("ANO_CMPT")) != year:
            continue
        if not (
            is_tb_cid(record_text(record, "DIAG_PRINC"))
            or is_tb_cid(record_text(record, "DIAG_SECUN"))
        ):
            continue
        territory_id = municipality_map.get(record_text(record, "MUNIC_RES"))
        if territory_id is not None:
            admissions_by_territory[territory_id] += 1

    return [
        HospitalizationAggregate(
            territory_id=territory_id,
            year=year,
            tb_admissions=admissions,
        )
        for territory_id, admissions in sorted(admissions_by_territory.items())
    ]


def transform_cnes_records(
    records: Iterable[Record],
    municipality_map: Mapping[str, str],
) -> list[Facility]:
    facilities: dict[str, Facility] = {}
    for record in records:
        facility_id = record_text(record, "CNES")
        territory_id = municipality_map.get(record_text(record, "CODUFMUN"))
        if not facility_id or territory_id is None:
            continue
        facilities[facility_id] = Facility(
            facility_id=facility_id,
            territory_id=territory_id,
            name=record_text(record, "NOME") or f"CNES {facility_id}",
            facility_type=record_text(record, "TP_UNID") or "unknown",
            sus_linked=record_text(record, "VINC_SUS") == "1",
        )
    return sorted(facilities.values(), key=lambda facility: facility.facility_id)


def case_metrics() -> dict[str, int]:
    return {
        "notified_cases": 0,
        "new_cases": 0,
        "closed_cases": 0,
        "cured_cases": 0,
        "treatment_interruption_cases": 0,
        "retreatment_cases": 0,
        "new_pulmonary_cases": 0,
        "lab_confirmed_pulmonary_cases": 0,
        "hiv_tested_cases": 0,
        "tb_hiv_cases": 0,
        "trm_tb_cases": 0,
        "retreatment_pulmonary_cases": 0,
        "culture_retreated_cases": 0,
    }


def is_pulmonary_tb(record: Record) -> bool:
    return record_text(record, "FORMA") in {"1", "3"}


def has_lab_confirmation(record: Record) -> bool:
    return (
        record_text(record, "BACILOSC_E") == "1"
        or record_text(record, "CULTURA_ES") == "1"
        or record_text(record, "RIFAMPICIN") in {"1", "2"}
    )


def is_tb_cid(value: str) -> bool:
    return value.startswith(("A15", "A16", "A17", "A18", "A19"))


def record_text(record: Record, field: str) -> str:
    value = record.get(field, "")
    return "" if value is None else str(value).strip()


def record_year(value: object) -> int | None:
    text = "" if value is None else str(value).strip()
    return int(text) if text.isdigit() and len(text) == 4 else None


def death_date_year(value: str) -> int | None:
    return int(value[-4:]) if len(value) == 8 and value[-4:].isdigit() else None
