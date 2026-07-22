from __future__ import annotations

from datetime import UTC, date, datetime

from tbia.domain.models import (
    ContactInvestigation,
    LocalLabEvent,
    LocalResistanceEvidence,
    LocalTbCase,
    MedicationDispensing,
    ResistanceSignalKind,
)
from tbia.domain.operational_alerts import build_operational_alerts


def test_build_operational_alerts_generates_each_mvp2_rule() -> None:
    alerts = build_operational_alerts(
        [base_case("LC-001"), base_case("LC-002", retreatment=True, previous_failure=True)],
        [
            LocalLabEvent(
                "LAB-001",
                "LC-001",
                "PAT-001",
                "rapid_molecular",
                2023,
                date(2023, 1, 12),
                date(2023, 1, 13),
                None,
                "",
                "pending",
            )
        ],
        [
            MedicationDispensing(
                "DISP-001", "LC-001", "PAT-001", date(2023, 2, 1), 30, "first", 2023
            )
        ],
        [
            ContactInvestigation(
                "CON-001",
                "LC-001",
                "CONT-001",
                date(2023, 1, 20),
                None,
                False,
                None,
                "identified",
                2023,
            )
        ],
        year=2023,
        reference_date=date(2023, 4, 20),
        generated_at=datetime(2023, 4, 20, tzinfo=UTC),
    )

    by_type = {alert.alert_type: alert for alert in alerts}

    assert set(by_type) == {
        "pending_lab_result",
        "medication_pickup_delay",
        "contact_pending_evaluation",
        "resistance_vigilance",
    }
    assert by_type["pending_lab_result"].severity.value == "moderate"
    assert by_type["contact_pending_evaluation"].severity.value == "moderate"
    assert by_type["medication_pickup_delay"].severity.value == "high"
    assert by_type["resistance_vigilance"].severity.value == "high"
    assert by_type["resistance_vigilance"].local_case_id == "LC-002"
    assert by_type["resistance_vigilance"].signal_kinds == (
        ResistanceSignalKind.RESISTANCE_RISK_HISTORY,
        ResistanceSignalKind.RESISTANCE_SURVEILLANCE_GAP,
    )
    assert {item.code for item in by_type["resistance_vigilance"].evidence} == {
        "previous_treatment_failure",
        "retreatment_history",
        "missing_completed_culture_or_dst",
    }
    assert "PAT-" not in " ".join(alert.message for alert in alerts)


def test_only_final_confirmed_record_creates_confirmed_resistance_signal() -> None:
    case = base_case("LC-004")
    final_record = resistance_record("RSE-004", "LC-004", "PAT-004", record_status="final")
    preliminary_record = resistance_record(
        "RSE-005", "LC-004", "PAT-004", record_status="preliminary"
    )

    alerts = build_operational_alerts(
        [case],
        [],
        [],
        [],
        resistance_evidence=[final_record, preliminary_record],
        year=2023,
        reference_date=date(2023, 4, 20),
        generated_at=datetime(2023, 4, 20, tzinfo=UTC),
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.signal_kinds == (ResistanceSignalKind.CONFIRMED_RESISTANCE,)
    assert [item.code for item in alert.evidence] == ["final_confirmed_resistance_record"]
    assert alert.evidence[0].source_record_id == "RSE-004"
    assert alert.review_status == "pending_domain_review"

    nonfinal_alerts = build_operational_alerts(
        [base_case("LC-005")],
        [],
        [],
        [],
        resistance_evidence=[
            resistance_record(
                "RSE-006",
                "LC-005",
                "PAT-005",
                record_status="preliminary",
            )
        ],
        year=2023,
        reference_date=date(2023, 4, 20),
        generated_at=datetime(2023, 4, 20, tzinfo=UTC),
    )
    assert nonfinal_alerts == []


def test_legacy_resistance_flag_is_unverified_risk_not_confirmation() -> None:
    alerts = build_operational_alerts(
        [base_case("LC-006", rifampicin_resistance=True)],
        [],
        [],
        [],
        year=2023,
        reference_date=date(2023, 4, 20),
        generated_at=datetime(2023, 4, 20, tzinfo=UTC),
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.signal_kinds == (ResistanceSignalKind.RESISTANCE_RISK_HISTORY,)
    assert alert.evidence[0].code == "legacy_unverified_resistance_flag"
    assert alert.evidence[0].evidence_status == "unverified_legacy_flag"


def test_completed_events_and_closed_cases_do_not_generate_delay_alerts() -> None:
    closed_case = base_case("LC-003", closure_status="cured", closure_date=date(2023, 7, 1))

    alerts = build_operational_alerts(
        [closed_case],
        [
            LocalLabEvent(
                "LAB-003",
                "LC-003",
                "PAT-003",
                "culture",
                2023,
                date(2023, 1, 12),
                date(2023, 1, 13),
                date(2023, 1, 30),
                "negative",
                "complete",
            )
        ],
        [
            MedicationDispensing(
                "DISP-003", "LC-003", "PAT-003", date(2023, 2, 1), 30, "first", 2023
            )
        ],
        [
            ContactInvestigation(
                "CON-003",
                "LC-003",
                "CONT-003",
                date(2023, 1, 20),
                date(2023, 1, 25),
                False,
                None,
                "evaluated",
                2023,
            )
        ],
        year=2023,
        reference_date=date(2023, 4, 20),
        generated_at=datetime(2023, 4, 20, tzinfo=UTC),
    )

    assert alerts == []


def resistance_record(
    record_id: str,
    case_id: str,
    patient_id: str,
    *,
    record_status: str,
) -> LocalResistanceEvidence:
    return LocalResistanceEvidence(
        resistance_record_id=record_id,
        local_case_id=case_id,
        pseudonymized_patient_id=patient_id,
        year=2023,
        recorded_date=date(2023, 1, 14),
        evidence_type="laboratory_result",
        resistance_scope="rifampicin",
        resistance_status="confirmed",
        record_status=record_status,
        source_system="synthetic_demo",
    )


def base_case(
    local_case_id: str,
    *,
    retreatment: bool = False,
    previous_failure: bool = False,
    rifampicin_resistance: bool = False,
    closure_status: str = "open",
    closure_date: date | None = None,
) -> LocalTbCase:
    suffix = local_case_id.split("-")[-1]
    return LocalTbCase(
        local_case_id=local_case_id,
        pseudonymized_patient_id=f"PAT-{suffix}",
        territory_id="T-001",
        facility_id="UBS-01",
        team_id="EQUIPE-01",
        year=2023,
        notification_date=date(2023, 1, 10),
        diagnosis_date=date(2023, 1, 12),
        treatment_start_date=date(2023, 1, 15),
        entry_type="retreatment" if retreatment else "new",
        clinical_form="pulmonary",
        closure_status=closure_status,
        closure_date=closure_date,
        rifampicin_resistance=rifampicin_resistance,
        retreatment=retreatment,
        previous_treatment_failure=previous_failure,
    )
