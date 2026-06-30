from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, timedelta

from tbia.domain.models import (
    ContactInvestigation,
    LocalLabEvent,
    LocalTbCase,
    MedicationDispensing,
    OperationalAlert,
    OperationalAlertSeverity,
    OperationalAlertStatus,
)

PENDING_GRACE_DAYS = 7
COMPLETED_STATUSES = frozenset({"complete", "completed", "concluido", "concluído", "finalizado"})
CLOSED_CASE_STATUSES = frozenset(
    {
        "closed",
        "completed",
        "cured",
        "cura",
        "death",
        "died",
        "transfer",
        "transferred",
        "encerrado",
        "treatment_interruption",
        "abandonment",
        "interruption",
    }
)
CULTURE_DST_TERMS = ("culture", "cultura", "dst", "sensibilidade", "susceptibility")


def build_operational_alerts(
    cases: Sequence[LocalTbCase],
    lab_events: Sequence[LocalLabEvent],
    dispensings: Sequence[MedicationDispensing],
    contacts: Sequence[ContactInvestigation],
    *,
    year: int,
    reference_date: date,
    generated_at: datetime | None = None,
) -> list[OperationalAlert]:
    generated = generated_at or datetime.now(UTC)
    cases_by_id = {case.local_case_id: case for case in cases if case.year == year}
    labs_for_year = [event for event in lab_events if event.year == year]
    alerts = [
        *pending_lab_result_alerts(labs_for_year, cases_by_id, year, reference_date, generated),
        *medication_pickup_delay_alerts(dispensings, cases_by_id, year, reference_date, generated),
        *contact_pending_evaluation_alerts(contacts, cases_by_id, year, reference_date, generated),
        *resistance_vigilance_alerts(
            cases_by_id.values(), labs_for_year, year, reference_date, generated
        ),
    ]
    return sorted(alerts, key=alert_sort_key)


def pending_lab_result_alerts(
    lab_events: Sequence[LocalLabEvent],
    cases_by_id: dict[str, LocalTbCase],
    year: int,
    reference_date: date,
    generated_at: datetime,
) -> list[OperationalAlert]:
    alerts: list[OperationalAlert] = []
    for event in lab_events:
        case = cases_by_id.get(event.local_case_id)
        if case is None or is_complete_status(event.status) or event.result_date is not None:
            continue
        due_date = event.request_date + timedelta(days=PENDING_GRACE_DAYS)
        if due_date < reference_date:
            alerts.append(
                make_alert(
                    alert_type="pending_lab_result",
                    severity=OperationalAlertSeverity.MODERATE,
                    case=case,
                    related_entity_id=event.local_lab_id,
                    year=year,
                    reference_date=reference_date,
                    generated_at=generated_at,
                    due_date=due_date,
                    message=(
                        f"Lab result pending for case {case.local_case_id} "
                        f"since {event.request_date}."
                    ),
                )
            )
    return alerts


def medication_pickup_delay_alerts(
    dispensings: Sequence[MedicationDispensing],
    cases_by_id: dict[str, LocalTbCase],
    year: int,
    reference_date: date,
    generated_at: datetime,
) -> list[OperationalAlert]:
    latest_by_case = latest_dispensings_by_case(dispensings, year)
    alerts: list[OperationalAlert] = []
    for case_id, dispensing in latest_by_case.items():
        case = cases_by_id.get(case_id)
        if case is None or not is_open_case(case):
            continue
        due_date = dispensing.dispensing_date + timedelta(
            days=dispensing.days_supplied + PENDING_GRACE_DAYS
        )
        if due_date < reference_date:
            alerts.append(
                make_alert(
                    alert_type="medication_pickup_delay",
                    severity=OperationalAlertSeverity.HIGH,
                    case=case,
                    related_entity_id=dispensing.dispensing_id,
                    year=year,
                    reference_date=reference_date,
                    generated_at=generated_at,
                    due_date=due_date,
                    message=f"Medication pickup is delayed for open case {case.local_case_id}.",
                )
            )
    return alerts


def contact_pending_evaluation_alerts(
    contacts: Sequence[ContactInvestigation],
    cases_by_id: dict[str, LocalTbCase],
    year: int,
    reference_date: date,
    generated_at: datetime,
) -> list[OperationalAlert]:
    alerts: list[OperationalAlert] = []
    for contact in contacts:
        case = cases_by_id.get(contact.index_case_id)
        if contact.year != year or case is None or contact.evaluation_date is not None:
            continue
        due_date = contact.identified_date + timedelta(days=PENDING_GRACE_DAYS)
        if due_date < reference_date:
            alerts.append(
                make_alert(
                    alert_type="contact_pending_evaluation",
                    severity=OperationalAlertSeverity.MODERATE,
                    case=case,
                    related_entity_id=contact.contact_id,
                    year=year,
                    reference_date=reference_date,
                    generated_at=generated_at,
                    due_date=due_date,
                    message=f"Contact evaluation is pending for index case {case.local_case_id}.",
                )
            )
    return alerts


