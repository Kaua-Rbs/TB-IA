from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine, delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from tbia.domain.models import (
    CaseAggregate,
    DataSource,
    Facility,
    HospitalizationAggregate,
    ImportRun,
    IndicatorDefinition,
    IndicatorDirection,
    IndicatorUnit,
    IndicatorValue,
    MortalityAggregate,
    PopulationDenominator,
    PublicDataStatus,
    Recommendation,
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
    for aggregate in aggregates:
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
    for mortality in mortalities:
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
    for hospitalization in hospitalizations:
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
