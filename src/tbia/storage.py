from __future__ import annotations

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
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

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
    LocalTbCase,
    LocalTeam,
    LocalTerritory,
    MedicationDispensing,
    MortalityAggregate,
    OperationalAlert,
    OperationalAlertSeverity,
    OperationalAlertStatus,
    PopulationDenominator,
    PublicDataStatus,
    Recommendation,
    ResourceInventory,
    ScenarioRule,
    ScenarioSeverity,
    Strategy,
    Territory,
    TerritoryScenario,
)


class Base(DeclarativeBase):
    pass


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


class TerritoryScenarioRecord(Base):
    __tablename__ = "territory_scenarios"

    territory_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(40))
    score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    indicator_id: Mapped[str] = mapped_column(String(120))
    indicator_value: Mapped[float] = mapped_column(Float)
    threshold_value: Mapped[float] = mapped_column(Float)


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
    strategy_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    priority: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text)


def create_engine_for_url(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)


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
            )
        )


def save_case_aggregates(session: Session, aggregates: Iterable[CaseAggregate]) -> None:
    rows = list(aggregates)
    if not rows:
        return
    years = {aggregate.year for aggregate in rows}
    session.execute(delete(CaseAggregateRecord).where(CaseAggregateRecord.year.in_(years)))
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


def save_mortalities(session: Session, mortalities: Iterable[MortalityAggregate]) -> None:
    rows = list(mortalities)
    if not rows:
        return
    years = {mortality.year for mortality in rows}
    session.execute(
        delete(MortalityAggregateRecord).where(MortalityAggregateRecord.year.in_(years))
    )
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
) -> None:
    rows = list(hospitalizations)
    if not rows:
        return
    years = {hospitalization.year for hospitalization in rows}
    session.execute(
        delete(HospitalizationAggregateRecord).where(HospitalizationAggregateRecord.year.in_(years))
    )
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


def save_indicator_values(session: Session, values: Iterable[IndicatorValue], year: int) -> None:
    session.execute(delete(IndicatorValueRecord).where(IndicatorValueRecord.year == year))
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
            )
        )


def save_territory_scenarios(
    session: Session,
    scenarios: Iterable[TerritoryScenario],
    year: int,
) -> None:
    session.execute(delete(TerritoryScenarioRecord).where(TerritoryScenarioRecord.year == year))
    for scenario in scenarios:
        session.merge(
            TerritoryScenarioRecord(
                territory_id=scenario.territory_id,
                year=scenario.year,
                rule_id=scenario.rule_id,
                scenario_id=scenario.scenario_id,
                severity=scenario.severity.value,
                score=scenario.score,
                explanation=scenario.explanation,
                indicator_id=scenario.indicator_id,
                indicator_value=scenario.indicator_value,
                threshold_value=scenario.threshold_value,
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
) -> None:
    session.execute(delete(RecommendationRecord).where(RecommendationRecord.year == year))
    for recommendation in recommendations:
        session.merge(
            RecommendationRecord(
                territory_id=recommendation.territory_id,
                year=recommendation.year,
                strategy_id=recommendation.strategy_id,
                rule_id=recommendation.rule_id,
                priority=recommendation.priority.value,
                explanation=recommendation.explanation,
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


def load_indicator_values(session: Session, year: int) -> list[IndicatorValue]:
    records = session.query(IndicatorValueRecord).filter_by(year=year).all()
    return [
        IndicatorValue(
            indicator_id=record.indicator_id,
            territory_id=record.territory_id,
            year=record.year,
            value=record.value,
            numerator_value=record.numerator_value,
            denominator_value=record.denominator_value,
            is_suppressed=record.is_suppressed,
            source_ids=tuple(record.source_ids),
            caveats=record.caveats,
            computed_at=record.computed_at,
        )
        for record in records
    ]


def load_territory_scenarios(session: Session, year: int) -> list[TerritoryScenario]:
    records = session.query(TerritoryScenarioRecord).filter_by(year=year).all()
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
        )
        for record in records
    ]


def load_territories(session: Session, uf: str) -> list[Territory]:
    records = session.query(TerritoryRecord).filter_by(uf_sigla=uf).all()
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


def dashboard_context(session: Session, year: int, uf: str) -> dict[str, Any]:
    territories = {
        record.territory_id: record
        for record in session.query(TerritoryRecord).filter_by(uf_sigla=uf).all()
    }
    indicators = [
        record
        for record in session.query(IndicatorValueRecord).filter_by(year=year).all()
        if record.territory_id in territories
    ]
    scenarios = [
        record
        for record in session.query(TerritoryScenarioRecord).filter_by(year=year).all()
        if record.territory_id in territories
    ]
    source_runs = latest_import_runs(session)
    ranking = ranking_rows(territories, scenarios)
    return {
        "uf": uf,
        "year": year,
        "territory_count": len(territories),
        "indicator_count": len(indicators),
        "scenario_count": len(scenarios),
        "ranking": ranking,
        "sources": source_runs,
        "caveat": (
            "Public aggregate dashboard. Small counts are suppressed and outputs are "
            "decision support for professional review, not diagnosis."
        ),
    }


def api_indicator_rows(session: Session, year: int, uf: str) -> list[dict[str, Any]]:
    territory_by_id = {
        record.territory_id: record
        for record in session.query(TerritoryRecord).filter_by(uf_sigla=uf).all()
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
        {
            "source_id": source_id,
            "name": source_by_id[source_id].name if source_id in source_by_id else source_id,
            "status": run.status,
            "row_count": run.row_count,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "message": run.message,
            "caveats": source_by_id[source_id].caveats if source_id in source_by_id else "",
        }
        for source_id, run in sorted(runs.items())
    ]


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
                "top_explanations": [],
            },
        )
        row["score"] = round(float(row["score"]) + scenario.score, 4)
        row["scenario_count"] = int(row["scenario_count"]) + 1
        row["top_explanations"].append(scenario.explanation)

    return sorted(
        totals.values(),
        key=lambda row: (-float(row["score"]), -int(row["scenario_count"]), row["territory_name"]),
    )


