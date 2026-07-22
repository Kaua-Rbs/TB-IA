from __future__ import annotations

import csv
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TypeVar

from sqlalchemy.orm import Session

from tbia.domain.models import (
    ImportRun,
    LocalResistanceEvidence,
    LocalTbCase,
)
from tbia.domain.operational_alerts import build_operational_alerts
from tbia.ingest.contracts import SOURCE_CONTRACTS
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
from tbia.storage import (
    clear_local_data_for_year,
    clear_local_dimensions,
    load_contact_investigations,
    load_local_lab_events,
    load_local_resistance_evidence,
    load_local_tb_cases,
    load_medication_dispensings,
    save_contact_investigations,
    save_data_sources,
    save_import_run,
    save_local_lab_events,
    save_local_resistance_evidence,
    save_local_tb_cases,
    save_local_teams,
    save_local_territories,
    save_medication_dispensings,
    save_operational_alerts,
    save_resource_inventories,
)

T = TypeVar("T")


@dataclass(frozen=True)
class Mvp2Config:
    year: int = 2023
    raw_dir: Path = Path("data/raw/municipal_demo")

    def csv_path(self, filename: str) -> Path:
        return self.raw_dir / filename


def ingest_local_data(session: Session, config: Mvp2Config) -> dict[str, int]:
    save_data_sources(session, (contract.as_data_source() for contract in SOURCE_CONTRACTS))
    clear_local_dimensions(session)
    clear_local_data_for_year(session, config.year)
    counts = {
        "local_territories": load_local_source(
            session,
            config.year,
            "local_territories",
            config.csv_path("local_territories.csv"),
            read_local_territories_csv,
            save_local_territories,
        ),
        "local_teams": load_local_source(
            session,
            config.year,
            "local_teams",
            config.csv_path("local_teams.csv"),
            read_local_teams_csv,
            save_local_teams,
        ),
        "local_tb_cases": load_local_source(
            session,
            config.year,
            "local_tb_cases",
            config.csv_path("local_tb_cases.csv"),
            lambda path: read_local_tb_cases_csv(path, config.year),
            save_local_tb_cases,
        ),
        "local_lab_events": load_local_source(
            session,
            config.year,
            "local_lab_events",
            config.csv_path("local_lab_events.csv"),
            lambda path: read_local_lab_events_csv(path, config.year),
            save_local_lab_events,
        ),
        "local_resistance_evidence": load_optional_resistance_evidence(session, config),
        "local_pharmacy_dispensing": load_local_source(
            session,
            config.year,
            "local_pharmacy_dispensing",
            config.csv_path("local_pharmacy_dispensing.csv"),
            lambda path: read_local_pharmacy_dispensing_csv(path, config.year),
            save_medication_dispensings,
        ),
        "local_contacts": load_local_source(
            session,
            config.year,
            "local_contacts",
            config.csv_path("local_contacts.csv"),
            lambda path: read_local_contacts_csv(path, config.year),
            save_contact_investigations,
        ),
        "local_resources": load_local_source(
            session,
            config.year,
            "local_resources",
            config.csv_path("local_resources.csv"),
            lambda path: read_local_resources_csv(path, config.year),
            save_resource_inventories,
        ),
    }
    return counts


def load_optional_resistance_evidence(session: Session, config: Mvp2Config) -> int:
    source_id = "local_resistance_evidence"
    path = config.csv_path("local_resistance_evidence.csv")
    started_at = datetime.now(UTC)
    if not path.exists():
        save_import_run(
            session,
            ImportRun(
                source_id=source_id,
                status="skipped",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                row_count=0,
                message=f"optional MVP2 local CSV not supplied: {path}",
                year=config.year,
            ),
        )
        return 0

    records = read_local_resistance_evidence_csv(path, config.year)
    validate_resistance_evidence_links(records, load_local_tb_cases(session, config.year))
    save_local_resistance_evidence(session, records)
    save_import_run(
        session,
        ImportRun(
            source_id=source_id,
            status="success",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=len(records),
            message=f"loaded optional MVP2 local CSV: {path}",
            year=config.year,
        ),
    )
    return len(records)


