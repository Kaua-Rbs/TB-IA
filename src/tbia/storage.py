from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    delete,
    inspect,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Query, Session, mapped_column, sessionmaker

from tbia.domain.history import (
    HistoryPointStatus,
    build_indicator_history,
)
from tbia.domain.models import (
    CaseAggregate,
    ContactInvestigation,
    DataSource,
    Facility,
    HospitalizationAggregate,
    ImportRun,
    IndicatorDefinition,
    IndicatorDirection,
    IndicatorUnit,
    IndicatorValue,
    LocalLabEvent,
    LocalResistanceEvidence,
    LocalTbCase,
    LocalTeam,
    LocalTerritory,
    MedicationDispensing,
    MortalityAggregate,
    OperationalAlert,
    OperationalAlertEvidence,
    OperationalAlertSeverity,
    OperationalAlertStatus,
    PopulationDenominator,
    PublicDataStatus,
    Recommendation,
    ResistanceSignalKind,
    ResourceInventory,
    ScenarioEvaluationStatus,
    ScenarioRule,
    ScenarioRuleEvaluation,
    ScenarioSeverity,
    SourceProvenance,
    Strategy,
    Territory,
    TerritoryScenario,
)
from tbia.domain.resistance_surveillance import build_resistance_surveillance_profile
from tbia.domain.scenarios import DIAGNOSTIC_SCENARIO_RULE_IDS, summarize_dimension_scores
from tbia.geography import BRAZIL_SCOPE, normalize_geographic_scope, ufs_for_scope


class Base(DeclarativeBase):
    pass


MUNICIPALITY_TERRITORY_TYPE = "municipality"
NEIGHBORHOOD_REFERENCE_TERRITORY_TYPE = "neighborhood_reference"
PUBLIC_REFERENCE_DATA_LEVEL = "public_reference"
COMPARISON_SCOPE_UF = "uf"
COMPARISON_SCOPE_NATIONAL = "national"
COMPARISON_SCOPES = frozenset({COMPARISON_SCOPE_UF, COMPARISON_SCOPE_NATIONAL})
SUBTERRITORY_REFERENCE_CAVEAT = (
    "Reference neighborhoods are public geographic context; TB indicators and prioritization "
    "remain municipality-level."
)


class DataSourceRecord(Base):
    __tablename__ = "data_sources"

    source_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    owner: Mapped[str] = mapped_column(String(200))
    access_method: Mapped[str] = mapped_column(String(200))
    format: Mapped[str] = mapped_column(String(80))
    grain: Mapped[str] = mapped_column(String(200))
    privacy_level: Mapped[str] = mapped_column(String(120))
    refresh_cadence: Mapped[str] = mapped_column(String(120))
    caveats: Mapped[str] = mapped_column(Text)


class ImportRunRecord(Base):
    __tablename__ = "import_runs"

    import_run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geographic_scope: Mapped[str | None] = mapped_column(String(2), nullable=True)
    loaded_months: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)


class TerritoryRecord(Base):
    __tablename__ = "territories"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    territory_type: Mapped[str] = mapped_column(String(40), index=True)
    uf_code: Mapped[str] = mapped_column(String(10), index=True)
    uf_sigla: Mapped[str] = mapped_column(String(2), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    geometry: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class PopulationDenominatorRecord(Base):
    __tablename__ = "population_denominators"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    stratifier: Mapped[str] = mapped_column(String(80), primary_key=True, default="total")
    population: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[str] = mapped_column(String(80))
    source_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)


class CaseAggregateRecord(Base):
    __tablename__ = "case_aggregates"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    notified_cases: Mapped[int] = mapped_column(Integer, default=0)
    new_cases: Mapped[int] = mapped_column(Integer, default=0)
    closed_cases: Mapped[int] = mapped_column(Integer, default=0)
    cured_cases: Mapped[int] = mapped_column(Integer, default=0)
    treatment_interruption_cases: Mapped[int] = mapped_column(Integer, default=0)
    retreatment_cases: Mapped[int] = mapped_column(Integer, default=0)
    new_pulmonary_cases: Mapped[int] = mapped_column(Integer, default=0)
    lab_confirmed_pulmonary_cases: Mapped[int] = mapped_column(Integer, default=0)
    hiv_tested_cases: Mapped[int] = mapped_column(Integer, default=0)
    tb_hiv_cases: Mapped[int] = mapped_column(Integer, default=0)
    trm_tb_cases: Mapped[int] = mapped_column(Integer, default=0)
    retreatment_pulmonary_cases: Mapped[int] = mapped_column(Integer, default=0)
    culture_retreated_cases: Mapped[int] = mapped_column(Integer, default=0)
    source_id: Mapped[str] = mapped_column(String(80), default="sinan_tb")


class MortalityAggregateRecord(Base):
    __tablename__ = "mortality_aggregates"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    tb_deaths: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[str] = mapped_column(String(80), default="sim")


class HospitalizationAggregateRecord(Base):
    __tablename__ = "hospitalization_aggregates"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    tb_admissions: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[str] = mapped_column(String(80), default="sih_sus")


class FacilityRecord(Base):
    __tablename__ = "facilities"

    facility_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    territory_id: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(200))
    facility_type: Mapped[str] = mapped_column(String(120))
    sus_linked: Mapped[bool] = mapped_column(Boolean, default=True)
    source_id: Mapped[str] = mapped_column(String(80), default="cnes")


class LocalTerritoryRecord(Base):
    __tablename__ = "local_territories"

    territory_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    territory_type: Mapped[str] = mapped_column(String(80), index=True)
    uf_code: Mapped[str] = mapped_column(String(10), index=True)
    uf_sigla: Mapped[str] = mapped_column(String(2), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    facility_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    team_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)


class LocalTeamRecord(Base):
    __tablename__ = "local_teams"

    team_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    facility_id: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(200))
    team_type: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class LocalTbCaseRecord(Base):
    __tablename__ = "local_tb_cases"

    local_case_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    pseudonymized_patient_id: Mapped[str] = mapped_column(String(120))
    territory_id: Mapped[str] = mapped_column(String(80), index=True)
    facility_id: Mapped[str] = mapped_column(String(80), index=True)
    team_id: Mapped[str] = mapped_column(String(80), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    notification_date: Mapped[date] = mapped_column(Date)
    diagnosis_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    treatment_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    entry_type: Mapped[str] = mapped_column(String(80))
    clinical_form: Mapped[str] = mapped_column(String(80))
    closure_status: Mapped[str] = mapped_column(String(80))
    closure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rifampicin_resistance: Mapped[bool] = mapped_column(Boolean, default=False)
    retreatment: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_treatment_failure: Mapped[bool] = mapped_column(Boolean, default=False)


class LocalLabEventRecord(Base):
    __tablename__ = "local_lab_events"

    local_lab_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    local_case_id: Mapped[str] = mapped_column(String(80), index=True)
    pseudonymized_patient_id: Mapped[str] = mapped_column(String(120))
    test_type: Mapped[str] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer, index=True)
    request_date: Mapped[date] = mapped_column(Date)
    collection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(80))


class LocalResistanceEvidenceRecord(Base):
    __tablename__ = "local_resistance_evidence"

    resistance_record_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    local_case_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    pseudonymized_patient_id: Mapped[str] = mapped_column(String(120), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resistance_scope: Mapped[str] = mapped_column(String(120), nullable=False)
    resistance_status: Mapped[str] = mapped_column(String(40), nullable=False)
    record_status: Mapped[str] = mapped_column(String(40), nullable=False)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)


class MedicationDispensingRecord(Base):
    __tablename__ = "medication_dispensings"

    dispensing_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    local_case_id: Mapped[str] = mapped_column(String(80), index=True)
    pseudonymized_patient_id: Mapped[str] = mapped_column(String(120))
    dispensing_date: Mapped[date] = mapped_column(Date)
    days_supplied: Mapped[int] = mapped_column(Integer)
    medication_group: Mapped[str] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer, index=True)


class ContactInvestigationRecord(Base):
    __tablename__ = "contact_investigations"

    contact_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    index_case_id: Mapped[str] = mapped_column(String(80), index=True)
    pseudonymized_contact_id: Mapped[str] = mapped_column(String(120))
    identified_date: Mapped[date] = mapped_column(Date)
    evaluation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    symptomatic: Mapped[bool] = mapped_column(Boolean, default=False)
    tpt_started_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer, index=True)


class ResourceInventoryRecord(Base):
    __tablename__ = "resource_inventories"

    facility_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    sputum_collection: Mapped[bool] = mapped_column(Boolean, default=False)
    rapid_molecular_access: Mapped[bool] = mapped_column(Boolean, default=False)
    xray_access: Mapped[bool] = mapped_column(Boolean, default=False)
    sample_transport: Mapped[bool] = mapped_column(Boolean, default=False)
    pharmacy_tb_meds: Mapped[bool] = mapped_column(Boolean, default=False)
    chw_count: Mapped[int] = mapped_column(Integer, default=0)


class OperationalAlertRecord(Base):
    __tablename__ = "operational_alerts"

    alert_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    alert_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    local_case_id: Mapped[str] = mapped_column(String(80), index=True)
    territory_id: Mapped[str] = mapped_column(String(80), index=True)
    facility_id: Mapped[str] = mapped_column(String(80), index=True)
    team_id: Mapped[str] = mapped_column(String(80), index=True)
    related_entity_id: Mapped[str] = mapped_column(String(80))
    reference_date: Mapped[date] = mapped_column(Date)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    signal_kinds: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)


class IndicatorDefinitionRecord(Base):
    __tablename__ = "indicator_definitions"

    indicator_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    version: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(40))
    direction: Mapped[str] = mapped_column(String(40))
    public_data_status: Mapped[str] = mapped_column(String(80))
    numerator: Mapped[str] = mapped_column(Text)
    denominator: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[str]] = mapped_column(JSON)
    caveats: Mapped[str] = mapped_column(Text)
    minimum_count: Mapped[int] = mapped_column(Integer)


class IndicatorValueRecord(Base):
    __tablename__ = "indicator_values"

    indicator_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    numerator_value: Mapped[float] = mapped_column(Float)
    denominator_value: Mapped[float] = mapped_column(Float)
    is_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    source_ids: Mapped[list[str]] = mapped_column(JSON)
    caveats: Mapped[str] = mapped_column(Text)
    denominator_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_provenance: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioRuleRecord(Base):
    __tablename__ = "scenario_rules"

    rule_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    indicator_id: Mapped[str] = mapped_column(String(120))
    threshold_method: Mapped[str] = mapped_column(String(80))
    comparison_group: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(40))
    direction: Mapped[str] = mapped_column(String(40))
    explanation_template: Mapped[str] = mapped_column(Text)
    strategy_ids: Mapped[list[str]] = mapped_column(JSON)
    minimum_count: Mapped[int] = mapped_column(Integer)
    ranking_dimension: Mapped[str] = mapped_column(String(120), server_default="")
    minimum_coverage_ratio: Mapped[float] = mapped_column(Float, server_default="0")
    review_status: Mapped[str | None] = mapped_column(String(80), nullable=True)


class TerritoryScenarioRecord(Base):
    __tablename__ = "territory_scenarios"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_scope: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=COMPARISON_SCOPE_UF
    )
    rule_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(40))
    score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    indicator_id: Mapped[str] = mapped_column(String(120))
    indicator_value: Mapped[float] = mapped_column(Float)
    threshold_value: Mapped[float] = mapped_column(Float)
    ranking_dimension: Mapped[str] = mapped_column(String(120), server_default="")
    review_status: Mapped[str | None] = mapped_column(String(80), nullable=True)


class ScenarioRuleEvaluationRecord(Base):
    __tablename__ = "scenario_rule_evaluations"

    geographic_scope: Mapped[str] = mapped_column(String(2), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_scope: Mapped[str] = mapped_column(String(20), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    status: Mapped[str] = mapped_column(String(40))
    available_count: Mapped[int] = mapped_column(Integer)
    suppressed_count: Mapped[int] = mapped_column(Integer)
    unavailable_count: Mapped[int] = mapped_column(Integer)
    territory_count: Mapped[int] = mapped_column(Integer)
    coverage_ratio: Mapped[float] = mapped_column(Float)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_count: Mapped[int] = mapped_column(Integer)
    minimum_coverage_ratio: Mapped[float] = mapped_column(Float)


class StrategyRecord(Base):
    __tablename__ = "strategies"

    strategy_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    target_problem: Mapped[str] = mapped_column(Text)
    evidence_source: Mapped[str] = mapped_column(Text)
    evidence_strength: Mapped[str] = mapped_column(String(120))
    required_resources: Mapped[str] = mapped_column(Text)
    estimated_cost_level: Mapped[str] = mapped_column(String(40))
    operational_complexity: Mapped[str] = mapped_column(String(40))
    monitoring_indicators: Mapped[list[str]] = mapped_column(JSON)
    caveats: Mapped[str] = mapped_column(Text)


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_scope: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=COMPARISON_SCOPE_UF
    )
    strategy_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    priority: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text)
    trigger_rule_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)


