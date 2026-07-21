from __future__ import annotations

from collections.abc import Iterable

from tbia.domain.models import (
    CaseAggregate,
    HospitalizationAggregate,
    IndicatorDefinition,
    IndicatorDirection,
    IndicatorUnit,
    IndicatorValue,
    MortalityAggregate,
    PopulationDenominator,
    PublicDataStatus,
    SourceProvenance,
)

INDICATOR_DEFINITIONS: tuple[IndicatorDefinition, ...] = (
    IndicatorDefinition(
        indicator_id="tb_incidence_per_100k",
        name="TB incidence",
        unit=IndicatorUnit.PER_100K,
        direction=IndicatorDirection.HIGH_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="New TB cases in the period",
        denominator="Population denominator",
        sources=("sinan_tb", "ibge_population"),
        caveats="Uses residence territory and official new-case entry type mapping.",
    ),
    IndicatorDefinition(
        indicator_id="tb_mortality_per_100k",
        name="TB mortality",
        unit=IndicatorUnit.PER_100K,
        direction=IndicatorDirection.HIGH_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="Deaths with underlying cause CID-10 A15-A19",
        denominator="Population denominator",
        sources=("sim", "ibge_population"),
        caveats="Uses residence territory unless a different analysis is configured.",
    ),
    IndicatorDefinition(
        indicator_id="cure_proportion",
        name="Cure proportion",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.LOW_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="Cases closed as cure",
        denominator="Cases with closure status",
        sources=("sinan_tb",),
        caveats="Depends on official closure-status mapping and cohort-period definition.",
    ),
    IndicatorDefinition(
        indicator_id="treatment_interruption_proportion",
        name="Treatment interruption proportion",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.HIGH_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="Cases closed as treatment interruption",
        denominator="Cases with closure status",
        sources=("sinan_tb",),
        caveats="Uses the current Brazilian terminology for abandonment/interruption.",
    ),
    IndicatorDefinition(
        indicator_id="retreatment_proportion",
        name="Retreatment proportion",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.HIGH_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="Recurrence and re-entry after abandonment cases",
        denominator="Notified TB cases",
        sources=("sinan_tb",),
        caveats="Requires official entry-type category mapping.",
    ),
    IndicatorDefinition(
        indicator_id="laboratory_confirmation_proportion",
        name="Laboratory confirmation proportion",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.LOW_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE_WITH_TRANSFORMATION,
        numerator="New pulmonary TB cases confirmed by smear, rapid molecular test, or culture",
        denominator="New pulmonary TB cases",
        sources=("sinan_tb",),
        caveats="DBC-derived transformations should avoid double counting lab confirmation fields.",
    ),
    IndicatorDefinition(
        indicator_id="hiv_testing_proportion",
        name="HIV testing proportion",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.LOW_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="New TB cases tested for HIV",
        denominator="New TB cases",
        sources=("sinan_tb",),
        caveats="Requires mapping positive, negative, in-progress, and not-performed categories.",
    ),
    IndicatorDefinition(
        indicator_id="tb_hiv_burden_proportion",
        name="TB-HIV burden",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.HIGH_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="New TB cases with positive HIV result",
        denominator="New TB cases",
        sources=("sinan_tb",),
        caveats=(
            "Uses HIV-positive result among the new-case universe; "
            "AIDS comorbidity is audited separately."
        ),
    ),
    IndicatorDefinition(
        indicator_id="trm_tb_use_proportion",
        name="TRM-TB use proportion",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.LOW_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="New pulmonary TB cases with rapid molecular test",
        denominator="New pulmonary TB cases",
        sources=("sinan_tb",),
        caveats="Requires rapid molecular test field mapping and non-applicable exclusions.",
    ),
    IndicatorDefinition(
        indicator_id="culture_use_among_retreatment",
        name="Culture use among retreatment",
        unit=IndicatorUnit.PERCENT,
        direction=IndicatorDirection.LOW_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE_WITH_TRANSFORMATION,
        numerator="Retreatment pulmonary TB cases with sputum culture",
        denominator="Retreatment pulmonary TB cases",
        sources=("sinan_tb",),
        caveats="Combines entry type, pulmonary form, and culture fields.",
    ),
    IndicatorDefinition(
        indicator_id="hospitalization_burden_per_100k",
        name="TB hospitalization burden",
        unit=IndicatorUnit.PER_100K,
        direction=IndicatorDirection.HIGH_BAD,
        public_data_status=PublicDataStatus.OBTAINABLE,
        numerator="TB-related hospital admissions",
        denominator="Population denominator",
        sources=("sih_sus", "ibge_population"),
        caveats="Interprets hospitalizations as severity or care-pathway proxy, not incidence.",
    ),
)