def resistance_vigilance_alerts(
    cases: Iterable[LocalTbCase],
    lab_events: Sequence[LocalLabEvent],
    year: int,
    reference_date: date,
    generated_at: datetime,
) -> list[OperationalAlert]:
    alerts: list[OperationalAlert] = []
    for case in cases:
        reasons = resistance_reasons(case, lab_events)
        if case.year != year or not reasons:
            continue
        alerts.append(
            make_alert(
                alert_type="resistance_vigilance",
                severity=OperationalAlertSeverity.HIGH,
                case=case,
                related_entity_id=case.local_case_id,
                year=year,
                reference_date=reference_date,
                generated_at=generated_at,
                due_date=None,
                message=f"Resistance vigilance for case {case.local_case_id}: {' '.join(reasons)}",
            )
        )
    return alerts


def latest_dispensings_by_case(
    dispensings: Sequence[MedicationDispensing], year: int
) -> dict[str, MedicationDispensing]:
    latest: dict[str, MedicationDispensing] = {}
    for dispensing in dispensings:
        if dispensing.year != year:
            continue
        existing = latest.get(dispensing.local_case_id)
        if existing is None or dispensing.dispensing_date > existing.dispensing_date:
            latest[dispensing.local_case_id] = dispensing
    return latest


def resistance_reasons(case: LocalTbCase, lab_events: Sequence[LocalLabEvent]) -> list[str]:
    reasons: list[str] = []
    if case.rifampicin_resistance:
        reasons.append("Rifampicin resistance is marked in the local case file.")
    if case.previous_treatment_failure:
        reasons.append("Previous treatment failure is marked in the local case file.")
    if case.retreatment:
        reasons.append("Retreatment is marked in the local case file.")
    if is_pulmonary_retreatment(case) and not has_culture_or_dst_evidence(case, lab_events):
        reasons.append("Pulmonary retreatment has no completed culture/DST evidence in labs.")
    return reasons


def has_culture_or_dst_evidence(case: LocalTbCase, lab_events: Sequence[LocalLabEvent]) -> bool:
    for event in lab_events:
        if event.local_case_id != case.local_case_id or not is_complete_status(event.status):
            continue
        if event.result_date is not None and contains_culture_or_dst_term(event.test_type):
            return True
    return False


def contains_culture_or_dst_term(value: str) -> bool:
    normalized = normalize_text(value)
    return any(term in normalized for term in CULTURE_DST_TERMS)


def is_pulmonary_retreatment(case: LocalTbCase) -> bool:
    return case.retreatment and "pulmon" in normalize_text(case.clinical_form)


def is_open_case(case: LocalTbCase) -> bool:
    return (
        case.closure_date is None
        and normalize_text(case.closure_status) not in CLOSED_CASE_STATUSES
    )


def is_complete_status(status: str) -> bool:
    return normalize_text(status) in COMPLETED_STATUSES


def make_alert(
    *,
    alert_type: str,
    severity: OperationalAlertSeverity,
    case: LocalTbCase,
    related_entity_id: str,
    year: int,
    reference_date: date,
    generated_at: datetime,
    due_date: date | None,
    message: str,
) -> OperationalAlert:
    return OperationalAlert(
        alert_id=build_alert_id(alert_type, related_entity_id, reference_date),
        year=year,
        alert_type=alert_type,
        severity=severity,
        status=OperationalAlertStatus.OPEN,
        local_case_id=case.local_case_id,
        territory_id=case.territory_id,
        facility_id=case.facility_id,
        team_id=case.team_id,
        related_entity_id=related_entity_id,
        reference_date=reference_date,
        generated_at=generated_at,
        due_date=due_date,
        message=message,
    )


def build_alert_id(alert_type: str, related_entity_id: str, reference_date: date) -> str:
    return f"{alert_type}:{related_entity_id}:{reference_date.isoformat()}"


def alert_sort_key(alert: OperationalAlert) -> tuple[str, str, str, str, str]:
    return (
        alert.facility_id,
        alert.team_id,
        alert.alert_type,
        alert.local_case_id,
        alert.related_entity_id,
    )


def normalize_text(value: str) -> str:
    return value.strip().lower().replace("í", "i").replace("ó", "o").replace("ã", "a")
