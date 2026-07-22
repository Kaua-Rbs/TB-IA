from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from tbia.ingest.local import (
    LOCAL_CONTACT_FIELDS,
    LOCAL_LAB_EVENT_FIELDS,
    LOCAL_PHARMACY_DISPENSING_FIELDS,
    LOCAL_RESISTANCE_EVIDENCE_FIELDS,
    LOCAL_RESOURCE_FIELDS,
    LOCAL_TB_CASE_FIELDS,
    LOCAL_TEAM_FIELDS,
    LOCAL_TERRITORY_FIELDS,
    read_local_contacts_csv,
    read_local_lab_events_csv,
    read_local_pharmacy_dispensing_csv,
    read_local_resistance_evidence_csv,
    read_local_resources_csv,
    read_local_tb_cases_csv,
    read_local_teams_csv,
    read_local_territories_csv,
)

BASE_TERRITORY = {
    "territory_id": "T-001",
    "name": "Area 01",
    "territory_type": "microarea",
    "parent_id": "",
    "uf_code": "23",
    "uf_sigla": "CE",
    "facility_id": "UBS-01",
    "team_id": "EQUIPE-01",
}
BASE_TEAM = {
    "team_id": "EQUIPE-01",
    "facility_id": "UBS-01",
    "name": "Equipe 01",
    "team_type": "family_health",
    "active": "true",
}
BASE_CASE = {
    "local_case_id": "LC-001",
    "pseudonymized_patient_id": "PAT-001",
    "territory_id": "T-001",
    "facility_id": "UBS-01",
    "team_id": "EQUIPE-01",
    "notification_date": "2023-01-10",
    "diagnosis_date": "2023-01-12",
    "treatment_start_date": "2023-01-15",
    "entry_type": "new",
    "clinical_form": "pulmonary",
    "closure_status": "open",
    "closure_date": "",
    "rifampicin_resistance": "false",
    "retreatment": "false",
    "previous_treatment_failure": "false",
}
BASE_LAB = {
    "local_lab_id": "LAB-001",
    "local_case_id": "LC-001",
    "pseudonymized_patient_id": "PAT-001",
    "test_type": "rapid_molecular",
    "request_date": "2023-01-12",
    "collection_date": "2023-01-13",
    "result_date": "",
    "result": "",
    "status": "pending",
}
BASE_RESISTANCE_EVIDENCE = {
    "resistance_record_id": "RSE-001",
    "local_case_id": "LC-001",
    "pseudonymized_patient_id": "PAT-001",
    "recorded_date": "2023-01-14",
    "evidence_type": "laboratory_result",
    "resistance_scope": "rifampicin",
    "resistance_status": "confirmed",
    "record_status": "final",
    "source_system": "synthetic_demo",
}
BASE_DISPENSING = {
    "dispensing_id": "DISP-001",
    "local_case_id": "LC-001",
    "pseudonymized_patient_id": "PAT-001",
    "dispensing_date": "2023-02-01",
    "days_supplied": "30",
    "medication_group": "first_line",
}
BASE_CONTACT = {
    "contact_id": "CON-001",
    "index_case_id": "LC-001",
    "pseudonymized_contact_id": "CONT-001",
    "identified_date": "2023-01-20",
    "evaluation_date": "",
    "symptomatic": "false",
    "tpt_started_date": "",
    "status": "identified",
}
BASE_RESOURCE = {
    "facility_id": "UBS-01",
    "sputum_collection": "true",
    "rapid_molecular_access": "true",
    "xray_access": "false",
    "sample_transport": "true",
    "pharmacy_tb_meds": "true",
    "chw_count": "12",
}


def test_local_csv_readers_parse_contracts(tmp_path: Path) -> None:
    territory_path = write_rows(
        tmp_path / "local_territories.csv", LOCAL_TERRITORY_FIELDS, [BASE_TERRITORY]
    )
    team_path = write_rows(tmp_path / "local_teams.csv", LOCAL_TEAM_FIELDS, [BASE_TEAM])
    case_path = write_rows(tmp_path / "local_tb_cases.csv", LOCAL_TB_CASE_FIELDS, [BASE_CASE])
    lab_path = write_rows(tmp_path / "local_lab_events.csv", LOCAL_LAB_EVENT_FIELDS, [BASE_LAB])
    resistance_path = write_rows(
        tmp_path / "local_resistance_evidence.csv",
        LOCAL_RESISTANCE_EVIDENCE_FIELDS,
        [BASE_RESISTANCE_EVIDENCE],
    )
    dispensing_path = write_rows(
        tmp_path / "local_pharmacy_dispensing.csv",
        LOCAL_PHARMACY_DISPENSING_FIELDS,
        [BASE_DISPENSING],
    )
    contact_path = write_rows(tmp_path / "local_contacts.csv", LOCAL_CONTACT_FIELDS, [BASE_CONTACT])
    resource_path = write_rows(
        tmp_path / "local_resources.csv", LOCAL_RESOURCE_FIELDS, [BASE_RESOURCE]
    )

    territories = read_local_territories_csv(territory_path)
    teams = read_local_teams_csv(team_path)
    cases = read_local_tb_cases_csv(case_path, 2023)
    labs = read_local_lab_events_csv(lab_path, 2023)
    resistance_evidence = read_local_resistance_evidence_csv(resistance_path, 2023)
    dispensings = read_local_pharmacy_dispensing_csv(dispensing_path, 2023)
    contacts = read_local_contacts_csv(contact_path, 2023)
    resources = read_local_resources_csv(resource_path, 2023)

    assert territories[0].name == "Area 01"
    assert teams[0].active is True
    assert cases[0].notification_date.isoformat() == "2023-01-10"
    assert labs[0].result_date is None
    assert resistance_evidence[0].resistance_status == "confirmed"
    assert dispensings[0].days_supplied == 30
    assert contacts[0].evaluation_date is None
    assert resources[0].chw_count == 12


