from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Priority(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class AlertStatus(str, Enum):
    pending = "pending"
    validated = "validated"
    dismissed = "dismissed"
    completed = "completed"


class AlertCategory(str, Enum):
    respiratory_symptom_screening = "respiratory_symptom_screening"
    contact_investigation = "contact_investigation"
    adherence_support = "adherence_support"
    territorial_vulnerability = "territorial_vulnerability"


class Symptoms(BaseModel):
    cough_weeks: int = Field(default=0, ge=0, le=52)
    fever: bool = False
    night_sweats: bool = False
    weight_loss: bool = False


class ContactInfo(BaseModel):
    known_tb_contact: bool = False
    household_contact: bool = False
    contact_investigated: bool = False


class AdherenceInfo(BaseModel):
    on_treatment: bool = False
    missed_recent_appointments: bool = False
    treatment_interruption: bool = False
    side_effects_reported: bool = False


class QuestionnaireCreate(BaseModel):
    synthetic_person_id: str = Field(min_length=3, max_length=64)
    territory_id: str = Field(min_length=2, max_length=64)
    territory_name: str = Field(min_length=2, max_length=120)
    micro_area: str = Field(min_length=1, max_length=64)
    age_range: str = Field(default="unknown", max_length=32)
    symptoms: Symptoms = Field(default_factory=Symptoms)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    adherence: AdherenceInfo = Field(default_factory=AdherenceInfo)
    barriers: list[str] = Field(default_factory=list)
    vulnerabilities: list[str] = Field(default_factory=list)
    submitted_by: str = Field(default="demo_user", max_length=80)


class Questionnaire(QuestionnaireCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuestionnaireSubmissionResponse(BaseModel):
    questionnaire: Questionnaire
    alerts: list["Alert"]


class RuleEvaluation(BaseModel):
    score: int
    priority: Priority
    categories: list[AlertCategory]
    rationale: list[str]
    recommended_actions: dict[AlertCategory, str]


class AlertValidationCreate(BaseModel):
    decision: Literal["validated", "dismissed"]
    validated_by: str = Field(min_length=2, max_length=80)
    note: str = Field(default="", max_length=500)


class AlertValidation(AlertValidationCreate):
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertActionCreate(BaseModel):
    action_type: str = Field(min_length=2, max_length=80)
    performed_by: str = Field(min_length=2, max_length=80)
    note: str = Field(default="", max_length=500)


class AlertAction(AlertActionCreate):
    performed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    questionnaire_id: UUID
    synthetic_person_id: str
    territory_id: str
    territory_name: str
    micro_area: str
    category: AlertCategory
    priority: Priority
    score: int
    title: str
    rationale: list[str]
    recommended_action: str
    status: AlertStatus = AlertStatus.pending
    validation: AlertValidation | None = None
    actions: list[AlertAction] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TerritoryDashboard(BaseModel):
    territory_id: str
    territory_name: str
    questionnaires: int
    alerts_total: int
    alerts_by_priority: dict[str, int]
    alerts_by_status: dict[str, int]
    average_score: float


class Disclaimer(BaseModel):
    message: str
    allowed_use: str
    forbidden_use: str