def create_engine_for_url(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    migrate_import_run_scope_columns(engine)
    migrate_indicator_provenance_columns(engine)
    migrate_comparison_scope_tables(engine)
    migrate_scenario_metadata_columns(engine)
    migrate_operational_alert_evidence_columns(engine)


def migrate_operational_alert_evidence_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(OperationalAlertRecord.__tablename__):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns(OperationalAlertRecord.__tablename__)
    }
    with engine.begin() as connection:
        if "signal_kinds" not in existing_columns:
            connection.execute(text("ALTER TABLE operational_alerts ADD COLUMN signal_kinds JSON"))
        if "review_status" not in existing_columns:
            connection.execute(
                text("ALTER TABLE operational_alerts ADD COLUMN review_status VARCHAR(80)")
            )
        if "evidence" not in existing_columns:
            connection.execute(text("ALTER TABLE operational_alerts ADD COLUMN evidence JSON"))


def migrate_import_run_scope_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(ImportRunRecord.__tablename__):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns(ImportRunRecord.__tablename__)
    }
    with engine.begin() as connection:
        if "year" not in existing_columns:
            connection.execute(text("ALTER TABLE import_runs ADD COLUMN year INTEGER"))
        if "geographic_scope" not in existing_columns:
            connection.execute(
                text("ALTER TABLE import_runs ADD COLUMN geographic_scope VARCHAR(2)")
            )
        if "loaded_months" not in existing_columns:
            connection.execute(text("ALTER TABLE import_runs ADD COLUMN loaded_months JSON"))
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_import_runs_source_year_scope "
                "ON import_runs (source_id, year, geographic_scope, import_run_id)"
            )
        )


def migrate_indicator_provenance_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    population_columns = {
        column["name"]
        for column in inspector.get_columns(PopulationDenominatorRecord.__tablename__)
    }
    indicator_columns = {
        column["name"] for column in inspector.get_columns(IndicatorValueRecord.__tablename__)
    }

    with engine.begin() as connection:
        if "source_year" not in population_columns:
            connection.execute(
                text("ALTER TABLE population_denominators ADD COLUMN source_year INTEGER")
            )
        if "source_kind" not in population_columns:
            connection.execute(
                text("ALTER TABLE population_denominators ADD COLUMN source_kind VARCHAR(40)")
            )
        if "denominator_year" not in indicator_columns:
            connection.execute(
                text("ALTER TABLE indicator_values ADD COLUMN denominator_year INTEGER")
            )
        if "source_provenance" not in indicator_columns:
            connection.execute(
                text("ALTER TABLE indicator_values ADD COLUMN source_provenance JSON")
            )


def migrate_comparison_scope_tables(engine: Engine) -> None:
    migrate_comparison_scope_table(
        engine,
        TerritoryScenarioRecord.__table__,
        (
            "territory_id",
            "year",
            "comparison_scope",
            "rule_id",
            "scenario_id",
            "severity",
            "score",
            "explanation",
            "indicator_id",
            "indicator_value",
            "threshold_value",
        ),
    )
    migrate_comparison_scope_table(
        engine,
        RecommendationRecord.__table__,
        (
            "territory_id",
            "year",
            "comparison_scope",
            "strategy_id",
            "rule_id",
            "priority",
            "explanation",
        ),
    )


def migrate_scenario_metadata_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    rule_columns = {
        column["name"] for column in inspector.get_columns(ScenarioRuleRecord.__tablename__)
    }
    scenario_columns = {
        column["name"] for column in inspector.get_columns(TerritoryScenarioRecord.__tablename__)
    }
    recommendation_columns = {
        column["name"] for column in inspector.get_columns(RecommendationRecord.__tablename__)
    }

    with engine.begin() as connection:
        if "ranking_dimension" not in rule_columns:
            connection.execute(
                text("ALTER TABLE scenario_rules ADD COLUMN ranking_dimension VARCHAR(120)")
            )
        if "minimum_coverage_ratio" not in rule_columns:
            connection.execute(
                text("ALTER TABLE scenario_rules ADD COLUMN minimum_coverage_ratio FLOAT DEFAULT 0")
            )
        if "review_status" not in rule_columns:
            connection.execute(
                text("ALTER TABLE scenario_rules ADD COLUMN review_status VARCHAR(80)")
            )
        if "ranking_dimension" not in scenario_columns:
            connection.execute(
                text("ALTER TABLE territory_scenarios ADD COLUMN ranking_dimension VARCHAR(120)")
            )
        if "review_status" not in scenario_columns:
            connection.execute(
                text("ALTER TABLE territory_scenarios ADD COLUMN review_status VARCHAR(80)")
            )
        if "trigger_rule_ids" not in recommendation_columns:
            connection.execute(text("ALTER TABLE recommendations ADD COLUMN trigger_rule_ids JSON"))
        connection.execute(
            text(
                "UPDATE scenario_rules SET ranking_dimension = rule_id "
                "WHERE ranking_dimension IS NULL OR ranking_dimension = ''"
            )
        )
        connection.execute(
            text(
                "UPDATE scenario_rules SET minimum_coverage_ratio = 0 "
                "WHERE minimum_coverage_ratio IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE territory_scenarios SET ranking_dimension = rule_id "
                "WHERE ranking_dimension IS NULL OR ranking_dimension = ''"
            )
        )
        connection.execute(
            text(
                "UPDATE recommendations SET trigger_rule_ids = json_array(rule_id) "
                "WHERE trigger_rule_ids IS NULL"
            )
        )


def migrate_comparison_scope_table(
    engine: Engine,
    table: Any,
    columns: Sequence[str],
) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(table.name):
        return
    existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
    primary_key_columns = set(inspector.get_pk_constraint(table.name)["constrained_columns"])
    if "comparison_scope" in existing_columns and "comparison_scope" in primary_key_columns:
        return

    legacy_table_name = f"{table.name}_legacy_comparison_scope"
    with engine.begin() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {legacy_table_name}"))
        connection.execute(text(f"ALTER TABLE {table.name} RENAME TO {legacy_table_name}"))
        table.create(connection)
        select_columns = [
            column if column in existing_columns else f"'{COMPARISON_SCOPE_UF}' AS {column}"
            for column in columns
        ]
        connection.execute(
            text(
                f"INSERT INTO {table.name} ({', '.join(columns)}) "
                f"SELECT {', '.join(select_columns)} FROM {legacy_table_name}"
            )
        )
        connection.execute(text(f"DROP TABLE {legacy_table_name}"))


def save_data_sources(session: Session, sources: Iterable[DataSource]) -> None:
    for source in sources:
        session.merge(
            DataSourceRecord(
                source_id=source.source_id,
                name=source.name,
                owner=source.owner,
                access_method=source.access_method,
                format=source.format,
                grain=source.grain,
                privacy_level=source.privacy_level,
                refresh_cadence=source.refresh_cadence,
                caveats=source.caveats,
            )
        )


def save_import_run(session: Session, import_run: ImportRun) -> None:
    session.add(
        ImportRunRecord(
            source_id=import_run.source_id,
            status=import_run.status,
            started_at=import_run.started_at,
            finished_at=import_run.finished_at,
            row_count=import_run.row_count,
            message=import_run.message,
            year=import_run.year,
            geographic_scope=import_run.geographic_scope,
            loaded_months=(
                list(import_run.loaded_months) if import_run.loaded_months is not None else None
            ),
        )
    )


def save_territories(session: Session, territories: Iterable[Territory]) -> None:
    for territory in territories:
        session.merge(
            TerritoryRecord(
                territory_id=territory.territory_id,
                name=territory.name,
                territory_type=territory.territory_type,
                uf_code=territory.uf_code,
                uf_sigla=territory.uf_sigla,
                parent_id=territory.parent_id,
                geometry=territory.geometry,
            )
        )


def save_populations(session: Session, populations: Iterable[PopulationDenominator]) -> None:
    for population in populations:
        session.merge(
            PopulationDenominatorRecord(
                territory_id=population.territory_id,
                year=population.year,
                stratifier=population.stratifier,
                population=population.population,
                source_id=population.source_id,
                source_year=population.source_year,
                source_kind=population.source_kind,
            )
        )


def replacement_territory_ids(
    explicit_ids: Iterable[str] | None,
    rows: Iterable[Any],
) -> set[str]:
    if explicit_ids is not None:
        return set(explicit_ids)
    return {str(row.territory_id) for row in rows}


def delete_public_rows(
    session: Session,
    record_type: Any,
    years: set[int],
    territory_ids: set[str],
) -> None:
    if not years or not territory_ids:
        return
    session.execute(
        delete(record_type).where(
            record_type.year.in_(years),
            record_type.territory_id.in_(territory_ids),
        )
    )