def validate_resistance_evidence_links(
    records: Sequence[LocalResistanceEvidence],
    cases: Sequence[LocalTbCase],
) -> None:
    cases_by_id = {case.local_case_id: case for case in cases}
    for record in records:
        if record.recorded_date.year != record.year:
            raise ValueError(
                "recorded_date year must match the selected analysis year "
                f"for resistance record {record.resistance_record_id}"
            )
        case = cases_by_id.get(record.local_case_id)
        if case is None:
            raise ValueError(
                f"resistance evidence references unknown local_case_id {record.local_case_id}"
            )
        if case.pseudonymized_patient_id != record.pseudonymized_patient_id:
            raise ValueError(
                f"resistance evidence pseudonym does not match linked case {record.local_case_id}"
            )


def load_local_source(
    session: Session,
    year: int,
    source_id: str,
    path: Path,
    reader: Callable[[Path], Sequence[T]],
    saver: Callable[[Session, Iterable[T]], None],
) -> int:
    started_at = datetime.now(UTC)
    rows = reader(path)
    saver(session, rows)
    save_import_run(
        session,
        ImportRun(
            source_id=source_id,
            status="success",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=len(rows),
            message=f"loaded MVP2 local CSV: {path}",
            year=year,
        ),
    )
    return len(rows)


def build_and_store_operational_alerts(
    session: Session, config: Mvp2Config, reference_date: date
) -> int:
    save_data_sources(session, (contract.as_data_source() for contract in SOURCE_CONTRACTS))
    started_at = datetime.now(UTC)
    alerts = build_operational_alerts(
        load_local_tb_cases(session, config.year),
        load_local_lab_events(session, config.year),
        load_medication_dispensings(session, config.year),
        load_contact_investigations(session, config.year),
        resistance_evidence=load_local_resistance_evidence(session, config.year),
        year=config.year,
        reference_date=reference_date,
    )
    save_operational_alerts(session, alerts, config.year)
    save_import_run(
        session,
        ImportRun(
            source_id="operational_alerts",
            status="success",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            row_count=len(alerts),
            message=f"generated MVP2 operational alerts for reference date {reference_date}",
            year=config.year,
        ),
    )
    return len(alerts)


