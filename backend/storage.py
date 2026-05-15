from collections import defaultdict
from threading import Lock
from uuid import UUID

from backend.rules_engine import evaluate_questionnaire, title_for_category
from backend.schemas import (
    Alert,
    AlertAction,
    AlertActionCreate,
    AlertStatus,
    AlertValidation,
    AlertValidationCreate,
    Questionnaire,
    QuestionnaireCreate,
    TerritoryDashboard,
)


class MemoryRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self.questionnaires: dict[UUID, Questionnaire] = {}
        self.alerts: dict[UUID, Alert] = {}

    def reset(self) -> None:
        with self._lock:
            self.questionnaires.clear()
            self.alerts.clear()

    def create_questionnaire(self, payload: QuestionnaireCreate) -> tuple[Questionnaire, list[Alert]]:
        questionnaire = Questionnaire(**payload.model_dump())
        evaluation = evaluate_questionnaire(questionnaire)

        alerts = [
            Alert(
                questionnaire_id=questionnaire.id,
                synthetic_person_id=questionnaire.synthetic_person_id,
                territory_id=questionnaire.territory_id,
                territory_name=questionnaire.territory_name,
                micro_area=questionnaire.micro_area,
                category=category,
                priority=evaluation.priority,
                score=evaluation.score,
                title=title_for_category(category),
                rationale=evaluation.rationale,
                recommended_action=evaluation.recommended_actions[category],
            )
            for category in evaluation.categories
        ]

        with self._lock:
            self.questionnaires[questionnaire.id] = questionnaire
            for alert in alerts:
                self.alerts[alert.id] = alert
        return questionnaire, alerts

    def list_questionnaires(self) -> list[Questionnaire]:
        return sorted(self.questionnaires.values(), key=lambda item: item.created_at)

    def list_alerts(
        self,
        status: AlertStatus | None = None,
        territory_id: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        alerts = list(self.alerts.values())
        if status is not None:
            alerts = [alert for alert in alerts if alert.status == status]
        if territory_id is not None:
            alerts = [alert for alert in alerts if alert.territory_id == territory_id]
        return sorted(
            alerts,
            key=lambda alert: (-alert.score, alert.created_at, alert.synthetic_person_id),
        )[:limit]

    def validate_alert(self, alert_id: UUID, payload: AlertValidationCreate) -> Alert:
        with self._lock:
            alert = self.alerts[alert_id]
            alert.validation = AlertValidation(**payload.model_dump())
            alert.status = (
                AlertStatus.validated
                if payload.decision == "validated"
                else AlertStatus.dismissed
            )
            self.alerts[alert_id] = alert
            return alert

    def add_action(self, alert_id: UUID, payload: AlertActionCreate) -> Alert:
        with self._lock:
            alert = self.alerts[alert_id]
            alert.actions.append(AlertAction(**payload.model_dump()))
            if alert.status == AlertStatus.validated:
                alert.status = AlertStatus.completed
            self.alerts[alert_id] = alert
            return alert

    def territory_dashboard(self) -> list[TerritoryDashboard]:
        questionnaires_by_territory: dict[str, int] = defaultdict(int)
        territory_names: dict[str, str] = {}
        for questionnaire in self.questionnaires.values():
            questionnaires_by_territory[questionnaire.territory_id] += 1
            territory_names[questionnaire.territory_id] = questionnaire.territory_name

        alerts_by_territory: dict[str, list[Alert]] = defaultdict(list)
        for alert in self.alerts.values():
            alerts_by_territory[alert.territory_id].append(alert)
            territory_names[alert.territory_id] = alert.territory_name

        territory_ids = sorted(set(questionnaires_by_territory) | set(alerts_by_territory))
        dashboards: list[TerritoryDashboard] = []
        for territory_id in territory_ids:
            alerts = alerts_by_territory[territory_id]
            priority_counts: dict[str, int] = defaultdict(int)
            status_counts: dict[str, int] = defaultdict(int)
            for alert in alerts:
                priority_counts[alert.priority.value] += 1
                status_counts[alert.status.value] += 1
            average_score = (
                round(sum(alert.score for alert in alerts) / len(alerts), 2)
                if alerts
                else 0.0
            )
            dashboards.append(
                TerritoryDashboard(
                    territory_id=territory_id,
                    territory_name=territory_names.get(territory_id, territory_id),
                    questionnaires=questionnaires_by_territory[territory_id],
                    alerts_total=len(alerts),
                    alerts_by_priority=dict(priority_counts),
                    alerts_by_status=dict(status_counts),
                    average_score=average_score,
                )
            )
        return dashboards


repository = MemoryRepository()