def save_case_aggregates(
    session: Session,
    aggregates: Iterable[CaseAggregate],
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    rows = list(aggregates)
    if not rows:
        return
    years = {aggregate.year for aggregate in rows}
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    delete_public_rows(session, CaseAggregateRecord, years, territory_ids)
    for aggregate in rows:
        session.merge(
            CaseAggregateRecord(
                territory_id=aggregate.territory_id,
                year=aggregate.year,
                notified_cases=aggregate.notified_cases,
                new_cases=aggregate.new_cases,
                closed_cases=aggregate.closed_cases,
                cured_cases=aggregate.cured_cases,
                treatment_interruption_cases=aggregate.treatment_interruption_cases,
                retreatment_cases=aggregate.retreatment_cases,
                new_pulmonary_cases=aggregate.new_pulmonary_cases,
                lab_confirmed_pulmonary_cases=aggregate.lab_confirmed_pulmonary_cases,
                hiv_tested_cases=aggregate.hiv_tested_cases,
                tb_hiv_cases=aggregate.tb_hiv_cases,
                trm_tb_cases=aggregate.trm_tb_cases,
                retreatment_pulmonary_cases=aggregate.retreatment_pulmonary_cases,
                culture_retreated_cases=aggregate.culture_retreated_cases,
                source_id=aggregate.source_id,
            )
        )


def save_mortalities(
    session: Session,
    mortalities: Iterable[MortalityAggregate],
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    rows = list(mortalities)
    if not rows:
        return
    years = {mortality.year for mortality in rows}
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    delete_public_rows(session, MortalityAggregateRecord, years, territory_ids)
    for mortality in rows:
        session.merge(
            MortalityAggregateRecord(
                territory_id=mortality.territory_id,
                year=mortality.year,
                tb_deaths=mortality.tb_deaths,
                source_id=mortality.source_id,
            )
        )


def save_hospitalizations(
    session: Session,
    hospitalizations: Iterable[HospitalizationAggregate],
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    rows = list(hospitalizations)
    if not rows:
        return
    years = {hospitalization.year for hospitalization in rows}
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    delete_public_rows(session, HospitalizationAggregateRecord, years, territory_ids)
    for hospitalization in rows:
        session.merge(
            HospitalizationAggregateRecord(
                territory_id=hospitalization.territory_id,
                year=hospitalization.year,
                tb_admissions=hospitalization.tb_admissions,
                source_id=hospitalization.source_id,
            )
        )


def save_facilities(session: Session, facilities: Iterable[Facility]) -> None:
    for facility in facilities:
        session.merge(
            FacilityRecord(
                facility_id=facility.facility_id,
                territory_id=facility.territory_id,
                name=facility.name,
                facility_type=facility.facility_type,
                sus_linked=facility.sus_linked,
                source_id=facility.source_id,
            )
        )


def clear_local_dimensions(session: Session) -> None:
    session.execute(delete(LocalTerritoryRecord))
    session.execute(delete(LocalTeamRecord))


def clear_local_data_for_year(session: Session, year: int) -> None:
    session.execute(delete(LocalTbCaseRecord).where(LocalTbCaseRecord.year == year))
    session.execute(delete(LocalLabEventRecord).where(LocalLabEventRecord.year == year))
    session.execute(
        delete(LocalResistanceEvidenceRecord).where(LocalResistanceEvidenceRecord.year == year)
    )
    session.execute(
        delete(MedicationDispensingRecord).where(MedicationDispensingRecord.year == year)
    )
    session.execute(
        delete(ContactInvestigationRecord).where(ContactInvestigationRecord.year == year)
    )
    session.execute(delete(ResourceInventoryRecord).where(ResourceInventoryRecord.year == year))
    session.execute(delete(OperationalAlertRecord).where(OperationalAlertRecord.year == year))


def save_local_territories(session: Session, territories: Iterable[LocalTerritory]) -> None:
    for territory in territories:
        session.merge(
            LocalTerritoryRecord(
                territory_id=territory.territory_id,
                name=territory.name,
                territory_type=territory.territory_type,
                parent_id=territory.parent_id,
                uf_code=territory.uf_code,
                uf_sigla=territory.uf_sigla,
                facility_id=territory.facility_id,
                team_id=territory.team_id,
            )
        )


def save_local_teams(session: Session, teams: Iterable[LocalTeam]) -> None:
    for team in teams:
        session.merge(
            LocalTeamRecord(
                team_id=team.team_id,
                facility_id=team.facility_id,
                name=team.name,
                team_type=team.team_type,
                active=team.active,
            )
        )


def save_local_tb_cases(session: Session, cases: Iterable[LocalTbCase]) -> None:
    for case in cases:
        session.merge(
            LocalTbCaseRecord(
                local_case_id=case.local_case_id,
                pseudonymized_patient_id=case.pseudonymized_patient_id,
                territory_id=case.territory_id,
                facility_id=case.facility_id,
                team_id=case.team_id,
                year=case.year,
                notification_date=case.notification_date,
                diagnosis_date=case.diagnosis_date,
                treatment_start_date=case.treatment_start_date,
                entry_type=case.entry_type,
                clinical_form=case.clinical_form,
                closure_status=case.closure_status,
                closure_date=case.closure_date,
                rifampicin_resistance=case.rifampicin_resistance,
                retreatment=case.retreatment,
                previous_treatment_failure=case.previous_treatment_failure,
            )
        )


def save_local_lab_events(session: Session, lab_events: Iterable[LocalLabEvent]) -> None:
    for event in lab_events:
        session.merge(
            LocalLabEventRecord(
                local_lab_id=event.local_lab_id,
                local_case_id=event.local_case_id,
                pseudonymized_patient_id=event.pseudonymized_patient_id,
                test_type=event.test_type,
                year=event.year,
                request_date=event.request_date,
                collection_date=event.collection_date,
                result_date=event.result_date,
                result=event.result,
                status=event.status,
            )
        )


def save_local_resistance_evidence(
    session: Session, records: Iterable[LocalResistanceEvidence]
) -> None:
    for record in records:
        session.merge(
            LocalResistanceEvidenceRecord(
                resistance_record_id=record.resistance_record_id,
                local_case_id=record.local_case_id,
                pseudonymized_patient_id=record.pseudonymized_patient_id,
                year=record.year,
                recorded_date=record.recorded_date,
                evidence_type=record.evidence_type,
                resistance_scope=record.resistance_scope,
                resistance_status=record.resistance_status,
                record_status=record.record_status,
                source_system=record.source_system,
            )
        )


def save_medication_dispensings(
    session: Session, dispensings: Iterable[MedicationDispensing]
) -> None:
    for dispensing in dispensings:
        session.merge(
            MedicationDispensingRecord(
                dispensing_id=dispensing.dispensing_id,
                local_case_id=dispensing.local_case_id,
                pseudonymized_patient_id=dispensing.pseudonymized_patient_id,
                dispensing_date=dispensing.dispensing_date,
                days_supplied=dispensing.days_supplied,
                medication_group=dispensing.medication_group,
                year=dispensing.year,
            )
        )


def save_contact_investigations(session: Session, contacts: Iterable[ContactInvestigation]) -> None:
    for contact in contacts:
        session.merge(
            ContactInvestigationRecord(
                contact_id=contact.contact_id,
                index_case_id=contact.index_case_id,
                pseudonymized_contact_id=contact.pseudonymized_contact_id,
                identified_date=contact.identified_date,
                evaluation_date=contact.evaluation_date,
                symptomatic=contact.symptomatic,
                tpt_started_date=contact.tpt_started_date,
                status=contact.status,
                year=contact.year,
            )
        )


def save_resource_inventories(session: Session, resources: Iterable[ResourceInventory]) -> None:
    for resource in resources:
        session.merge(
            ResourceInventoryRecord(
                facility_id=resource.facility_id,
                year=resource.year,
                sputum_collection=resource.sputum_collection,
                rapid_molecular_access=resource.rapid_molecular_access,
                xray_access=resource.xray_access,
                sample_transport=resource.sample_transport,
                pharmacy_tb_meds=resource.pharmacy_tb_meds,
                chw_count=resource.chw_count,
            )
        )


def operational_alert_evidence_payload(
    evidence: OperationalAlertEvidence,
) -> dict[str, Any]:
    return {
        "code": evidence.code,
        "signal_kind": evidence.signal_kind.value,
        "source_ids": list(evidence.source_ids),
        "source_record_id": evidence.source_record_id,
        "observed_at": evidence.observed_at.isoformat()
        if evidence.observed_at is not None
        else None,
        "resistance_scope": evidence.resistance_scope,
        "evidence_status": evidence.evidence_status,
        "source_system": evidence.source_system,
    }


def operational_alert_evidence_from_payload(
    payload: dict[str, Any],
) -> OperationalAlertEvidence:
    source_ids = payload.get("source_ids")
    observed_at = payload.get("observed_at")
    return OperationalAlertEvidence(
        code=str(payload["code"]),
        signal_kind=ResistanceSignalKind(str(payload["signal_kind"])),
        source_ids=tuple(str(value) for value in source_ids)
        if isinstance(source_ids, list)
        else (),
        source_record_id=optional_payload_text(payload.get("source_record_id")),
        observed_at=date.fromisoformat(str(observed_at)) if observed_at else None,
        resistance_scope=optional_payload_text(payload.get("resistance_scope")),
        evidence_status=optional_payload_text(payload.get("evidence_status")),
        source_system=optional_payload_text(payload.get("source_system")),
    )


def optional_payload_text(value: Any) -> str | None:
    return str(value) if value is not None else None


def save_operational_alerts(
    session: Session, alerts: Iterable[OperationalAlert], year: int
) -> None:
    session.execute(delete(OperationalAlertRecord).where(OperationalAlertRecord.year == year))
    for alert in alerts:
        session.merge(
            OperationalAlertRecord(
                alert_id=alert.alert_id,
                year=alert.year,
                alert_type=alert.alert_type,
                severity=alert.severity.value,
                status=alert.status.value,
                local_case_id=alert.local_case_id,
                territory_id=alert.territory_id,
                facility_id=alert.facility_id,
                team_id=alert.team_id,
                related_entity_id=alert.related_entity_id,
                reference_date=alert.reference_date,
                generated_at=alert.generated_at,
                due_date=alert.due_date,
                message=alert.message,
                signal_kinds=[kind.value for kind in alert.signal_kinds],
                review_status=alert.review_status,
                evidence=[operational_alert_evidence_payload(item) for item in alert.evidence],
            )
        )


def save_indicator_definitions(
    session: Session,
    definitions: Iterable[IndicatorDefinition],
) -> None:
    for definition in definitions:
        session.merge(
            IndicatorDefinitionRecord(
                indicator_id=definition.indicator_id,
                version=definition.version,
                name=definition.name,
                unit=definition.unit.value,
                direction=definition.direction.value,
                public_data_status=definition.public_data_status.value,
                numerator=definition.numerator,
                denominator=definition.denominator,
                sources=list(definition.sources),
                caveats=definition.caveats,
                minimum_count=definition.minimum_count,
            )
        )


def save_indicator_values(
    session: Session,
    values: Iterable[IndicatorValue],
    year: int,
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    rows = list(values)
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    delete_public_rows(session, IndicatorValueRecord, {year}, territory_ids)
    merge_indicator_values(session, rows)


def save_indicator_history_values(
    session: Session,
    values: Iterable[IndicatorValue],
    *,
    indicator_id: str,
    start_year: int,
    end_year: int,
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    if start_year > end_year:
        raise ValueError("history start year must not exceed end year")
    rows = list(values)
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    for value in rows:
        if value.indicator_id != indicator_id:
            raise ValueError(f"unexpected indicator history value: {value.indicator_id}")
        if value.year < start_year or value.year > end_year:
            raise ValueError(f"indicator history year outside replacement range: {value.year}")
        if territory_ids and value.territory_id not in territory_ids:
            raise ValueError(
                f"indicator history territory outside replacement scope: {value.territory_id}"
            )

    if territory_ids:
        session.execute(
            delete(IndicatorValueRecord).where(
                IndicatorValueRecord.indicator_id == indicator_id,
                IndicatorValueRecord.year.between(start_year, end_year),
                IndicatorValueRecord.territory_id.in_(territory_ids),
            )
        )
    merge_indicator_values(session, rows)


def merge_indicator_values(
    session: Session,
    values: Iterable[IndicatorValue],
) -> None:
    for value in values:
        session.merge(
            IndicatorValueRecord(
                indicator_id=value.indicator_id,
                territory_id=value.territory_id,
                year=value.year,
                value=value.value,
                numerator_value=value.numerator_value,
                denominator_value=value.denominator_value,
                is_suppressed=value.is_suppressed,
                source_ids=list(value.source_ids),
                caveats=value.caveats,
                denominator_year=value.denominator_year,
                source_provenance=[
                    {
                        "source_id": item.source_id,
                        "reference_year": item.reference_year,
                        "release_status": item.release_status,
                        "dataset_kind": item.dataset_kind,
                        "artifact_sha256": item.artifact_sha256,
                    }
                    for item in value.source_provenance
                ],
                computed_at=value.computed_at,
            )
        )


def save_scenario_rules(session: Session, rules: Iterable[ScenarioRule]) -> None:
    for rule in rules:
        session.merge(
            ScenarioRuleRecord(
                rule_id=rule.rule_id,
                name=rule.name,
                indicator_id=rule.indicator_id,
                threshold_method=rule.threshold_method,
                comparison_group=rule.comparison_group,
                severity=rule.severity.value,
                direction=rule.direction.value,
                explanation_template=rule.explanation_template,
                strategy_ids=list(rule.strategy_ids),
                minimum_count=rule.minimum_count,
                ranking_dimension=rule.ranking_dimension or rule.rule_id,
                minimum_coverage_ratio=rule.minimum_coverage_ratio,
                review_status=rule.review_status,
            )
        )


def save_territory_scenarios(
    session: Session,
    scenarios: Iterable[TerritoryScenario],
    year: int,
    comparison_scope: str = COMPARISON_SCOPE_UF,
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    rows = list(scenarios)
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    if territory_ids:
        session.execute(
            delete(TerritoryScenarioRecord).where(
                TerritoryScenarioRecord.year == year,
                TerritoryScenarioRecord.comparison_scope == comparison_scope,
                TerritoryScenarioRecord.territory_id.in_(territory_ids),
            )
        )
    for scenario in rows:
        session.merge(
            TerritoryScenarioRecord(
                territory_id=scenario.territory_id,
                year=scenario.year,
                comparison_scope=scenario.comparison_scope,
                rule_id=scenario.rule_id,
                scenario_id=scenario.scenario_id,
                severity=scenario.severity.value,
                score=scenario.score,
                explanation=scenario.explanation,
                indicator_id=scenario.indicator_id,
                indicator_value=scenario.indicator_value,
                threshold_value=scenario.threshold_value,
                ranking_dimension=scenario.ranking_dimension or scenario.rule_id,
                review_status=scenario.review_status,
            )
        )


def save_scenario_rule_evaluations(
    session: Session,
    evaluations: Iterable[ScenarioRuleEvaluation],
    year: int,
    comparison_scope: str,
    *,
    replace_geographic_scopes: Iterable[str],
) -> None:
    rows = list(evaluations)
    geographic_scopes = set(replace_geographic_scopes)
    if geographic_scopes:
        session.execute(
            delete(ScenarioRuleEvaluationRecord).where(
                ScenarioRuleEvaluationRecord.year == year,
                ScenarioRuleEvaluationRecord.comparison_scope == comparison_scope,
                ScenarioRuleEvaluationRecord.geographic_scope.in_(geographic_scopes),
            )
        )
    for evaluation in rows:
        session.merge(
            ScenarioRuleEvaluationRecord(
                geographic_scope=evaluation.geographic_scope,
                year=evaluation.year,
                comparison_scope=evaluation.comparison_scope,
                rule_id=evaluation.rule_id,
                status=evaluation.status.value,
                available_count=evaluation.available_count,
                suppressed_count=evaluation.suppressed_count,
                unavailable_count=evaluation.unavailable_count,
                territory_count=evaluation.territory_count,
                coverage_ratio=evaluation.coverage_ratio,
                threshold_value=evaluation.threshold_value,
                minimum_count=evaluation.minimum_count,
                minimum_coverage_ratio=evaluation.minimum_coverage_ratio,
            )
        )


def save_strategies(session: Session, strategies: Iterable[Strategy]) -> None:
    for strategy in strategies:
        session.merge(
            StrategyRecord(
                strategy_id=strategy.strategy_id,
                name=strategy.name,
                target_problem=strategy.target_problem,
                evidence_source=strategy.evidence_source,
                evidence_strength=strategy.evidence_strength,
                required_resources=strategy.required_resources,
                estimated_cost_level=strategy.estimated_cost_level,
                operational_complexity=strategy.operational_complexity,
                monitoring_indicators=list(strategy.monitoring_indicators),
                caveats=strategy.caveats,
            )
        )


def save_recommendations(
    session: Session,
    recommendations: Iterable[Recommendation],
    year: int,
    comparison_scope: str = COMPARISON_SCOPE_UF,
    replace_territory_ids: Iterable[str] | None = None,
) -> None:
    rows = list(recommendations)
    territory_ids = replacement_territory_ids(replace_territory_ids, rows)
    if territory_ids:
        session.execute(
            delete(RecommendationRecord).where(
                RecommendationRecord.year == year,
                RecommendationRecord.comparison_scope == comparison_scope,
                RecommendationRecord.territory_id.in_(territory_ids),
            )
        )
    for recommendation in rows:
        session.merge(
            RecommendationRecord(
                territory_id=recommendation.territory_id,
                year=recommendation.year,
                comparison_scope=recommendation.comparison_scope,
                strategy_id=recommendation.strategy_id,
                rule_id=recommendation.rule_id,
                priority=recommendation.priority.value,
                explanation=recommendation.explanation,
                trigger_rule_ids=list(recommendation.trigger_rule_ids or (recommendation.rule_id,)),
            )
        )


def load_populations(session: Session, year: int) -> list[PopulationDenominator]:
    records = session.query(PopulationDenominatorRecord).filter_by(year=year).all()
    return [
        PopulationDenominator(
            territory_id=record.territory_id,
            year=record.year,
            population=record.population,
            source_id=record.source_id,
            stratifier=record.stratifier,
            source_year=record.source_year,
            source_kind=record.source_kind or "unknown",
        )
        for record in records
    ]


def load_cases(session: Session, year: int) -> list[CaseAggregate]:
    records = session.query(CaseAggregateRecord).filter_by(year=year).all()
    return [
        CaseAggregate(
            territory_id=record.territory_id,
            year=record.year,
            notified_cases=record.notified_cases,
            new_cases=record.new_cases,
            closed_cases=record.closed_cases,
            cured_cases=record.cured_cases,
            treatment_interruption_cases=record.treatment_interruption_cases,
            retreatment_cases=record.retreatment_cases,
            new_pulmonary_cases=record.new_pulmonary_cases,
            lab_confirmed_pulmonary_cases=record.lab_confirmed_pulmonary_cases,
            hiv_tested_cases=record.hiv_tested_cases,
            tb_hiv_cases=record.tb_hiv_cases,
            trm_tb_cases=record.trm_tb_cases,
            retreatment_pulmonary_cases=record.retreatment_pulmonary_cases,
            culture_retreated_cases=record.culture_retreated_cases,
            source_id=record.source_id,
        )
        for record in records
    ]


def load_mortalities(session: Session, year: int) -> list[MortalityAggregate]:
    records = session.query(MortalityAggregateRecord).filter_by(year=year).all()
    return [
        MortalityAggregate(
            territory_id=record.territory_id,
            year=record.year,
            tb_deaths=record.tb_deaths,
            source_id=record.source_id,
        )
        for record in records
    ]


def load_hospitalizations(session: Session, year: int) -> list[HospitalizationAggregate]:
    records = session.query(HospitalizationAggregateRecord).filter_by(year=year).all()
    return [
        HospitalizationAggregate(
            territory_id=record.territory_id,
            year=record.year,
            tb_admissions=record.tb_admissions,
            source_id=record.source_id,
        )
        for record in records
    ]


def load_indicator_values(
    session: Session,
    year: int,
    territory_ids: Iterable[str] | None = None,
) -> list[IndicatorValue]:
    query = session.query(IndicatorValueRecord).filter_by(year=year)
    if territory_ids is not None:
        ids = set(territory_ids)
        if not ids:
            return []
        query = query.filter(IndicatorValueRecord.territory_id.in_(ids))
    records = query.all()
    return [hydrate_indicator_value(record) for record in records]


def load_indicator_history_values(
    session: Session,
    *,
    indicator_id: str,
    start_year: int,
    end_year: int,
    territory_ids: Iterable[str] | None = None,
) -> list[IndicatorValue]:
    if start_year > end_year:
        raise ValueError("history start year must not exceed end year")
    query = session.query(IndicatorValueRecord).filter(
        IndicatorValueRecord.indicator_id == indicator_id,
        IndicatorValueRecord.year.between(start_year, end_year),
    )
    if territory_ids is not None:
        ids = set(territory_ids)
        if not ids:
            return []
        query = query.filter(IndicatorValueRecord.territory_id.in_(ids))
    records = query.order_by(
        IndicatorValueRecord.territory_id,
        IndicatorValueRecord.year,
    ).all()
    return [hydrate_indicator_value(record) for record in records]


def hydrate_indicator_value(record: IndicatorValueRecord) -> IndicatorValue:
    return IndicatorValue(
        indicator_id=record.indicator_id,
        territory_id=record.territory_id,
        year=record.year,
        value=record.value,
        numerator_value=record.numerator_value,
        denominator_value=record.denominator_value,
        is_suppressed=record.is_suppressed,
        source_ids=tuple(record.source_ids),
        caveats=record.caveats,
        denominator_year=record.denominator_year,
        source_provenance=tuple(
            SourceProvenance(
                source_id=str(item["source_id"]),
                reference_year=(
                    int(item["reference_year"]) if item.get("reference_year") is not None else None
                ),
                release_status=str(item.get("release_status", "unknown")),
                dataset_kind=str(item.get("dataset_kind", "unknown")),
                artifact_sha256=(
                    str(item["artifact_sha256"])
                    if item.get("artifact_sha256") is not None
                    else None
                ),
            )
            for item in (record.source_provenance or [])
        ),
        computed_at=record.computed_at,
    )


def load_territory_scenarios(
    session: Session,
    year: int,
    comparison_scope: str | None = None,
) -> list[TerritoryScenario]:
    query = session.query(TerritoryScenarioRecord).filter_by(year=year)
    if comparison_scope is not None:
        query = query.filter_by(comparison_scope=comparison_scope)
    records = query.all()
    return [
        TerritoryScenario(
            territory_id=record.territory_id,
            year=record.year,
            rule_id=record.rule_id,
            scenario_id=record.scenario_id,
            severity=ScenarioSeverity(record.severity),
            score=record.score,
            explanation=record.explanation,
            indicator_id=record.indicator_id,
            indicator_value=record.indicator_value,
            threshold_value=record.threshold_value,
            comparison_scope=record.comparison_scope,
            ranking_dimension=record.ranking_dimension or record.rule_id,
            review_status=record.review_status,
        )
        for record in records
    ]


def load_territories(
    session: Session,
    uf: str,
    territory_type: str | None = MUNICIPALITY_TERRITORY_TYPE,
) -> list[Territory]:
    query = territory_query(session, uf, territory_type)
    records = query.all()
    return [
        Territory(
            territory_id=record.territory_id,
            name=record.name,
            territory_type=record.territory_type,
            uf_code=record.uf_code,
            uf_sigla=record.uf_sigla,
            parent_id=record.parent_id,
            geometry=record.geometry,
        )
        for record in records
    ]


def territory_query(
    session: Session,
    uf: str,
    territory_type: str | None = MUNICIPALITY_TERRITORY_TYPE,
) -> Query[TerritoryRecord]:
    scope = normalize_geographic_scope(uf)
    query = session.query(TerritoryRecord)
    if scope != BRAZIL_SCOPE:
        query = query.filter_by(uf_sigla=scope)
    if territory_type is not None:
        query = query.filter_by(territory_type=territory_type)
    return query


def territory_records_for_scope(
    session: Session,
    uf: str,
    territory_type: str | None = MUNICIPALITY_TERRITORY_TYPE,
) -> list[TerritoryRecord]:
    return territory_query(session, uf, territory_type).order_by(TerritoryRecord.name).all()


def normalize_comparison_scope(uf: str, comparison_scope: str | None = None) -> str:
    geographic_scope = normalize_geographic_scope(uf)
    if geographic_scope == BRAZIL_SCOPE:
        return COMPARISON_SCOPE_NATIONAL
    scope = comparison_scope or COMPARISON_SCOPE_UF
    if scope not in COMPARISON_SCOPES:
        raise ValueError(f"unsupported comparison scope: {scope}")
    return scope


def load_local_territories(session: Session) -> list[LocalTerritory]:
    records = session.query(LocalTerritoryRecord).order_by(LocalTerritoryRecord.territory_id).all()
    return [
        LocalTerritory(
            territory_id=record.territory_id,
            name=record.name,
            territory_type=record.territory_type,
            parent_id=record.parent_id,
            uf_code=record.uf_code,
            uf_sigla=record.uf_sigla,
            facility_id=record.facility_id,
            team_id=record.team_id,
        )
        for record in records
    ]


def load_local_teams(session: Session) -> list[LocalTeam]:
    records = session.query(LocalTeamRecord).order_by(LocalTeamRecord.team_id).all()
    return [
        LocalTeam(
            team_id=record.team_id,
            facility_id=record.facility_id,
            name=record.name,
            team_type=record.team_type,
            active=record.active,
        )
        for record in records
    ]


def load_local_tb_cases(session: Session, year: int) -> list[LocalTbCase]:
    records = session.query(LocalTbCaseRecord).filter_by(year=year).all()
    return [
        LocalTbCase(
            local_case_id=record.local_case_id,
            pseudonymized_patient_id=record.pseudonymized_patient_id,
            territory_id=record.territory_id,
            facility_id=record.facility_id,
            team_id=record.team_id,
            year=record.year,
            notification_date=record.notification_date,
            diagnosis_date=record.diagnosis_date,
            treatment_start_date=record.treatment_start_date,
            entry_type=record.entry_type,
            clinical_form=record.clinical_form,
            closure_status=record.closure_status,
            closure_date=record.closure_date,
            rifampicin_resistance=record.rifampicin_resistance,
            retreatment=record.retreatment,
            previous_treatment_failure=record.previous_treatment_failure,
        )
        for record in records
    ]


def load_local_lab_events(session: Session, year: int) -> list[LocalLabEvent]:
    records = session.query(LocalLabEventRecord).filter_by(year=year).all()
    return [
        LocalLabEvent(
            local_lab_id=record.local_lab_id,
            local_case_id=record.local_case_id,
            pseudonymized_patient_id=record.pseudonymized_patient_id,
            test_type=record.test_type,
            year=record.year,
            request_date=record.request_date,
            collection_date=record.collection_date,
            result_date=record.result_date,
            result=record.result,
            status=record.status,
        )
        for record in records
    ]


def load_local_resistance_evidence(session: Session, year: int) -> list[LocalResistanceEvidence]:
    records = session.query(LocalResistanceEvidenceRecord).filter_by(year=year).all()
    return [
        LocalResistanceEvidence(
            resistance_record_id=record.resistance_record_id,
            local_case_id=record.local_case_id,
            pseudonymized_patient_id=record.pseudonymized_patient_id,
            year=record.year,
            recorded_date=record.recorded_date,
            evidence_type=record.evidence_type,
            resistance_scope=record.resistance_scope,
            resistance_status=record.resistance_status,
            record_status=record.record_status,
            source_system=record.source_system,
        )
        for record in records
    ]


def load_medication_dispensings(session: Session, year: int) -> list[MedicationDispensing]:
    records = session.query(MedicationDispensingRecord).filter_by(year=year).all()
    return [
        MedicationDispensing(
            dispensing_id=record.dispensing_id,
            local_case_id=record.local_case_id,
            pseudonymized_patient_id=record.pseudonymized_patient_id,
            dispensing_date=record.dispensing_date,
            days_supplied=record.days_supplied,
            medication_group=record.medication_group,
            year=record.year,
        )
        for record in records
    ]


def load_contact_investigations(session: Session, year: int) -> list[ContactInvestigation]:
    records = session.query(ContactInvestigationRecord).filter_by(year=year).all()
    return [
        ContactInvestigation(
            contact_id=record.contact_id,
            index_case_id=record.index_case_id,
            pseudonymized_contact_id=record.pseudonymized_contact_id,
            identified_date=record.identified_date,
            evaluation_date=record.evaluation_date,
            symptomatic=record.symptomatic,
            tpt_started_date=record.tpt_started_date,
            status=record.status,
            year=record.year,
        )
        for record in records
    ]


def load_resource_inventories(session: Session, year: int) -> list[ResourceInventory]:
    records = session.query(ResourceInventoryRecord).filter_by(year=year).all()
    return [
        ResourceInventory(
            facility_id=record.facility_id,
            year=record.year,
            sputum_collection=record.sputum_collection,
            rapid_molecular_access=record.rapid_molecular_access,
            xray_access=record.xray_access,
            sample_transport=record.sample_transport,
            pharmacy_tb_meds=record.pharmacy_tb_meds,
            chw_count=record.chw_count,
        )
        for record in records
    ]


def load_operational_alerts(session: Session, year: int) -> list[OperationalAlert]:
    records = session.query(OperationalAlertRecord).filter_by(year=year).all()
    return [
        OperationalAlert(
            alert_id=record.alert_id,
            year=record.year,
            alert_type=record.alert_type,
            severity=OperationalAlertSeverity(record.severity),
            status=OperationalAlertStatus(record.status),
            local_case_id=record.local_case_id,
            territory_id=record.territory_id,
            facility_id=record.facility_id,
            team_id=record.team_id,
            related_entity_id=record.related_entity_id,
            reference_date=record.reference_date,
            generated_at=record.generated_at,
            message=record.message,
            due_date=record.due_date,
            signal_kinds=tuple(
                ResistanceSignalKind(value) for value in (record.signal_kinds or [])
            ),
            review_status=record.review_status,
            evidence=tuple(
                operational_alert_evidence_from_payload(item) for item in (record.evidence or [])
            ),
        )
        for record in records
    ]


MAP_LAYER_INDICATOR_IDS = frozenset(
    {
        "tb_incidence_per_100k",
        "tb_mortality_per_100k",
        "cure_proportion",
        "treatment_interruption_proportion",
        "laboratory_confirmation_proportion",
    }
)
SEVERITY_ORDER = {"low": 1, "moderate": 2, "high": 3}
SIH_SOURCE_ID = "sih_sus"
SIH_EXPECTED_MONTHS = tuple(range(1, 13))
CORE_PUBLIC_SOURCE_IDS = (
    "ibge_localidades",
    "ibge_population",
    "sinan_tb",
    "sim",
    "sih_sus",
    "cnes",
)
TERRITORIAL_PUBLIC_SOURCE_IDS = (
    "ibge_localidades",
    "ibge_malhas",
    "ibge_intramunicipal",
    "ibge_population",
    "sinan_tb",
    "sinan_validation",
    "sim",
    "sih_sus",
    "cnes",
    "indicator_validation",
)
REGIONAL_PUBLIC_SOURCE_IDS = frozenset(
    {"ibge_localidades", "ibge_malhas", "ibge_population", "sim", "sih_sus", "cnes"}
)
INHERITABLE_NATIONAL_SOURCE_IDS = frozenset({"sinan_tb"})


def scenario_rule_evaluation_rows(
    session: Session,
    *,
    year: int,
    geographic_scope: str,
    comparison_scope: str,
) -> list[dict[str, Any]]:
    target_scopes = (
        {BRAZIL_SCOPE}
        if comparison_scope == COMPARISON_SCOPE_NATIONAL
        else set(ufs_for_scope(geographic_scope))
    )
    records = (
        session.query(ScenarioRuleEvaluationRecord)
        .filter_by(year=year, comparison_scope=comparison_scope)
        .filter(ScenarioRuleEvaluationRecord.geographic_scope.in_(target_scopes))
        .all()
    )
    rules = {record.rule_id: record for record in session.query(ScenarioRuleRecord).all()}
    return [
        scenario_rule_evaluation_api_row(record, rules.get(record.rule_id))
        for record in sorted(
            records,
            key=lambda item: (item.geographic_scope, item.rule_id),
        )
    ]


def scenario_rule_evaluation_api_row(
    record: ScenarioRuleEvaluationRecord,
    rule: ScenarioRuleRecord | None,
) -> dict[str, Any]:
    return {
        "geographic_scope": record.geographic_scope,
        "year": record.year,
        "comparison_scope": record.comparison_scope,
        "rule_id": record.rule_id,
        "rule_name": rule.name if rule is not None else record.rule_id,
        "indicator_id": rule.indicator_id if rule is not None else None,
        "ranking_dimension": (
            (rule.ranking_dimension or rule.rule_id) if rule is not None else record.rule_id
        ),
        "review_status": rule.review_status if rule is not None else None,
        "status": record.status,
        "available_count": record.available_count,
        "suppressed_count": record.suppressed_count,
        "unavailable_count": record.unavailable_count,
        "territory_count": record.territory_count,
        "coverage_ratio": record.coverage_ratio,
        "threshold_value": record.threshold_value,
        "minimum_count": record.minimum_count,
        "minimum_coverage_ratio": record.minimum_coverage_ratio,
    }


def diagnostic_scenario_rule_readiness(
    evaluations: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    diagnostic_evaluations = [
        row for row in evaluations if row.get("rule_id") in DIAGNOSTIC_SCENARIO_RULE_IDS
    ]
    ready_status = ScenarioEvaluationStatus.READY.value
    insufficient_status = ScenarioEvaluationStatus.INSUFFICIENT_COMPARISON.value
    missing_status = ScenarioEvaluationStatus.MISSING_INDICATOR.value
    ready_count = sum(1 for row in diagnostic_evaluations if row.get("status") == ready_status)
    insufficient_count = sum(
        1 for row in diagnostic_evaluations if row.get("status") == insufficient_status
    )
    missing_count = sum(1 for row in diagnostic_evaluations if row.get("status") == missing_status)
    evaluation_count = len(diagnostic_evaluations)
    if evaluation_count == 0 or missing_count == evaluation_count:
        status = "missing"
    elif ready_count == evaluation_count:
        status = "ready"
    else:
        status = "partial"

    return {
        "label": "Diagnostic coverage prioritization",
        "status": status,
        "ready_count": ready_count,
        "evaluation_count": evaluation_count,
        "insufficient_count": insufficient_count,
        "missing_count": missing_count,
        "detail": (
            f"{ready_count}/{evaluation_count} diagnostic rule evaluations ready; "
            f"{insufficient_count} with insufficient comparison coverage; "
            f"{missing_count} missing indicators"
        ),
    }


def dashboard_context(
    session: Session,
    year: int,
    uf: str,
    comparison_scope: str | None = None,
) -> dict[str, Any]:
    geographic_scope = normalize_geographic_scope(uf)
    scenario_scope = normalize_comparison_scope(geographic_scope, comparison_scope)
    territories = {
        record.territory_id: record
        for record in territory_records_for_scope(session, geographic_scope)
    }
    indicators = [
        record
        for record in session.query(IndicatorValueRecord).filter_by(year=year).all()
        if record.territory_id in territories
    ]
    scenarios = [
        record
        for record in session.query(TerritoryScenarioRecord)
        .filter_by(year=year, comparison_scope=scenario_scope)
        .all()
        if record.territory_id in territories
    ]
    scenario_rule_evaluations = scenario_rule_evaluation_rows(
        session,
        year=year,
        geographic_scope=geographic_scope,
        comparison_scope=scenario_scope,
    )
    source_runs = latest_import_runs_for_scope(
        session, year=year, geographic_scope=geographic_scope
    )
    ranking = ranking_rows(territories, scenarios)
    geometry_count = sum(1 for territory in territories.values() if territory.geometry is not None)
    return {
        "uf": geographic_scope,
        "geographic_scope": geographic_scope,
        "comparison_scope": scenario_scope,
        "year": year,
        "territory_count": len(territories),
        "indicator_count": len(indicators),
        "scenario_count": len(scenarios),
        "scenario_rule_evaluations": scenario_rule_evaluations,
        "readiness": dashboard_readiness(
            territory_count=len(territories),
            geometry_count=geometry_count,
            indicator_count=len(indicators),
            scenarios=scenarios,
            source_runs=source_runs,
            scenario_rule_evaluations=scenario_rule_evaluations,
        ),
        "health_territory_readiness": health_territory_readiness(
            session, geographic_scope, set(territories)
        ),
        "ranking": ranking,
        "sources": source_runs,
        "caveat": (
            "Public aggregate dashboard. Small counts are suppressed and outputs are "
            "decision support for professional review, not diagnosis."
        ),
    }


def api_indicator_rows(session: Session, year: int, uf: str) -> list[dict[str, Any]]:
    territory_by_id = {
        record.territory_id: record for record in territory_records_for_scope(session, uf)
    }
    definitions = {
        record.indicator_id: record for record in session.query(IndicatorDefinitionRecord).all()
    }
    rows: list[dict[str, Any]] = []
    for record in session.query(IndicatorValueRecord).filter_by(year=year).all():
        territory = territory_by_id.get(record.territory_id)
        if territory is None:
            continue
        definition = definitions.get(record.indicator_id)
        rows.append(
            {
                "indicator_id": record.indicator_id,
                "indicator_name": definition.name if definition else record.indicator_id,
                "territory_id": record.territory_id,
                "territory_name": territory.name,
                "year": record.year,
                "value": None if record.is_suppressed else record.value,
                "is_suppressed": record.is_suppressed,
                "numerator_value": record.numerator_value,
                "denominator_value": record.denominator_value,
                "caveats": record.caveats,
                "unit": definition.unit if definition else None,
                "direction": definition.direction if definition else None,
            }
        )
    return rows


def latest_import_runs(session: Session) -> list[dict[str, Any]]:
    source_by_id = {record.source_id: record for record in session.query(DataSourceRecord).all()}
    runs: dict[str, ImportRunRecord] = {}
    for record in session.query(ImportRunRecord).order_by(ImportRunRecord.import_run_id).all():
        runs[record.source_id] = record
    return [
        import_run_api_row(source_id, run, source_by_id) for source_id, run in sorted(runs.items())
    ]


def latest_import_runs_for_scope(
    session: Session,
    *,
    year: int,
    geographic_scope: str,
) -> list[dict[str, Any]]:
    scope = normalize_geographic_scope(geographic_scope)
    source_ids = set(TERRITORIAL_PUBLIC_SOURCE_IDS)
    source_by_id = {record.source_id: record for record in session.query(DataSourceRecord).all()}
    latest_by_source_scope: dict[tuple[str, str], ImportRunRecord] = {}
    records = (
        session.query(ImportRunRecord)
        .filter(
            ImportRunRecord.year == year,
            ImportRunRecord.source_id.in_(source_ids),
            ImportRunRecord.geographic_scope.is_not(None),
        )
        .order_by(ImportRunRecord.import_run_id)
        .all()
    )
    for record in records:
        if record.geographic_scope is not None:
            latest_by_source_scope[(record.source_id, record.geographic_scope)] = record

    rows: list[dict[str, Any]] = []
    for source_id in TERRITORIAL_PUBLIC_SOURCE_IDS:
        row = scoped_import_run_row(source_id, year, scope, latest_by_source_scope, source_by_id)
        if row is not None:
            rows.append(row)
    return rows


def normalized_loaded_months(months: Sequence[int] | None) -> tuple[int, ...] | None:
    if months is None:
        return None
    return tuple(sorted({int(month) for month in months if 1 <= int(month) <= 12}))


def is_complete_sih_run(run: ImportRunRecord) -> bool:
    return (
        run.status == "success"
        and normalized_loaded_months(run.loaded_months) == SIH_EXPECTED_MONTHS
    )


def effective_import_run_status(source_id: str, run: ImportRunRecord) -> str:
    if source_id == SIH_SOURCE_ID and run.status == "success" and not is_complete_sih_run(run):
        return "partial"
    return run.status


def complete_sih_scopes(
    session: Session,
    *,
    year: int,
    geographic_scopes: Iterable[str],
) -> set[str]:
    scopes = {normalize_geographic_scope(scope) for scope in geographic_scopes}
    latest_by_scope: dict[str, ImportRunRecord] = {}
    records = (
        session.query(ImportRunRecord)
        .filter(
            ImportRunRecord.source_id == SIH_SOURCE_ID,
            ImportRunRecord.year == year,
            ImportRunRecord.geographic_scope.in_(scopes),
        )
        .order_by(ImportRunRecord.import_run_id)
        .all()
    )
    for record in records:
        if record.geographic_scope is not None:
            latest_by_scope[record.geographic_scope] = record
    return {scope for scope, run in latest_by_scope.items() if is_complete_sih_run(run)}


def scoped_import_run_row(
    source_id: str,
    year: int,
    geographic_scope: str,
    latest_by_source_scope: dict[tuple[str, str], ImportRunRecord],
    source_by_id: dict[str, DataSourceRecord],
) -> dict[str, Any] | None:
    exact_run = latest_by_source_scope.get((source_id, geographic_scope))
    if geographic_scope != BRAZIL_SCOPE:
        return regional_import_run_row(
            source_id,
            year,
            geographic_scope,
            exact_run,
            latest_by_source_scope,
            source_by_id,
        )

    if source_id not in REGIONAL_PUBLIC_SOURCE_IDS:
        return (
            import_run_api_row(source_id, exact_run, source_by_id)
            if exact_run is not None
            else None
        )

    component_runs = {
        uf: run
        for uf in ufs_for_scope(BRAZIL_SCOPE)
        if (run := latest_by_source_scope.get((source_id, uf))) is not None
    }
    latest_component_id = max((run.import_run_id for run in component_runs.values()), default=-1)
    if exact_run is not None and exact_run.import_run_id > latest_component_id:
        return import_run_api_row(source_id, exact_run, source_by_id)
    if component_runs:
        return national_import_run_row(source_id, year, component_runs, source_by_id)
    if exact_run is not None:
        return import_run_api_row(source_id, exact_run, source_by_id)
    return None


def regional_import_run_row(
    source_id: str,
    year: int,
    geographic_scope: str,
    exact_run: ImportRunRecord | None,
    latest_by_source_scope: dict[tuple[str, str], ImportRunRecord],
    source_by_id: dict[str, DataSourceRecord],
) -> dict[str, Any] | None:
    if exact_run is not None:
        return import_run_api_row(source_id, exact_run, source_by_id)
    if source_id not in INHERITABLE_NATIONAL_SOURCE_IDS:
        return None

    national_run = latest_by_source_scope.get((source_id, BRAZIL_SCOPE))
    if national_run is None:
        return None
    row = import_run_api_row(source_id, national_run, source_by_id, scope_inherited=True)
    row["message"] = (
        f"Brazil-wide source run used for {geographic_scope}/{year}; {national_run.message}"
    )
    return row


def import_run_month_coverage(
    source_id: str,
    run: ImportRunRecord,
) -> dict[str, Any] | None:
    if source_id != SIH_SOURCE_ID:
        return None
    loaded_months = normalized_loaded_months(run.loaded_months)
    missing_months = (
        sorted(set(SIH_EXPECTED_MONTHS) - set(loaded_months)) if loaded_months is not None else None
    )
    complete = is_complete_sih_run(run)
    return {
        "expected_months": list(SIH_EXPECTED_MONTHS),
        "loaded_months": list(loaded_months) if loaded_months is not None else None,
        "missing_months": missing_months,
        "complete": complete,
        "scope_count": 1,
        "complete_scope_count": 1 if complete else 0,
    }


def national_month_coverage(
    source_id: str,
    component_runs: dict[str, ImportRunRecord],
) -> dict[str, Any] | None:
    if source_id != SIH_SOURCE_ID:
        return None
    expected_ufs = ufs_for_scope(BRAZIL_SCOPE)
    loaded_in_every_scope = set(SIH_EXPECTED_MONTHS)
    for uf in expected_ufs:
        run = component_runs.get(uf)
        months = normalized_loaded_months(run.loaded_months) if run is not None else ()
        loaded_in_every_scope.intersection_update(months or ())
    complete_scope_count = sum(
        1
        for uf in expected_ufs
        if (run := component_runs.get(uf)) is not None and is_complete_sih_run(run)
    )
    loaded_months = sorted(loaded_in_every_scope)
    return {
        "expected_months": list(SIH_EXPECTED_MONTHS),
        "loaded_months": loaded_months,
        "missing_months": sorted(set(SIH_EXPECTED_MONTHS) - set(loaded_months)),
        "complete": complete_scope_count == len(expected_ufs),
        "scope_count": len(expected_ufs),
        "complete_scope_count": complete_scope_count,
    }


def national_import_run_row(
    source_id: str,
    year: int,
    component_runs: dict[str, ImportRunRecord],
    source_by_id: dict[str, DataSourceRecord],
) -> dict[str, Any]:
    expected_ufs = ufs_for_scope(BRAZIL_SCOPE)
    component_statuses = {
        uf: effective_import_run_status(source_id, run) for uf, run in component_runs.items()
    }
    success_ufs = sorted(uf for uf, status in component_statuses.items() if status == "success")
    failed_ufs = sorted(uf for uf, status in component_statuses.items() if status == "failed")
    skipped_ufs = sorted(uf for uf, status in component_statuses.items() if status == "skipped")
    other_ufs = sorted(
        uf
        for uf, status in component_statuses.items()
        if status not in {"success", "failed", "skipped"}
    )
    missing_ufs = sorted(set(expected_ufs) - set(component_runs))

    if failed_ufs:
        status = "failed"
    elif len(success_ufs) == len(expected_ufs):
        status = "success"
    elif not success_ufs and len(skipped_ufs) == len(expected_ufs):
        status = "skipped"
    else:
        status = "partial"

    source = source_by_id.get(source_id)
    message = (
        f"national component summary for {year}: {len(success_ufs)} success, "
        f"{len(failed_ufs)} failed, {len(skipped_ufs)} skipped, "
        f"{len(other_ufs)} other, {len(missing_ufs)} missing"
    )
    gaps = [
        f"{label}={','.join(values)}"
        for label, values in (
            ("failed", failed_ufs),
            ("skipped", skipped_ufs),
            ("other", other_ufs),
            ("missing", missing_ufs),
        )
        if values
    ]
    if gaps:
        message = f"{message}; {'; '.join(gaps)}"

    finished_at = max(
        (run.finished_at for run in component_runs.values() if run.finished_at is not None),
        default=None,
    )
    return {
        "source_id": source_id,
        "name": source.name if source is not None else source_id,
        "status": status,
        "row_count": sum(run.row_count for run in component_runs.values()),
        "finished_at": finished_at.isoformat() if finished_at is not None else None,
        "message": message,
        "caveats": source.caveats if source is not None else "",
        "year": year,
        "geographic_scope": BRAZIL_SCOPE,
        "scope_inherited": False,
        "month_coverage": national_month_coverage(source_id, component_runs),
    }


def import_run_api_row(
    source_id: str,
    run: ImportRunRecord,
    source_by_id: dict[str, DataSourceRecord],
    *,
    scope_inherited: bool = False,
) -> dict[str, Any]:
    source = source_by_id.get(source_id)
    return {
        "source_id": source_id,
        "name": source.name if source is not None else source_id,
        "status": effective_import_run_status(source_id, run),
        "row_count": run.row_count,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "message": run.message,
        "caveats": source.caveats if source is not None else "",
        "year": run.year,
        "geographic_scope": run.geographic_scope,
        "scope_inherited": scope_inherited,
        "month_coverage": import_run_month_coverage(source_id, run),
    }


def ranking_rows(
    territories: dict[str, TerritoryRecord],
    scenarios: Iterable[TerritoryScenarioRecord],
) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for scenario in scenarios:
        territory = territories.get(scenario.territory_id)
        if territory is None:
            continue
        row = totals.setdefault(
            scenario.territory_id,
            {
                "territory_id": scenario.territory_id,
                "territory_name": territory.name,
                "score": 0.0,
                "scenario_count": 0,
                "ranking_dimension_count": 0,
                "top_severity": None,
                "scenario_records": [],
                "top_explanations": [],
                "top_scenarios": [],
            },
        )
        row["scenario_count"] = int(row["scenario_count"]) + 1
        row["top_severity"] = highest_severity(
            cast(str | None, row["top_severity"]), scenario.severity
        )
        row["scenario_records"].append(scenario)

    for row in totals.values():
        records = cast(list[TerritoryScenarioRecord], row["scenario_records"])
        score, dimension_count = summarize_dimension_scores(
            (record.ranking_dimension or record.rule_id, record.score) for record in records
        )
        row["score"] = score
        row["ranking_dimension_count"] = dimension_count
        top_scenarios = top_scenario_rows([scenario_api_row(record) for record in records])
        row["top_scenarios"] = top_scenarios
        row["top_explanations"] = [scenario["explanation"] for scenario in top_scenarios]
        del row["scenario_records"]

    return sorted(
        totals.values(),
        key=lambda row: (
            -float(row["score"]),
            -int(row["ranking_dimension_count"]),
            row["territory_name"],
        ),
    )


def api_territory_rows(session: Session, uf: str) -> list[dict[str, Any]]:
    records = territory_records_for_scope(session, uf)
    return [
        {
            "territory_id": record.territory_id,
            "name": record.name,
            "territory_type": record.territory_type,
            "uf_code": record.uf_code,
            "uf_sigla": record.uf_sigla,
            "parent_id": record.parent_id,
        }
        for record in records
    ]


def territory_indicator_history(
    session: Session,
    territory_id: str,
    indicator_id: str,
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    territory = session.get(TerritoryRecord, territory_id)
    if territory is None or territory.territory_type != MUNICIPALITY_TERRITORY_TYPE:
        raise KeyError(f"unknown municipality territory: {territory_id}")
    definition = (
        session.query(IndicatorDefinitionRecord)
        .filter_by(indicator_id=indicator_id)
        .order_by(IndicatorDefinitionRecord.version.desc())
        .first()
    )
    if definition is None:
        raise KeyError(f"unknown indicator: {indicator_id}")

    values = load_indicator_history_values(
        session,
        indicator_id=indicator_id,
        start_year=start_year,
        end_year=end_year,
        territory_ids={territory_id},
    )
    history = build_indicator_history(
        values,
        indicator_id=indicator_id,
        territory_id=territory_id,
        start_year=start_year,
        end_year=end_year,
    )
    return {
        "territory_id": territory.territory_id,
        "territory_name": territory.name,
        "uf": territory.uf_sigla,
        "indicator_id": definition.indicator_id,
        "indicator_name": definition.name,
        "unit": definition.unit,
        "direction": definition.direction,
        "start_year": history.start_year,
        "end_year": history.end_year,
        "coverage": {
            "requested_year_count": history.coverage.requested_year_count,
            "available_year_count": history.coverage.available_year_count,
            "suppressed_year_count": history.coverage.suppressed_year_count,
            "missing_year_count": history.coverage.missing_year_count,
            "provenance_incomplete_year_count": (history.coverage.provenance_incomplete_year_count),
            "status": history.coverage.status.value,
        },
        "comparability_flags": [
            {"code": flag.code, "years": list(flag.years)} for flag in history.flags
        ],
        "points": [
            {
                "year": point.year,
                "status": point.status.value,
                "value": (point.value if point.status == HistoryPointStatus.AVAILABLE else None),
                "numerator_value": (
                    point.numerator_value if point.status == HistoryPointStatus.AVAILABLE else None
                ),
                "denominator_value": point.denominator_value,
                "denominator_year": point.denominator_year,
                "source_provenance": [
                    source_provenance_api_row(source) for source in point.source_provenance
                ],
                "caveats": point.caveats,
            }
            for point in history.points
        ],
    }


def source_provenance_api_row(source: SourceProvenance) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "reference_year": source.reference_year,
        "release_status": source.release_status,
        "dataset_kind": source.dataset_kind,
        "artifact_sha256": source.artifact_sha256,
    }


def optional_incidence_history(
    session: Session, territory_id: str, year: int
) -> dict[str, Any] | None:
    definition_exists = (
        session.query(IndicatorDefinitionRecord.indicator_id)
        .filter_by(indicator_id="tb_incidence_per_100k")
        .first()
        is not None
    )
    if not definition_exists:
        return None
    return territory_indicator_history(
        session, territory_id, "tb_incidence_per_100k", max(2000, year - 5), year
    )


def resistance_surveillance_profile_for_territory(
    session: Session,
    *,
    territory_id: str,
    territory_uf: str,
    year: int,
    comparison_scope: str,
    triggered_rule_ids: set[str],
) -> dict[str, Any]:
    target_scopes = (
        {BRAZIL_SCOPE}
        if comparison_scope == COMPARISON_SCOPE_NATIONAL
        else set(ufs_for_scope(territory_uf))
    )
    evaluation_records = (
        session.query(ScenarioRuleEvaluationRecord)
        .filter_by(year=year, comparison_scope=comparison_scope)
        .filter(ScenarioRuleEvaluationRecord.geographic_scope.in_(target_scopes))
        .all()
    )
    evaluations = [
        ScenarioRuleEvaluation(
            geographic_scope=record.geographic_scope,
            year=record.year,
            comparison_scope=record.comparison_scope,
            rule_id=record.rule_id,
            status=ScenarioEvaluationStatus(record.status),
            available_count=record.available_count,
            suppressed_count=record.suppressed_count,
            unavailable_count=record.unavailable_count,
            territory_count=record.territory_count,
            coverage_ratio=record.coverage_ratio,
            threshold_value=record.threshold_value,
            minimum_count=record.minimum_count,
            minimum_coverage_ratio=record.minimum_coverage_ratio,
        )
        for record in evaluation_records
    ]
    return build_resistance_surveillance_profile(
        load_indicator_values(session, year, [territory_id]),
        evaluations,
        triggered_rule_ids,
        comparison_scope=comparison_scope,
    )


def territory_report(
    session: Session,
    territory_id: str,
    year: int,
    comparison_scope: str | None = None,
) -> dict[str, Any]:
    territory = session.get(TerritoryRecord, territory_id)
    if territory is None or territory.territory_type != MUNICIPALITY_TERRITORY_TYPE:
        raise KeyError(f"unknown municipality territory: {territory_id}")

    scenario_scope = normalize_comparison_scope(territory.uf_sigla, comparison_scope)
    indicators = [
        row
        for row in api_indicator_rows(session, year, territory.uf_sigla)
        if row["territory_id"] == territory_id
    ]
    scenarios = [
        scenario_api_row(record)
        for record in session.query(TerritoryScenarioRecord).filter_by(
            territory_id=territory_id,
            year=year,
            comparison_scope=scenario_scope,
        )
    ]
    recommendations = [
        {
            "strategy_id": record.strategy_id,
            "rule_id": record.rule_id,
            "trigger_rule_ids": record.trigger_rule_ids or [record.rule_id],
            "priority": record.priority,
            "explanation": record.explanation,
            "comparison_scope": record.comparison_scope,
        }
        for record in session.query(RecommendationRecord).filter_by(
            territory_id=territory_id,
            year=year,
            comparison_scope=scenario_scope,
        )
    ]
    return {
        "territory_id": territory.territory_id,
        "territory_name": territory.name,
        "uf": territory.uf_sigla,
        "comparison_scope": scenario_scope,
        "year": year,
        "incidence_history": optional_incidence_history(session, territory_id, year),
        "resistance_surveillance": resistance_surveillance_profile_for_territory(
            session,
            territory_id=territory_id,
            territory_uf=territory.uf_sigla,
            year=year,
            comparison_scope=scenario_scope,
            triggered_rule_ids={str(row["rule_id"]) for row in scenarios},
        ),
        "indicators": indicators,
        "scenarios": scenarios,
        "recommendations": recommendations,
    }


def geojson_for_territories(session: Session, uf: str) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for record in territory_records_for_scope(session, uf):
        if record.geometry is None:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "territory_id": record.territory_id,
                    "name": record.name,
                    "uf": record.uf_sigla,
                },
                "geometry": record.geometry,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def geojson_for_subterritories(
    session: Session,
    parent_id: str,
    territory_type: str = NEIGHBORHOOD_REFERENCE_TERRITORY_TYPE,
) -> dict[str, Any]:
    records = (
        session.query(TerritoryRecord)
        .filter_by(parent_id=parent_id, territory_type=territory_type)
        .order_by(TerritoryRecord.name)
        .all()
    )
    features = [subterritory_feature(record) for record in records]
    return {
        "type": "FeatureCollection",
        "metadata": subterritory_geojson_metadata(parent_id, territory_type, features),
        "features": features,
    }


def subterritory_feature(record: TerritoryRecord) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": {
            "territory_id": record.territory_id,
            "name": record.name,
            "territory_type": record.territory_type,
            "parent_id": record.parent_id,
            "uf": record.uf_sigla,
            "uf_code": record.uf_code,
            "data_level": PUBLIC_REFERENCE_DATA_LEVEL,
        },
        "geometry": record.geometry,
    }


def subterritory_geojson_metadata(
    parent_id: str,
    territory_type: str,
    features: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    drawable_geometry_count = sum(1 for feature in features if feature["geometry"] is not None)
    return {
        "parent_id": parent_id,
        "territory_type": territory_type,
        "feature_count": len(features),
        "drawable_geometry_count": drawable_geometry_count,
        "status": coverage_readiness_status(drawable_geometry_count, len(features)),
        "data_level": PUBLIC_REFERENCE_DATA_LEVEL,
        "caveat": SUBTERRITORY_REFERENCE_CAVEAT,
    }


def map_geojson_for_municipalities(
    session: Session,
    year: int,
    uf: str,
    comparison_scope: str | None = None,
) -> dict[str, Any]:
    geographic_scope = normalize_geographic_scope(uf)
    scenario_scope = normalize_comparison_scope(geographic_scope, comparison_scope)
    territories = territory_records_for_scope(session, geographic_scope)
    territory_ids = {territory.territory_id for territory in territories}
    definitions = {
        record.indicator_id: record for record in session.query(IndicatorDefinitionRecord).all()
    }
    indicators = map_indicator_rows_by_territory(session, year, territory_ids)
    scenarios = map_scenario_summary_by_territory(
        session, year, territory_ids, comparison_scope=scenario_scope
    )
    features = [
        map_municipality_feature(territory, indicators, scenarios) for territory in territories
    ]
    return {
        "type": "FeatureCollection",
        "metadata": map_geojson_metadata(
            geographic_scope, year, features, definitions, comparison_scope=scenario_scope
        ),
        "features": features,
    }


def map_municipality_feature(
    territory: TerritoryRecord,
    indicators: dict[str, dict[str, dict[str, Any]]],
    scenarios: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    territory_indicators = indicators.get(territory.territory_id, {})
    scenario_summary = scenarios.get(territory.territory_id, empty_map_scenario_summary())
    return {
        "type": "Feature",
        "properties": {
            "territory_id": territory.territory_id,
            "name": territory.name,
            "uf": territory.uf_sigla,
            "priority_score": scenario_summary["priority_score"],
            "scenario_count": scenario_summary["scenario_count"],
            "ranking_dimension_count": scenario_summary["ranking_dimension_count"],
            "top_severity": scenario_summary["top_severity"],
            "top_explanations": scenario_summary["top_explanations"],
            "top_scenarios": scenario_summary["top_scenarios"],
            "data_status": map_data_status(territory_indicators),
            "indicators": territory_indicators,
        },
        "geometry": territory.geometry,
    }


def dashboard_readiness(
    *,
    territory_count: int,
    geometry_count: int,
    indicator_count: int,
    scenarios: Sequence[TerritoryScenarioRecord],
    source_runs: Sequence[dict[str, Any]],
    scenario_rule_evaluations: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    source_by_id = {str(row["source_id"]): row for row in source_runs}
    public_source_runs = [source_by_id.get(source_id) for source_id in CORE_PUBLIC_SOURCE_IDS]
    public_success_count = sum(
        1 for row in public_source_runs if row is not None and row["status"] == "success"
    )
    public_failed_count = sum(
        1 for row in public_source_runs if row is not None and row["status"] == "failed"
    )
    validation_run = source_by_id.get("indicator_validation")
    hospitalization_run = source_by_id.get(SIH_SOURCE_ID)
    scenario_territory_count = len({scenario.territory_id for scenario in scenarios})
    warning_count = validation_warning_count(validation_run)
    diagnostic_readiness = diagnostic_scenario_rule_readiness(scenario_rule_evaluations)

    return {
        "public_sources": {
            "label": "Public sources",
            "status": public_sources_readiness_status(
                success_count=public_success_count,
                failed_count=public_failed_count,
            ),
            "success_count": public_success_count,
            "expected_count": len(CORE_PUBLIC_SOURCE_IDS),
            "detail": (
                f"{public_success_count}/{len(CORE_PUBLIC_SOURCE_IDS)} core public "
                "source runs successful"
            ),
        },
        "hospitalization_coverage": hospitalization_coverage_readiness(hospitalization_run),
        "geometry": {
            "label": "Geometry",
            "status": coverage_readiness_status(geometry_count, territory_count),
            "geometry_count": geometry_count,
            "territory_count": territory_count,
            "detail": f"{geometry_count}/{territory_count} municipalities with geometry",
        },
        "indicator_validation": {
            "label": "Indicator validation",
            "status": validation_readiness_status(validation_run),
            "source_status": validation_run["status"] if validation_run is not None else "missing",
            "warning_count": warning_count,
            "indicator_count": indicator_count,
            "detail": indicator_validation_detail(validation_run, warning_count),
        },
        "diagnostic_scenario_rules": diagnostic_readiness,
        "generated_scenarios": {
            "label": "Generated scenarios",
            "status": "ready" if scenarios else "missing",
            "scenario_count": len(scenarios),
            "territory_count": scenario_territory_count,
            "detail": f"{len(scenarios)} scenarios in {scenario_territory_count} territories",
        },
    }


def health_territory_readiness(
    session: Session,
    uf: str,
    municipality_ids: set[str],
) -> dict[str, Any]:
    subterritories = territory_query(session, uf, NEIGHBORHOOD_REFERENCE_TERRITORY_TYPE).all()
    public_geometry_count = sum(1 for territory in subterritories if territory.geometry is not None)
    facilities = (
        session.query(FacilityRecord)
        .filter(FacilityRecord.territory_id.in_(municipality_ids))
        .all()
        if municipality_ids
        else []
    )
    facility_municipality_count = len({facility.territory_id for facility in facilities})

    return {
        "public_subterritory_geometry": {
            "label": "Public submunicipal reference geometry",
            "status": coverage_readiness_status(public_geometry_count, len(subterritories)),
            "feature_count": len(subterritories),
            "drawable_geometry_count": public_geometry_count,
            "detail": (
                f"{public_geometry_count}/{len(subterritories)} public reference polygons "
                "available for contextual drill-down"
            ),
        },
        "cnes_facility_context": {
            "label": "CNES facility context",
            "status": "ready" if facilities else "missing",
            "facility_count": len(facilities),
            "municipality_count": facility_municipality_count,
            "detail": (
                f"{len(facilities)} public CNES facility records in "
                f"{facility_municipality_count} municipalities"
            ),
        },
        "official_health_territory_boundaries": {
            "label": "Official health-territory boundaries",
            "status": "missing",
            "available": False,
            "detail": (
                "Official UBS, team, and microarea boundaries are not available from "
                "the current public-only sources."
            ),
        },
        "tb_health_territory_indicators": {
            "label": "TB indicators by health territory",
            "status": "missing",
            "available": False,
            "detail": (
                "TB outcomes by UBS, team, microarea, or bairro are not computed in MVP1; "
                "public TB indicators remain municipality-level."
            ),
        },
    }


def hospitalization_coverage_status(source_status: str, complete: bool) -> str:
    if source_status == "failed":
        return "warning"
    if complete:
        return "ready"
    if source_status == "skipped":
        return "missing"
    return "partial"


def hospitalization_coverage_detail(coverage: dict[str, Any]) -> str:
    scope_count = int(coverage.get("scope_count", 1))
    complete_scope_count = int(coverage.get("complete_scope_count", 0))
    loaded_months = coverage.get("loaded_months")
    if scope_count > 1:
        return f"{complete_scope_count}/{scope_count} UFs with complete 12-month SIH/SUS coverage"
    if loaded_months is None:
        return "SIH/SUS monthly coverage is unknown; annual indicators are excluded"

    missing_months = coverage.get("missing_months") or []
    detail = f"{len(loaded_months)}/12 SIH/SUS months loaded"
    if not missing_months:
        return detail
    missing_text = ",".join(f"{int(month):02d}" for month in missing_months)
    return f"{detail}; missing {missing_text}"


def hospitalization_coverage_readiness(
    source_run: dict[str, Any] | None,
) -> dict[str, Any]:
    label = "Annual SIH/SUS coverage"
    if source_run is None:
        return {
            "label": label,
            "status": "missing",
            "complete": False,
            "detail": "No scoped SIH/SUS import run recorded",
        }

    coverage = source_run.get("month_coverage")
    if not isinstance(coverage, dict):
        return {
            "label": label,
            "status": "partial",
            "complete": False,
            "detail": "SIH/SUS monthly coverage was not recorded",
        }

    complete = bool(coverage.get("complete"))
    return {
        "label": label,
        "status": hospitalization_coverage_status(
            str(source_run.get("status", "missing")), complete
        ),
        "complete": complete,
        "detail": hospitalization_coverage_detail(coverage),
    }


def public_sources_readiness_status(*, success_count: int, failed_count: int) -> str:
    if failed_count:
        return "warning"
    if success_count == len(CORE_PUBLIC_SOURCE_IDS):
        return "ready"
    if success_count:
        return "partial"
    return "missing"


def coverage_readiness_status(covered_count: int, total_count: int) -> str:
    if total_count == 0:
        return "missing"
    if covered_count == total_count:
        return "ready"
    if covered_count:
        return "partial"
    return "missing"


def validation_readiness_status(validation_run: dict[str, Any] | None) -> str:
    if validation_run is None:
        return "missing"
    if validation_run["status"] == "success":
        return "ready"
    if validation_run["status"] == "failed":
        return "warning"
    return "partial"


def indicator_validation_detail(
    validation_run: dict[str, Any] | None,
    warning_count: int,
) -> str:
    if validation_run is None:
        return "No validation run recorded"
    if warning_count:
        return f"{validation_run['status']} with {warning_count} warning(s)"
    return str(validation_run["status"])


def validation_warning_count(validation_run: dict[str, Any] | None) -> int:
    if validation_run is None:
        return 0
    match = re.search(r"(\d+) warning\(s\) found", str(validation_run.get("message", "")))
    return int(match.group(1)) if match else 0


def map_indicator_rows_by_territory(
    session: Session,
    year: int,
    territory_ids: set[str],
) -> dict[str, dict[str, dict[str, Any]]]:
    definitions = {
        record.indicator_id: record for record in session.query(IndicatorDefinitionRecord).all()
    }
    indicators: dict[str, dict[str, dict[str, Any]]] = {}
    records = session.query(IndicatorValueRecord).filter_by(year=year).all()
    for record in records:
        if record.territory_id not in territory_ids:
            continue
        definition = definitions.get(record.indicator_id)
        territory_indicators = indicators.setdefault(record.territory_id, {})
        territory_indicators[record.indicator_id] = {
            "name": definition.name if definition is not None else record.indicator_id,
            "value": None if record.is_suppressed else record.value,
            "is_suppressed": record.is_suppressed,
            "unit": definition.unit if definition is not None else None,
            "direction": definition.direction if definition is not None else None,
        }
    return indicators


def map_scenario_summary_by_territory(
    session: Session,
    year: int,
    territory_ids: set[str],
    comparison_scope: str = COMPARISON_SCOPE_UF,
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    records = (
        session.query(TerritoryScenarioRecord)
        .filter_by(year=year, comparison_scope=comparison_scope)
        .all()
    )
    for record in records:
        if record.territory_id not in territory_ids:
            continue
        summary = summaries.setdefault(record.territory_id, empty_map_scenario_summary())
        summary["scenario_count"] = int(summary["scenario_count"]) + 1
        summary["top_severity"] = highest_severity(
            cast(str | None, summary["top_severity"]), record.severity
        )
        summary["scenario_records"].append(record)

    for summary in summaries.values():
        scenario_records = cast(
            list[TerritoryScenarioRecord],
            summary["scenario_records"],
        )
        score, dimension_count = summarize_dimension_scores(
            (record.ranking_dimension or record.rule_id, record.score)
            for record in scenario_records
        )
        summary["priority_score"] = score
        summary["ranking_dimension_count"] = dimension_count
        top_scenarios = top_scenario_rows([scenario_api_row(record) for record in scenario_records])
        summary["top_scenarios"] = top_scenarios
        summary["top_explanations"] = [scenario["explanation"] for scenario in top_scenarios]
        del summary["scenario_records"]
    return summaries


def empty_map_scenario_summary() -> dict[str, Any]:
    return {
        "priority_score": 0.0,
        "scenario_count": 0,
        "ranking_dimension_count": 0,
        "top_severity": None,
        "top_scenarios": [],
        "top_explanations": [],
        "scenario_records": [],
    }


def highest_severity(current: str | None, candidate: str) -> str:
    if current is None:
        return candidate
    if SEVERITY_ORDER.get(candidate, 0) > SEVERITY_ORDER.get(current, 0):
        return candidate
    return current


def scenario_api_row(record: TerritoryScenarioRecord) -> dict[str, Any]:
    return {
        "rule_id": record.rule_id,
        "ranking_dimension": record.ranking_dimension or record.rule_id,
        "review_status": record.review_status,
        "comparison_scope": record.comparison_scope,
        "indicator_id": record.indicator_id,
        "severity": record.severity,
        "score": round(record.score, 4),
        "explanation": record.explanation,
        "indicator_value": record.indicator_value,
        "threshold_value": record.threshold_value,
    }


def top_scenario_rows(scenarios: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        scenarios,
        key=lambda row: (
            -float(row["score"]),
            -SEVERITY_ORDER.get(str(row["severity"]), 0),
            str(row["rule_id"]),
        ),
    )[:3]


def map_geojson_metadata(
    uf: str,
    year: int,
    features: Sequence[dict[str, Any]],
    definitions: dict[str, IndicatorDefinitionRecord],
    *,
    comparison_scope: str,
) -> dict[str, Any]:
    return {
        "uf": uf,
        "geographic_scope": uf,
        "comparison_scope": comparison_scope,
        "year": year,
        "feature_count": len(features),
        "drawable_geometry_count": sum(
            1 for feature in features if feature["geometry"] is not None
        ),
        "layers": map_layer_definitions(definitions),
    }


def map_layer_definitions(
    definitions: dict[str, IndicatorDefinitionRecord],
) -> dict[str, dict[str, str | None]]:
    layers: dict[str, dict[str, str | None]] = {
        "priority_score": {
            "label": "Priority score",
            "kind": "property",
            "unit": "score",
            "direction": IndicatorDirection.HIGH_BAD.value,
        },
        "scenario_count": {
            "label": "Scenario count",
            "kind": "property",
            "unit": IndicatorUnit.COUNT.value,
            "direction": IndicatorDirection.HIGH_BAD.value,
        },
    }
    for indicator_id in sorted(MAP_LAYER_INDICATOR_IDS):
        definition = definitions.get(indicator_id)
        layers[indicator_id] = {
            "label": definition.name if definition is not None else indicator_id,
            "kind": "indicator",
            "unit": definition.unit if definition is not None else None,
            "direction": definition.direction if definition is not None else None,
        }
    return layers


def map_data_status(indicators: dict[str, dict[str, Any]]) -> str:
    required = {
        indicator_id: indicators.get(indicator_id) for indicator_id in MAP_LAYER_INDICATOR_IDS
    }
    if all(value is None for value in required.values()):
        return "missing"
    if all(value is not None and not value["is_suppressed"] for value in required.values()):
        return "complete"
    return "partial"


def mvp2_alert_rows(
    session: Session,
    year: int,
    *,
    alert_type: str | None = None,
    severity: str | None = None,
    signal_kind: str | None = None,
    facility_id: str | None = None,
    team_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    teams = {record.team_id: record for record in session.query(LocalTeamRecord).all()}
    records = filtered_operational_alert_records(
        session,
        year,
        alert_type=alert_type,
        signal_kind=signal_kind,
        severity=severity,
        facility_id=facility_id,
        team_id=team_id,
        status=status,
    )
    return [operational_alert_row(record, teams.get(record.team_id)) for record in records]


def filtered_operational_alert_records(
    session: Session,
    year: int,
    *,
    alert_type: str | None,
    signal_kind: str | None,
    severity: str | None,
    facility_id: str | None,
    team_id: str | None,
    status: str | None,
) -> list[OperationalAlertRecord]:
    records = (
        session.query(OperationalAlertRecord)
        .filter_by(year=year)
        .order_by(
            OperationalAlertRecord.facility_id,
            OperationalAlertRecord.team_id,
            OperationalAlertRecord.alert_type,
            OperationalAlertRecord.local_case_id,
        )
        .all()
    )
    return [
        record
        for record in records
        if matches_optional(record.alert_type, alert_type)
        and (signal_kind is None or signal_kind in (record.signal_kinds or []))
        and matches_optional(record.severity, severity)
        and matches_optional(record.facility_id, facility_id)
        and matches_optional(record.team_id, team_id)
        and matches_optional(record.status, status)
    ]


def operational_alert_row(
    record: OperationalAlertRecord, team: LocalTeamRecord | None
) -> dict[str, Any]:
    return {
        "alert_id": record.alert_id,
        "year": record.year,
        "alert_type": record.alert_type,
        "severity": record.severity,
        "status": record.status,
        "local_case_id": record.local_case_id,
        "territory_id": record.territory_id,
        "facility_id": record.facility_id,
        "team_id": record.team_id,
        "team_name": team.name if team is not None else record.team_id,
        "related_entity_id": record.related_entity_id,
        "reference_date": record.reference_date.isoformat(),
        "generated_at": record.generated_at.isoformat(),
        "due_date": record.due_date.isoformat() if record.due_date else None,
        "message": record.message,
        "signal_kinds": record.signal_kinds or [],
        "review_status": record.review_status,
        "evidence": record.evidence or [],
    }


def mvp2_alert_detail(session: Session, alert_id: str) -> dict[str, Any] | None:
    record = session.get(OperationalAlertRecord, alert_id)
    if record is None:
        return None
    team = session.get(LocalTeamRecord, record.team_id)
    return operational_alert_row(record, team)


def mvp2_summary(session: Session, year: int) -> dict[str, Any]:
    alerts = mvp2_alert_rows(session, year)
    return {
        "year": year,
        "case_count": session.query(LocalTbCaseRecord).filter_by(year=year).count(),
        "alert_count": len(alerts),
        "open_alert_count": sum(1 for row in alerts if row["status"] == "open"),
        "by_type": count_rows(alerts, "alert_type"),
        "by_severity": count_rows(alerts, "severity"),
        "by_status": count_rows(alerts, "status"),
        "by_signal_kind": count_list_values(alerts, "signal_kinds", "signal_kind"),
        "by_facility_team": facility_team_summary_rows(alerts),
    }


def mvp2_dashboard_context(
    session: Session,
    year: int,
    *,
    alert_type: str | None = None,
    severity: str | None = None,
    signal_kind: str | None = None,
    facility_id: str | None = None,
    team_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    alerts = mvp2_alert_rows(
        session,
        year,
        alert_type=alert_type,
        severity=severity,
        facility_id=facility_id,
        signal_kind=signal_kind,
        team_id=team_id,
        status=status,
    )
    all_alerts = mvp2_alert_rows(session, year)
    return {
        "year": year,
        "alerts": alerts,
        "summary": mvp2_summary(session, year),
        "filters": {
            "alert_type": alert_type or "",
            "severity": severity or "",
            "signal_kind": signal_kind or "",
            "facility_id": facility_id or "",
            "team_id": team_id or "",
            "status": status or "",
        },
        "filter_options": mvp2_filter_options(all_alerts),
        "caveat": (
            "Synthetic/pseudonymized operational pilot. Alerts are transparent review queues "
            "and do not diagnose, prescribe, or replace professional judgment."
        ),
    }


def mvp2_filter_options(alerts: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "alert_types": unique_filter_values(alerts, "alert_type"),
        "signal_kinds": unique_list_filter_values(alerts, "signal_kinds"),
        "severities": unique_filter_values(alerts, "severity"),
        "facilities": unique_filter_values(alerts, "facility_id"),
        "teams": unique_filter_values(alerts, "team_id"),
        "statuses": unique_filter_values(alerts, "status"),
    }


def count_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row[key])
        counts[value] = counts.get(value, 0) + 1
    return [{key: value, "count": count} for value, count in sorted(counts.items())]


def unique_list_filter_values(rows: list[dict[str, Any]], key: str) -> list[str]:
    values: set[str] = set()
    for row in rows:
        row_values = row.get(key, [])
        if isinstance(row_values, list):
            values.update(str(value) for value in row_values)
    return sorted(values)


def count_list_values(
    rows: list[dict[str, Any]], key: str, output_key: str
) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        values = row.get(key, [])
        if not isinstance(values, list):
            continue
        for value in values:
            normalized = str(value)
            counts[normalized] = counts.get(normalized, 0) + 1
    return [{output_key: value, "count": count} for value, count in sorted(counts.items())]


def facility_team_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["facility_id"]), str(row["team_id"]))
        item = summary.setdefault(
            key,
            {
                "facility_id": row["facility_id"],
                "team_id": row["team_id"],
                "team_name": row["team_name"],
                "alert_count": 0,
                "high": 0,
                "moderate": 0,
                "open": 0,
            },
        )
        item["alert_count"] = int(item["alert_count"]) + 1
        if row["severity"] in {"high", "moderate"}:
            item[str(row["severity"])] = int(item[str(row["severity"])]) + 1
        if row["status"] == "open":
            item["open"] = int(item["open"]) + 1
    return sorted(summary.values(), key=lambda item: (-int(item["alert_count"]), item["team_id"]))


def unique_filter_values(rows: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({str(row[key]) for row in rows if row.get(key)})


def matches_optional(value: str, expected: str | None) -> bool:
    return expected in (None, "") or value == expected


def hydrate_indicator_definition(record: IndicatorDefinitionRecord) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_id=record.indicator_id,
        name=record.name,
        unit=IndicatorUnit(record.unit),
        direction=IndicatorDirection(record.direction),
        public_data_status=PublicDataStatus(record.public_data_status),
        numerator=record.numerator,
        denominator=record.denominator,
        sources=tuple(record.sources),
        caveats=record.caveats,
        version=record.version,
        minimum_count=record.minimum_count,
    )