def api_territory_rows(session: Session, uf: str) -> list[dict[str, Any]]:
    records = (
        session.query(TerritoryRecord).filter_by(uf_sigla=uf).order_by(TerritoryRecord.name).all()
    )
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


def territory_report(session: Session, territory_id: str, year: int) -> dict[str, Any]:
    territory = session.get(TerritoryRecord, territory_id)
    if territory is None:
        raise KeyError(f"unknown territory: {territory_id}")

    indicators = [
        row
        for row in api_indicator_rows(session, year, territory.uf_sigla)
        if row["territory_id"] == territory_id
    ]
    scenarios = [
        {
            "rule_id": record.rule_id,
            "severity": record.severity,
            "score": record.score,
            "explanation": record.explanation,
            "indicator_id": record.indicator_id,
            "indicator_value": record.indicator_value,
            "threshold_value": record.threshold_value,
        }
        for record in session.query(TerritoryScenarioRecord).filter_by(
            territory_id=territory_id,
            year=year,
        )
    ]
    recommendations = [
        {
            "strategy_id": record.strategy_id,
            "rule_id": record.rule_id,
            "priority": record.priority,
            "explanation": record.explanation,
        }
        for record in session.query(RecommendationRecord).filter_by(
            territory_id=territory_id,
            year=year,
        )
    ]
    return {
        "territory_id": territory.territory_id,
        "territory_name": territory.name,
        "uf": territory.uf_sigla,
        "year": year,
        "indicators": indicators,
        "scenarios": scenarios,
        "recommendations": recommendations,
    }


def geojson_for_territories(session: Session, uf: str) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for record in session.query(TerritoryRecord).filter_by(uf_sigla=uf).all():
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


def map_geojson_for_municipalities(session: Session, year: int, uf: str) -> dict[str, Any]:
    territories = (
        session.query(TerritoryRecord).filter_by(uf_sigla=uf).order_by(TerritoryRecord.name).all()
    )
    territory_ids = {territory.territory_id for territory in territories}
    definitions = {
        record.indicator_id: record for record in session.query(IndicatorDefinitionRecord).all()
    }
    indicators = map_indicator_rows_by_territory(session, year, territory_ids)
    scenarios = map_scenario_summary_by_territory(session, year, territory_ids)
    features = [
        map_municipality_feature(territory, indicators, scenarios) for territory in territories
    ]
    return {
        "type": "FeatureCollection",
        "metadata": map_geojson_metadata(uf, year, features, definitions),
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
            "top_severity": scenario_summary["top_severity"],
            "top_explanations": scenario_summary["top_explanations"],
            "data_status": map_data_status(territory_indicators),
            "indicators": territory_indicators,
        },
        "geometry": territory.geometry,
    }


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
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    records = session.query(TerritoryScenarioRecord).filter_by(year=year).all()
    for record in records:
        if record.territory_id not in territory_ids:
            continue
        summary = summaries.setdefault(record.territory_id, empty_map_scenario_summary())
        summary["priority_score"] = round(float(summary["priority_score"]) + record.score, 4)
        summary["scenario_count"] = int(summary["scenario_count"]) + 1
        summary["top_severity"] = highest_severity(
            cast(str | None, summary["top_severity"]), record.severity
        )
        summary["scored_explanations"].append((record.score, record.explanation))

    for summary in summaries.values():
        summary["top_explanations"] = top_explanations(summary["scored_explanations"])
        del summary["scored_explanations"]
    return summaries


def empty_map_scenario_summary() -> dict[str, Any]:
    return {
        "priority_score": 0.0,
        "scenario_count": 0,
        "top_severity": None,
        "top_explanations": [],
        "scored_explanations": [],
    }


def highest_severity(current: str | None, candidate: str) -> str:
    if current is None:
        return candidate
    if SEVERITY_ORDER.get(candidate, 0) > SEVERITY_ORDER.get(current, 0):
        return candidate
    return current


def top_explanations(scored_explanations: list[tuple[float, str]]) -> list[str]:
    return [
        explanation
        for _, explanation in sorted(scored_explanations, key=lambda item: (-item[0], item[1]))[:3]
    ]


def map_geojson_metadata(
    uf: str,
    year: int,
    features: Sequence[dict[str, Any]],
    definitions: dict[str, IndicatorDefinitionRecord],
) -> dict[str, Any]:
    return {
        "uf": uf,
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
    facility_id: str | None = None,
    team_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    teams = {record.team_id: record for record in session.query(LocalTeamRecord).all()}
    records = filtered_operational_alert_records(
        session,
        year,
        alert_type=alert_type,
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
        "by_facility_team": facility_team_summary_rows(alerts),
    }


def mvp2_dashboard_context(
    session: Session,
    year: int,
    *,
    alert_type: str | None = None,
    severity: str | None = None,
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