def generate_mvp2_sample_data(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [
        write_csv(
            output_dir / "local_territories.csv", LOCAL_TERRITORY_FIELDS, sample_territories()
        ),
        write_csv(output_dir / "local_teams.csv", LOCAL_TEAM_FIELDS, sample_teams()),
        write_csv(output_dir / "local_tb_cases.csv", LOCAL_TB_CASE_FIELDS, sample_cases()),
        write_csv(output_dir / "local_lab_events.csv", LOCAL_LAB_EVENT_FIELDS, sample_labs()),
        write_csv(
            output_dir / "local_resistance_evidence.csv",
            LOCAL_RESISTANCE_EVIDENCE_FIELDS,
            sample_resistance_evidence(),
        ),
        write_csv(
            output_dir / "local_pharmacy_dispensing.csv",
            LOCAL_PHARMACY_DISPENSING_FIELDS,
            sample_dispensings(),
        ),
        write_csv(output_dir / "local_contacts.csv", LOCAL_CONTACT_FIELDS, sample_contacts()),
        write_csv(output_dir / "local_resources.csv", LOCAL_RESOURCE_FIELDS, sample_resources()),
    ]
    return files


def write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def sample_territories() -> list[dict[str, str]]:
    return [
        {
            "territory_id": "T-001",
            "name": "Area 01",
            "territory_type": "microarea",
            "parent_id": "",
            "uf_code": "23",
            "uf_sigla": "CE",
            "facility_id": "UBS-01",
            "team_id": "EQUIPE-01",
        },
        {
            "territory_id": "T-002",
            "name": "Area 02",
            "territory_type": "microarea",
            "parent_id": "",
            "uf_code": "23",
            "uf_sigla": "CE",
            "facility_id": "UBS-01",
            "team_id": "EQUIPE-02",
        },
        {
            "territory_id": "T-003",
            "name": "Area 03",
            "territory_type": "microarea",
            "parent_id": "",
            "uf_code": "23",
            "uf_sigla": "CE",
            "facility_id": "UBS-02",
            "team_id": "EQUIPE-03",
        },
    ]


def sample_teams() -> list[dict[str, str]]:
    return [
        {
            "team_id": "EQUIPE-01",
            "facility_id": "UBS-01",
            "name": "Equipe 01",
            "team_type": "family_health",
            "active": "true",
        },
        {
            "team_id": "EQUIPE-02",
            "facility_id": "UBS-01",
            "name": "Equipe 02",
            "team_type": "family_health",
            "active": "true",
        },
        {
            "team_id": "EQUIPE-03",
            "facility_id": "UBS-02",
            "name": "Equipe 03",
            "team_type": "primary_care",
            "active": "true",
        },
    ]


def sample_cases() -> list[dict[str, str]]:
    return [
        {
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
        },
        {
            "local_case_id": "LC-002",
            "pseudonymized_patient_id": "PAT-002",
            "territory_id": "T-002",
            "facility_id": "UBS-01",
            "team_id": "EQUIPE-02",
            "notification_date": "2023-03-05",
            "diagnosis_date": "2023-03-08",
            "treatment_start_date": "2023-03-10",
            "entry_type": "retreatment",
            "clinical_form": "pulmonary",
            "closure_status": "open",
            "closure_date": "",
            "rifampicin_resistance": "false",
            "retreatment": "true",
            "previous_treatment_failure": "true",
        },
        {
            "local_case_id": "LC-003",
            "pseudonymized_patient_id": "PAT-003",
            "territory_id": "T-003",
            "facility_id": "UBS-02",
            "team_id": "EQUIPE-03",
            "notification_date": "2023-05-01",
            "diagnosis_date": "2023-05-03",
            "treatment_start_date": "2023-05-04",
            "entry_type": "new",
            "clinical_form": "extrapulmonary",
            "closure_status": "cured",
            "closure_date": "2023-11-30",
            "rifampicin_resistance": "false",
            "retreatment": "false",
            "previous_treatment_failure": "false",
        },
    ]


def sample_labs() -> list[dict[str, str]]:
    return [
        {
            "local_lab_id": "LAB-001",
            "local_case_id": "LC-001",
            "pseudonymized_patient_id": "PAT-001",
            "test_type": "rapid_molecular",
            "request_date": "2023-01-12",
            "collection_date": "2023-01-13",
            "result_date": "",
            "result": "",
            "status": "pending",
        },
        {
            "local_lab_id": "LAB-002",
            "local_case_id": "LC-003",
            "pseudonymized_patient_id": "PAT-003",
            "test_type": "culture",
            "request_date": "2023-05-03",
            "collection_date": "2023-05-04",
            "result_date": "2023-05-20",
            "result": "negative",
            "status": "complete",
        },
    ]


def sample_resistance_evidence() -> list[dict[str, str]]:
    return [
        {
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
    ]


def sample_dispensings() -> list[dict[str, str]]:
    return [
        {
            "dispensing_id": "DISP-001",
            "local_case_id": "LC-001",
            "pseudonymized_patient_id": "PAT-001",
            "dispensing_date": "2023-02-01",
            "days_supplied": "30",
            "medication_group": "first_line",
        },
        {
            "dispensing_id": "DISP-002",
            "local_case_id": "LC-002",
            "pseudonymized_patient_id": "PAT-002",
            "dispensing_date": "2023-04-01",
            "days_supplied": "30",
            "medication_group": "first_line",
        },
    ]


def sample_contacts() -> list[dict[str, str]]:
    return [
        {
            "contact_id": "CON-001",
            "index_case_id": "LC-001",
            "pseudonymized_contact_id": "CONT-001",
            "identified_date": "2023-01-20",
            "evaluation_date": "",
            "symptomatic": "false",
            "tpt_started_date": "",
            "status": "identified",
        },
        {
            "contact_id": "CON-002",
            "index_case_id": "LC-002",
            "pseudonymized_contact_id": "CONT-002",
            "identified_date": "2023-03-15",
            "evaluation_date": "2023-03-20",
            "symptomatic": "false",
            "tpt_started_date": "2023-03-25",
            "status": "evaluated",
        },
    ]


def sample_resources() -> list[dict[str, str]]:
    return [
        {
            "facility_id": "UBS-01",
            "sputum_collection": "true",
            "rapid_molecular_access": "true",
            "xray_access": "false",
            "sample_transport": "true",
            "pharmacy_tb_meds": "true",
            "chw_count": "12",
        },
        {
            "facility_id": "UBS-02",
            "sputum_collection": "true",
            "rapid_molecular_access": "false",
            "xray_access": "true",
            "sample_transport": "true",
            "pharmacy_tb_meds": "true",
            "chw_count": "8",
        },
    ]