MANDATORY_INDICATOR_IDS = frozenset(
    definition.indicator_id
    for definition in INDICATOR_DEFINITIONS
    if definition.indicator_id != "hospitalization_burden_per_100k"
)


def compute_indicator_values(
    populations: Iterable[PopulationDenominator],
    cases: Iterable[CaseAggregate],
    mortalities: Iterable[MortalityAggregate],
    hospitalizations: Iterable[HospitalizationAggregate] = (),
    *,
    year: int,
    minimum_count: int = 5,
) -> list[IndicatorValue]:
    population_by_territory = {item.territory_id: item for item in populations if item.year == year}
    case_by_territory = {item.territory_id: item for item in cases if item.year == year}
    mortality_by_territory = {item.territory_id: item for item in mortalities if item.year == year}
    hospitalization_by_territory = {
        item.territory_id: item for item in hospitalizations if item.year == year
    }

    values: list[IndicatorValue] = []
    territory_ids = sorted(
        set(population_by_territory)
        | set(case_by_territory)
        | set(mortality_by_territory)
        | set(hospitalization_by_territory)
    )

    for territory_id in territory_ids:
        population = population_by_territory.get(territory_id)
        case = case_by_territory.get(territory_id)
        mortality = mortality_by_territory.get(territory_id)
        hospitalization = hospitalization_by_territory.get(territory_id)

        if case is not None:
            values.extend(case_indicator_values(case, population, minimum_count))
        if mortality is not None:
            values.append(
                build_value(
                    "tb_mortality_per_100k",
                    territory_id,
                    year,
                    numerator=mortality.tb_deaths,
                    denominator=population.population if population is not None else 0,
                    source_ids=(mortality.source_id, "ibge_population"),
                    denominator_year=population.source_year if population is not None else None,
                    source_provenance=rate_provenance(
                        mortality.source_id,
                        "mortality",
                        year,
                        population,
                    ),
                    scale=100_000,
                    minimum_count=minimum_count,
                )
            )
        if hospitalization is not None:
            values.append(
                build_value(
                    "hospitalization_burden_per_100k",
                    territory_id,
                    year,
                    numerator=hospitalization.tb_admissions,
                    denominator=population.population if population is not None else 0,
                    source_ids=(hospitalization.source_id, "ibge_population"),
                    denominator_year=population.source_year if population is not None else None,
                    source_provenance=rate_provenance(
                        hospitalization.source_id,
                        "hospitalization",
                        year,
                        population,
                    ),
                    scale=100_000,
                    minimum_count=minimum_count,
                )
            )

    return values


