from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import TypeVar

from tbia.domain.models import (
    ContactInvestigation,
    LocalLabEvent,
    LocalTbCase,
    LocalTeam,
    LocalTerritory,
    MedicationDispensing,
    ResourceInventory,
)

T = TypeVar("T")

FORBIDDEN_IDENTIFIABLE_COLUMNS = frozenset(
    {"cpf", "cns", "nome", "name", "endereco", "address", "telefone", "phone"}
)
TRUE_VALUES = frozenset({"1", "true", "t", "yes", "y", "sim", "s"})
FALSE_VALUES = frozenset({"0", "false", "f", "no", "n", "nao", "não"})

LOCAL_TERRITORY_FIELDS = (
    "territory_id",
    "name",
    "territory_type",
    "parent_id",
    "uf_code",
    "uf_sigla",
    "facility_id",
    "team_id",
)
LOCAL_TEAM_FIELDS = ("team_id", "facility_id", "name", "team_type", "active")
LOCAL_TB_CASE_FIELDS = (
    "local_case_id",
    "pseudonymized_patient_id",
    "territory_id",
    "facility_id",
    "team_id",
    "notification_date",
    "diagnosis_date",
    "treatment_start_date",
    "entry_type",
    "clinical_form",
    "closure_status",
    "closure_date",
    "rifampicin_resistance",
    "retreatment",
    "previous_treatment_failure",
)
LOCAL_LAB_EVENT_FIELDS = (
    "local_lab_id",
    "local_case_id",
    "pseudonymized_patient_id",
    "test_type",
    "request_date",
    "collection_date",
    "result_date",
    "result",
    "status",
)
LOCAL_PHARMACY_DISPENSING_FIELDS = (
    "dispensing_id",
    "local_case_id",
    "pseudonymized_patient_id",
    "dispensing_date",
    "days_supplied",
    "medication_group",
)
LOCAL_CONTACT_FIELDS = (
    "contact_id",
    "index_case_id",
    "pseudonymized_contact_id",
    "identified_date",
    "evaluation_date",
    "symptomatic",
    "tpt_started_date",
    "status",
)
LOCAL_RESOURCE_FIELDS = (
    "facility_id",
    "sputum_collection",
    "rapid_molecular_access",
    "xray_access",
    "sample_transport",
    "pharmacy_tb_meds",
    "chw_count",
)


def read_local_territories_csv(path: Path) -> list[LocalTerritory]:
    rows = read_contract_csv(path, LOCAL_TERRITORY_FIELDS, allowed_identifying_columns={"name"})
    return unique_records(
        rows,
        "territory_id",
        lambda row: LocalTerritory(
            territory_id=required_text(row, "territory_id"),
            name=required_text(row, "name"),
            territory_type=required_text(row, "territory_type"),
            parent_id=optional_text(row, "parent_id"),
            uf_code=required_text(row, "uf_code"),
            uf_sigla=required_text(row, "uf_sigla").upper(),
            facility_id=optional_text(row, "facility_id"),
            team_id=optional_text(row, "team_id"),
        ),
    )


def read_local_teams_csv(path: Path) -> list[LocalTeam]:
    rows = read_contract_csv(path, LOCAL_TEAM_FIELDS, allowed_identifying_columns={"name"})
    return unique_records(
        rows,
        "team_id",
        lambda row: LocalTeam(
            team_id=required_text(row, "team_id"),
            facility_id=required_text(row, "facility_id"),
            name=required_text(row, "name"),
            team_type=required_text(row, "team_type"),
            active=required_bool(row, "active"),
        ),
    )


def read_local_tb_cases_csv(path: Path, year: int) -> list[LocalTbCase]:
    rows = read_contract_csv(path, LOCAL_TB_CASE_FIELDS)
    return unique_records(
        rows,
        "local_case_id",
        lambda row: LocalTbCase(
            local_case_id=required_text(row, "local_case_id"),
            pseudonymized_patient_id=required_text(row, "pseudonymized_patient_id"),
            territory_id=required_text(row, "territory_id"),
            facility_id=required_text(row, "facility_id"),
            team_id=required_text(row, "team_id"),
            year=year,
            notification_date=required_date(row, "notification_date"),
            diagnosis_date=optional_date(row, "diagnosis_date"),
            treatment_start_date=optional_date(row, "treatment_start_date"),
            entry_type=required_text(row, "entry_type"),
            clinical_form=required_text(row, "clinical_form"),
            closure_status=required_text(row, "closure_status"),
            closure_date=optional_date(row, "closure_date"),
            rifampicin_resistance=required_bool(row, "rifampicin_resistance"),
            retreatment=required_bool(row, "retreatment"),
            previous_treatment_failure=required_bool(row, "previous_treatment_failure"),
        ),
    )


def read_local_lab_events_csv(path: Path, year: int) -> list[LocalLabEvent]:
    rows = read_contract_csv(path, LOCAL_LAB_EVENT_FIELDS)
    return unique_records(
        rows,
        "local_lab_id",
        lambda row: LocalLabEvent(
            local_lab_id=required_text(row, "local_lab_id"),
            local_case_id=required_text(row, "local_case_id"),
            pseudonymized_patient_id=required_text(row, "pseudonymized_patient_id"),
            test_type=required_text(row, "test_type"),
            year=year,
            request_date=required_date(row, "request_date"),
            collection_date=optional_date(row, "collection_date"),
            result_date=optional_date(row, "result_date"),
            result=optional_text(row, "result") or "",
            status=required_text(row, "status"),
        ),
    )


