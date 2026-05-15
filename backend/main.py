from uuid import UUID

from fastapi import FastAPI, HTTPException, Query

from backend.schemas import (
    Alert,
    AlertActionCreate,
    AlertStatus,
    AlertValidationCreate,
    Disclaimer,
    Questionnaire,
    QuestionnaireCreate,
    QuestionnaireSubmissionResponse,
    TerritoryDashboard,
)
from backend.seed import synthetic_questionnaires
from backend.storage import repository


app = FastAPI(
    title="TB-IA Gestao Territorial e Microassistencial",
    version="0.1.0",
    description=(
        "MVP BioChallenge para apoio operacional a APS no cuidado da tuberculose. "
        "Nao diagnostica, nao prescreve e nao substitui profissionais de saude."
    ),
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/disclaimer", response_model=Disclaimer)
def disclaimer() -> Disclaimer:
    return Disclaimer(
        message=(
            "O TB-IA e um MVP com dados sinteticos para apoio operacional. "
            "Nao diagnostica, nao prescreve e nao substitui profissionais de saude."
        ),
        allowed_use=(
            "Organizar fila de trabalho, explicar criterios de priorizacao e apoiar "
            "planejamento territorial em demonstracao ou validacao controlada."
        ),
        forbidden_use=(
            "Usar como diagnostico, decisao clinica automatizada, prescricao, "
            "notificacao oficial ou repositorio de dados reais no MVP."
        ),
    )


@app.post("/questionnaires", response_model=QuestionnaireSubmissionResponse)
def create_questionnaire(payload: QuestionnaireCreate) -> QuestionnaireSubmissionResponse:
    questionnaire, alerts = repository.create_questionnaire(payload)
    return QuestionnaireSubmissionResponse(questionnaire=questionnaire, alerts=alerts)


@app.get("/questionnaires", response_model=list[Questionnaire])
def list_questionnaires() -> list[Questionnaire]:
    return repository.list_questionnaires()


@app.get("/alerts", response_model=list[Alert])
def list_alerts(
    status: AlertStatus | None = None,
    territory_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Alert]:
    return repository.list_alerts(status=status, territory_id=territory_id, limit=limit)


@app.post("/alerts/{alert_id}/validation", response_model=Alert)
def validate_alert(alert_id: UUID, payload: AlertValidationCreate) -> Alert:
    try:
        return repository.validate_alert(alert_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc


@app.post("/alerts/{alert_id}/actions", response_model=Alert)
def add_alert_action(alert_id: UUID, payload: AlertActionCreate) -> Alert:
    try:
        return repository.add_action(alert_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc


@app.get("/dashboard/territories", response_model=list[TerritoryDashboard])
def territory_dashboard() -> list[TerritoryDashboard]:
    return repository.territory_dashboard()


@app.post("/seed/synthetic", response_model=dict[str, int])
def seed_synthetic() -> dict[str, int]:
    repository.reset()
    created_alerts = 0
    payloads = synthetic_questionnaires()
    for payload in payloads:
        _, alerts = repository.create_questionnaire(payload)
        created_alerts += len(alerts)
    return {
        "questionnaires_created": len(payloads),
        "alerts_created": created_alerts,
    }