def case_indicator_values(
    case: CaseAggregate,
    population: PopulationDenominator | None,
    minimum_count: int,
) -> list[IndicatorValue]:
    case_provenance = (
        SourceProvenance(case.source_id, reference_year=case.year, dataset_kind="notification"),
    )
    return [
        build_value(
            "tb_incidence_per_100k",
            case.territory_id,
            case.year,
            numerator=case.new_cases,
            denominator=population.population if population is not None else 0,
            source_ids=(case.source_id, "ibge_population"),
            denominator_year=population.source_year if population is not None else None,
            source_provenance=rate_provenance(
                case.source_id,
                "notification",
                case.year,
                population,
            ),
            scale=100_000,
            minimum_count=minimum_count,
        ),
        build_value(
            "cure_proportion",
            case.territory_id,
            case.year,
            numerator=case.cured_cases,
            denominator=case.closed_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "treatment_interruption_proportion",
            case.territory_id,
            case.year,
            numerator=case.treatment_interruption_cases,
            denominator=case.closed_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "retreatment_proportion",
            case.territory_id,
            case.year,
            numerator=case.retreatment_cases,
            denominator=case.notified_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "laboratory_confirmation_proportion",
            case.territory_id,
            case.year,
            numerator=case.lab_confirmed_pulmonary_cases,
            denominator=case.new_pulmonary_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "hiv_testing_proportion",
            case.territory_id,
            case.year,
            numerator=case.hiv_tested_cases,
            denominator=case.new_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "tb_hiv_burden_proportion",
            case.territory_id,
            case.year,
            numerator=case.tb_hiv_cases,
            denominator=case.new_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "trm_tb_use_proportion",
            case.territory_id,
            case.year,
            numerator=case.trm_tb_cases,
            denominator=case.new_pulmonary_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
        build_value(
            "culture_use_among_retreatment",
            case.territory_id,
            case.year,
            numerator=case.culture_retreated_cases,
            denominator=case.retreatment_pulmonary_cases,
            source_ids=(case.source_id,),
            denominator_year=case.year,
            source_provenance=case_provenance,
            scale=100,
            minimum_count=minimum_count,
        ),
    ]


def build_value(
    indicator_id: str,
    territory_id: str,
    year: int,
    *,
    numerator: float,
    denominator: float,
    source_ids: tuple[str, ...],
    denominator_year: int | None,
    source_provenance: tuple[SourceProvenance, ...],
    scale: float,
    minimum_count: int,
) -> IndicatorValue:
    definition = get_indicator_definition(indicator_id)
    bounded_proportion_violation = (
        definition.unit == IndicatorUnit.PERCENT and denominator > 0 and numerator > denominator
    )
    suppressed = denominator <= 0 or numerator < minimum_count or bounded_proportion_violation
    value = None if suppressed else numerator / denominator * scale
    caveats = definition.caveats
    if denominator <= 0:
        caveats = f"{caveats} Denominator unavailable or zero."
    elif bounded_proportion_violation:
        caveats = (
            f"{caveats} Suppressed for public output because numerator exceeds "
            "denominator for a bounded proportion."
        )
    elif numerator < minimum_count:
        caveats = f"{caveats} Suppressed for public output because count is below {minimum_count}."

    return IndicatorValue(
        indicator_id=indicator_id,
        territory_id=territory_id,
        year=year,
        value=value,
        numerator_value=numerator,
        denominator_value=denominator,
        is_suppressed=suppressed,
        source_ids=source_ids,
        caveats=caveats,
        denominator_year=denominator_year,
        source_provenance=source_provenance,
    )


def rate_provenance(
    event_source_id: str,
    event_dataset_kind: str,
    year: int,
    population: PopulationDenominator | None,
) -> tuple[SourceProvenance, ...]:
    event_source = SourceProvenance(
        event_source_id,
        reference_year=year,
        dataset_kind=event_dataset_kind,
    )
    population_source = SourceProvenance(
        population.source_id if population is not None else "ibge_population",
        reference_year=population.source_year if population is not None else None,
        dataset_kind=population.source_kind if population is not None else "unknown",
    )
    return event_source, population_source


def get_indicator_definition(indicator_id: str) -> IndicatorDefinition:
    for definition in INDICATOR_DEFINITIONS:
        if definition.indicator_id == indicator_id:
            return definition
    raise KeyError(f"unknown indicator: {indicator_id}")