def test_local_readers_reject_duplicate_natural_keys(tmp_path: Path) -> None:
    scenarios: list[tuple[str, Sequence[str], list[dict[str, str]], Callable[[Path], object]]] = [
        (
            "local_territories.csv",
            LOCAL_TERRITORY_FIELDS,
            [BASE_TERRITORY, {**BASE_TERRITORY, "name": "Area copy"}],
            read_local_territories_csv,
        ),
        (
            "local_teams.csv",
            LOCAL_TEAM_FIELDS,
            [BASE_TEAM, {**BASE_TEAM, "name": "Equipe copy"}],
            read_local_teams_csv,
        ),
        (
            "local_tb_cases.csv",
            LOCAL_TB_CASE_FIELDS,
            [BASE_CASE, {**BASE_CASE, "territory_id": "T-002"}],
            lambda path: read_local_tb_cases_csv(path, 2023),
        ),
        (
            "local_lab_events.csv",
            LOCAL_LAB_EVENT_FIELDS,
            [BASE_LAB, {**BASE_LAB, "status": "complete"}],
            lambda path: read_local_lab_events_csv(path, 2023),
        ),
        (
            "local_pharmacy_dispensing.csv",
            LOCAL_PHARMACY_DISPENSING_FIELDS,
            [BASE_DISPENSING, {**BASE_DISPENSING, "days_supplied": "15"}],
            lambda path: read_local_pharmacy_dispensing_csv(path, 2023),
        ),
        (
            "local_contacts.csv",
            LOCAL_CONTACT_FIELDS,
            [BASE_CONTACT, {**BASE_CONTACT, "status": "evaluated"}],
            lambda path: read_local_contacts_csv(path, 2023),
        ),
        (
            "local_resources.csv",
            LOCAL_RESOURCE_FIELDS,
            [BASE_RESOURCE, {**BASE_RESOURCE, "chw_count": "10"}],
            lambda path: read_local_resources_csv(path, 2023),
        ),
    ]

    for filename, fields, rows, reader in scenarios:
        csv_path = write_rows(tmp_path / filename, fields, rows)
        with pytest.raises(ValueError, match="duplicate"):
            reader(csv_path)


def test_local_case_reader_rejects_forbidden_identifiable_column(tmp_path: Path) -> None:
    csv_path = write_rows(
        tmp_path / "local_tb_cases.csv",
        (*LOCAL_TB_CASE_FIELDS, "cpf"),
        [{**BASE_CASE, "cpf": "00000000000"}],
    )

    with pytest.raises(ValueError, match="forbidden identifiable"):
        read_local_tb_cases_csv(csv_path, 2023)


def test_local_case_reader_requires_pseudonymized_patient_id(tmp_path: Path) -> None:
    csv_path = write_rows(
        tmp_path / "local_tb_cases.csv",
        LOCAL_TB_CASE_FIELDS,
        [{**BASE_CASE, "pseudonymized_patient_id": ""}],
    )

    with pytest.raises(ValueError, match="pseudonymized_patient_id"):
        read_local_tb_cases_csv(csv_path, 2023)


def test_local_lab_reader_rejects_invalid_date(tmp_path: Path) -> None:
    csv_path = write_rows(
        tmp_path / "local_lab_events.csv",
        LOCAL_LAB_EVENT_FIELDS,
        [{**BASE_LAB, "request_date": "01/12/2023"}],
    )

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        read_local_lab_events_csv(csv_path, 2023)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("evidence_type", "unverified_note"),
        ("resistance_status", "suspected"),
        ("record_status", "draft"),
        ("source_system", "real_clinical_system"),
    ],
)
def test_resistance_evidence_reader_rejects_unapproved_categories(
    tmp_path: Path, field: str, value: str
) -> None:
    csv_path = write_rows(
        tmp_path / "local_resistance_evidence.csv",
        LOCAL_RESISTANCE_EVIDENCE_FIELDS,
        [{**BASE_RESISTANCE_EVIDENCE, field: value}],
    )

    with pytest.raises(ValueError, match=f"{field} must be one of"):
        read_local_resistance_evidence_csv(csv_path, 2023)


def test_resistance_evidence_reader_rejects_duplicate_records(tmp_path: Path) -> None:
    csv_path = write_rows(
        tmp_path / "local_resistance_evidence.csv",
        LOCAL_RESISTANCE_EVIDENCE_FIELDS,
        [
            BASE_RESISTANCE_EVIDENCE,
            {**BASE_RESISTANCE_EVIDENCE, "resistance_scope": "multidrug"},
        ],
    )

    with pytest.raises(ValueError, match="duplicate"):
        read_local_resistance_evidence_csv(csv_path, 2023)


def test_resistance_evidence_reader_rejects_identifiable_columns(
    tmp_path: Path,
) -> None:
    csv_path = write_rows(
        tmp_path / "local_resistance_evidence.csv",
        (*LOCAL_RESISTANCE_EVIDENCE_FIELDS, "cns"),
        [{**BASE_RESISTANCE_EVIDENCE, "cns": "000000000000000"}],
    )

    with pytest.raises(ValueError, match="forbidden identifiable"):
        read_local_resistance_evidence_csv(csv_path, 2023)


def write_rows(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path
