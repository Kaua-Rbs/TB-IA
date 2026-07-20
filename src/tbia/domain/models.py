from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any


class IndicatorDirection(StrEnum):
    HIGH_BAD = "high_bad"
    LOW_BAD = "low_bad"
    CONTEXT = "context"


class IndicatorUnit(StrEnum):
    PER_100K = "per_100k"
    PERCENT = "percent"
    COUNT = "count"


class PublicDataStatus(StrEnum):
    OBTAINABLE = "obtainable"
    OBTAINABLE_WITH_TRANSFORMATION = "obtainable_with_transformation"
    CONDITIONAL = "conditional_requires_validation"
    NOT_PUBLICLY_OBTAINABLE = "not_publicly_obtainable"


class ScenarioSeverity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class OperationalAlertSeverity(StrEnum):
    MODERATE = "moderate"
    HIGH = "high"


class OperationalAlertStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass(frozen=True)
class DataSource:
    source_id: str
    name: str
    owner: str
    access_method: str
    format: str
    grain: str
    privacy_level: str
    refresh_cadence: str
    caveats: str


@dataclass(frozen=True)
class ImportRun:
    source_id: str
    status: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    row_count: int = 0
    message: str = ""
    year: int | None = None
    geographic_scope: str | None = None
    loaded_months: tuple[int, ...] | None = None


@dataclass(frozen=True)
class Territory:
    territory_id: str
    name: str
    territory_type: str
    uf_code: str
    uf_sigla: str
    parent_id: str | None = None
    geometry: dict[str, Any] | None = None


@dataclass(frozen=True)
class PopulationDenominator:
    territory_id: str
    year: int
    population: int
    source_id: str
    stratifier: str = "total"


@dataclass(frozen=True)
class CaseAggregate:
    territory_id: str
    year: int
    notified_cases: int = 0
    new_cases: int = 0
    closed_cases: int = 0
    cured_cases: int = 0
    treatment_interruption_cases: int = 0
    retreatment_cases: int = 0
    new_pulmonary_cases: int = 0
    lab_confirmed_pulmonary_cases: int = 0
    hiv_tested_cases: int = 0
    tb_hiv_cases: int = 0
    trm_tb_cases: int = 0
    retreatment_pulmonary_cases: int = 0
    culture_retreated_cases: int = 0
    source_id: str = "sinan_tb"


@dataclass(frozen=True)
class MortalityAggregate:
    territory_id: str
    year: int
    tb_deaths: int
    source_id: str = "sim"


@dataclass(frozen=True)
class HospitalizationAggregate:
    territory_id: str
    year: int
    tb_admissions: int
    source_id: str = "sih_sus"


@dataclass(frozen=True)
class Facility:
    facility_id: str
    territory_id: str
    name: str
    facility_type: str
    sus_linked: bool
    source_id: str = "cnes"


@dataclass(frozen=True)
class LocalTerritory:
    territory_id: str
    name: str
    territory_type: str
    uf_code: str
    uf_sigla: str
    parent_id: str | None = None
    facility_id: str | None = None
    team_id: str | None = None


@dataclass(frozen=True)
class LocalTeam:
    team_id: str
    facility_id: str
    name: str
    team_type: str
    active: bool


@dataclass(frozen=True)
class LocalTbCase:
    local_case_id: str
    pseudonymized_patient_id: str
    territory_id: str
    facility_id: str
    team_id: str
    year: int
    notification_date: date
    diagnosis_date: date | None
    treatment_start_date: date | None
    entry_type: str
    clinical_form: str
    closure_status: str
    closure_date: date | None
    rifampicin_resistance: bool
    retreatment: bool
    previous_treatment_failure: bool


@dataclass(frozen=True)
class LocalLabEvent:
    local_lab_id: str
    local_case_id: str
    pseudonymized_patient_id: str
    test_type: str
    year: int
    request_date: date
    collection_date: date | None
    result_date: date | None
    result: str
    status: str


@dataclass(frozen=True)
class MedicationDispensing:
    dispensing_id: str
    local_case_id: str
    pseudonymized_patient_id: str
    dispensing_date: date
    days_supplied: int
    medication_group: str
    year: int


@dataclass(frozen=True)
class ContactInvestigation:
    contact_id: str
    index_case_id: str
    pseudonymized_contact_id: str
    identified_date: date
    evaluation_date: date | None
    symptomatic: bool
    tpt_started_date: date | None
    status: str
    year: int


@dataclass(frozen=True)
class ResourceInventory:
    facility_id: str
    year: int
    sputum_collection: bool
    rapid_molecular_access: bool
    xray_access: bool
    sample_transport: bool
    pharmacy_tb_meds: bool
    chw_count: int


@dataclass(frozen=True)
class OperationalAlert:
    alert_id: str
    year: int
    alert_type: str
    severity: OperationalAlertSeverity
    status: OperationalAlertStatus
    local_case_id: str
    territory_id: str
    facility_id: str
    team_id: str
    related_entity_id: str
    reference_date: date
    generated_at: datetime
    message: str
    due_date: date | None = None


@dataclass(frozen=True)
class IndicatorDefinition:
    indicator_id: str
    name: str
    unit: IndicatorUnit
    direction: IndicatorDirection
    public_data_status: PublicDataStatus
    numerator: str
    denominator: str
    sources: tuple[str, ...]
    caveats: str
    version: str = "2026.1"
    minimum_count: int = 5


@dataclass(frozen=True)
class IndicatorValue:
    indicator_id: str
    territory_id: str
    year: int
    value: float | None
    numerator_value: float
    denominator_value: float
    is_suppressed: bool
    source_ids: tuple[str, ...]
    caveats: str
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ScenarioRule:
    rule_id: str
    name: str
    indicator_id: str
    threshold_method: str
    comparison_group: str
    severity: ScenarioSeverity
    direction: IndicatorDirection
    explanation_template: str
    strategy_ids: tuple[str, ...]
    ranking_dimension: str = ""
    minimum_count: int = 5


@dataclass(frozen=True)
class TerritoryScenario:
    territory_id: str
    year: int
    rule_id: str
    scenario_id: str
    severity: ScenarioSeverity
    score: float
    explanation: str
    indicator_id: str
    indicator_value: float
    threshold_value: float
    comparison_scope: str = "uf"
    ranking_dimension: str = ""


@dataclass(frozen=True)
class Strategy:
    strategy_id: str
    name: str
    target_problem: str
    evidence_source: str
    evidence_strength: str
    required_resources: str
    estimated_cost_level: str
    operational_complexity: str
    monitoring_indicators: tuple[str, ...]
    caveats: str


@dataclass(frozen=True)
class Recommendation:
    territory_id: str
    year: int
    strategy_id: str
    rule_id: str
    priority: ScenarioSeverity
    explanation: str
    comparison_scope: str = "uf"
    trigger_rule_ids: tuple[str, ...] = ()