def read_local_pharmacy_dispensing_csv(path: Path, year: int) -> list[MedicationDispensing]:
    rows = read_contract_csv(path, LOCAL_PHARMACY_DISPENSING_FIELDS)
    return unique_records(
        rows,
        "dispensing_id",
        lambda row: MedicationDispensing(
            dispensing_id=required_text(row, "dispensing_id"),
            local_case_id=required_text(row, "local_case_id"),
            pseudonymized_patient_id=required_text(row, "pseudonymized_patient_id"),
            dispensing_date=required_date(row, "dispensing_date"),
            days_supplied=positive_int(row, "days_supplied"),
            medication_group=required_text(row, "medication_group"),
            year=year,
        ),
    )


def read_local_contacts_csv(path: Path, year: int) -> list[ContactInvestigation]:
    rows = read_contract_csv(path, LOCAL_CONTACT_FIELDS)
    return unique_records(
        rows,
        "contact_id",
        lambda row: ContactInvestigation(
            contact_id=required_text(row, "contact_id"),
            index_case_id=required_text(row, "index_case_id"),
            pseudonymized_contact_id=required_text(row, "pseudonymized_contact_id"),
            identified_date=required_date(row, "identified_date"),
            evaluation_date=optional_date(row, "evaluation_date"),
            symptomatic=required_bool(row, "symptomatic"),
            tpt_started_date=optional_date(row, "tpt_started_date"),
            status=required_text(row, "status"),
            year=year,
        ),
    )


def read_local_resources_csv(path: Path, year: int) -> list[ResourceInventory]:
    rows = read_contract_csv(path, LOCAL_RESOURCE_FIELDS)
    return unique_records(
        rows,
        "facility_id",
        lambda row: ResourceInventory(
            facility_id=required_text(row, "facility_id"),
            year=year,
            sputum_collection=required_bool(row, "sputum_collection"),
            rapid_molecular_access=required_bool(row, "rapid_molecular_access"),
            xray_access=required_bool(row, "xray_access"),
            sample_transport=required_bool(row, "sample_transport"),
            pharmacy_tb_meds=required_bool(row, "pharmacy_tb_meds"),
            chw_count=non_negative_int(row, "chw_count"),
        ),
    )


def read_contract_csv(
    path: Path,
    required_fields: Sequence[str],
    *,
    allowed_identifying_columns: set[str] | None = None,
) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        validate_headers(path, fieldnames, required_fields, allowed_identifying_columns or set())
        rows: list[dict[str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            rows.append(clean_row(path, line_number, row))
    return rows


def validate_headers(
    path: Path,
    fieldnames: Sequence[str],
    required_fields: Sequence[str],
    allowed_identifying_columns: set[str],
) -> None:
    normalized_fields = {normalize_header(field) for field in fieldnames}
    missing = [field for field in required_fields if field not in normalized_fields]
    if missing:
        raise ValueError(f"{path.name} missing required columns: {', '.join(missing)}")

    forbidden = [
        field
        for field in fieldnames
        if normalize_header(field) in FORBIDDEN_IDENTIFIABLE_COLUMNS
        and normalize_header(field) not in allowed_identifying_columns
    ]
    if forbidden:
        raise ValueError(
            f"{path.name} contains forbidden identifiable columns: {', '.join(forbidden)}"
        )


def clean_row(path: Path, line_number: int, row: dict[str | None, str | None]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in row.items():
        if key is None:
            raise ValueError(f"{path.name}:{line_number} has more values than headers")
        cleaned[normalize_header(key)] = "" if value is None else value.strip()
    return cleaned


def unique_records(
    rows: Sequence[dict[str, str]],
    key_field: str,
    builder: Callable[[dict[str, str]], T],
) -> list[T]:
    records: dict[str, T] = {}
    for row in rows:
        key = required_text(row, key_field)
        if key in records:
            raise ValueError(f"duplicate {key_field}: {key}")
        records[key] = builder(row)
    return list(records.values())


def required_text(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"missing required field: {field}")
    return value


def optional_text(row: dict[str, str], field: str) -> str | None:
    value = row.get(field, "").strip()
    return value or None


def required_date(row: dict[str, str], field: str) -> date:
    return parse_date(required_text(row, field), field)


def optional_date(row: dict[str, str], field: str) -> date | None:
    value = row.get(field, "").strip()
    return parse_date(value, field) if value else None


def parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc


def required_bool(row: dict[str, str], field: str) -> bool:
    value = required_text(row, field).lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValueError(f"{field} must be boolean-like")


def positive_int(row: dict[str, str], field: str) -> int:
    value = int(required_text(row, field))
    if value <= 0:
        raise ValueError(f"{field} must be positive")
    return value


def non_negative_int(row: dict[str, str], field: str) -> int:
    value = int(required_text(row, field))
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def normalize_header(value: str) -> str:
    return value.strip().lower()
