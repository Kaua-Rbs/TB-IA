from __future__ import annotations

from dataclasses import dataclass

from tbia.domain.models import DataSource


@dataclass(frozen=True)
class SourceContract:
    source_id: str
    name: str
    owner: str
    access_method: str
    file_format: str
    grain: str
    geographic_coverage: str
    time_coverage: str
    refresh_cadence: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    code_systems: tuple[str, ...]
    missingness_rules: str
    duplicate_handling: str
    privacy_level: str
    validation_checks: tuple[str, ...]
    caveats: str

    def as_data_source(self) -> DataSource:
        return DataSource(
            source_id=self.source_id,
            name=self.name,
            owner=self.owner,
            access_method=self.access_method,
            format=self.file_format,
            grain=self.grain,
            privacy_level=self.privacy_level,
            refresh_cadence=self.refresh_cadence,
            caveats=self.caveats,
        )


SOURCE_CONTRACTS: tuple[SourceContract, ...] = (
    SourceContract(
        source_id="ibge_localidades",
        name="IBGE Localidades",
        owner="IBGE",
        access_method="HTTPS API",
        file_format="JSON",
        grain="municipality",
        geographic_coverage="Brazil",
        time_coverage="current territorial registry",
        refresh_cadence="as published by IBGE",
        required_fields=("id", "nome", "microrregiao.mesorregiao.UF.sigla"),
        optional_fields=("regiao-imediata", "regiao-intermediaria"),
        code_systems=("IBGE municipality code", "UF code"),
        missingness_rules="Reject municipality records without IBGE code, name, or UF.",
        duplicate_handling="Use IBGE municipality code as the natural key.",
        privacy_level="public aggregate metadata",
        validation_checks=("unique municipality code", "requested UF matches response UF"),
        caveats="Territorial boundaries and municipality registry can change over time.",
    ),
    SourceContract(
        source_id="ibge_population",
        name="IBGE population denominator",
        owner="IBGE",
        access_method="SIDRA/Agregados HTTPS API or CSV export",
        file_format="JSON/CSV",
        grain="municipality-year",
        geographic_coverage="Brazil",
        time_coverage="selected year",
        refresh_cadence="annual or census release",
        required_fields=("municipality_code", "year", "population"),
        optional_fields=("source_table",),
        code_systems=("IBGE municipality code",),
        missingness_rules="Reject rows with missing or non-positive population.",
        duplicate_handling="One population denominator per municipality-year-stratifier.",
        privacy_level="public aggregate denominator",
        validation_checks=("positive population", "municipality exists in Territory"),
        caveats="Population estimates and census values must not be mixed without metadata.",
    ),
    SourceContract(
        source_id="sinan_tb",
        name="SINAN-TB / DATASUS",
        owner="Ministry of Health / DATASUS",
        access_method="DATASUS FTP DBC, TabNet PRN/HTML, or manual CSV fallback",
        file_format="DBC/DBF/CSV",
        grain="municipality-year aggregate for MVP 1",
        geographic_coverage="Brazil",
        time_coverage="selected notification or cohort year",
        refresh_cadence="DATASUS publication cadence; subject to delay",
        required_fields=(
            "municipality_code",
            "year",
            "notified_cases",
            "new_cases",
            "closed_cases",
            "cured_cases",
            "treatment_interruption_cases",
            "retreatment_cases",
            "new_pulmonary_cases",
            "lab_confirmed_pulmonary_cases",
            "hiv_tested_cases",
            "tb_hiv_cases",
            "trm_tb_cases",
            "retreatment_pulmonary_cases",
            "culture_retreated_cases",
        ),
        optional_fields=("source_period",),
        code_systems=("IBGE municipality code", "SINAN-TB dictionaries"),
        missingness_rules=(
            "Missing numeric metrics are treated as zero only in curated aggregate CSVs."
        ),
        duplicate_handling="Aggregate duplicate municipality-year rows by summing counts.",
        privacy_level="public aggregate or public anonymized microdata transformed to aggregate",
        validation_checks=("non-negative counts", "new cases <= notified cases when both exist"),
        caveats=(
            "Official mappings for entry type, closure, HIV, TRM-TB, and culture must be reviewed."
        ),
    ),
    SourceContract(
        source_id="sim",
        name="SIM mortality",
        owner="Ministry of Health / DATASUS",
        access_method="DATASUS FTP DBC or manual CSV fallback",
        file_format="DBC/DBF/CSV",
        grain="municipality-year aggregate",
        geographic_coverage="Brazil",
        time_coverage="selected death year",
        refresh_cadence="DATASUS publication cadence; subject to delay",
        required_fields=("municipality_code", "year", "tb_deaths"),
        optional_fields=("source_period",),
        code_systems=("IBGE municipality code", "CID-10 A15-A19"),
        missingness_rules="Reject rows with missing municipality, year, or death count.",
        duplicate_handling="Aggregate duplicate municipality-year rows by summing deaths.",
        privacy_level="public aggregate",
        validation_checks=("non-negative deaths",),
        caveats=(
            "Filter should use underlying cause CID-10 A15-A19 for the MVP mortality indicator."
        ),
    ),
    SourceContract(
        source_id="sih_sus",
        name="SIH/SUS hospital admissions",
        owner="Ministry of Health / DATASUS",
        access_method="DATASUS FTP DBC or manual CSV fallback",
        file_format="DBC/DBF/CSV",
        grain="municipality-year aggregate",
        geographic_coverage="Brazil",
        time_coverage="selected admission year/months",
        refresh_cadence="monthly publication subject to delay",
        required_fields=("municipality_code", "year", "tb_admissions"),
        optional_fields=("source_period",),
        code_systems=("IBGE municipality code", "CID-10 A15-A19"),
        missingness_rules="Reject rows with missing municipality, year, or admission count.",
        duplicate_handling="Aggregate duplicate municipality-year rows by summing admissions.",
        privacy_level="public aggregate",
        validation_checks=("non-negative admissions",),
        caveats="Hospitalization is a severity or care-pathway proxy, not an incidence measure.",
    ),
    SourceContract(
        source_id="cnes",
        name="CNES facility and capacity snapshot",
        owner="Ministry of Health / DATASUS",
        access_method="DATASUS FTP DBC or manual CSV fallback",
        file_format="DBC/DBF/CSV",
        grain="facility-month snapshot",
        geographic_coverage="Brazil",
        time_coverage="selected month",
        refresh_cadence="monthly publication subject to delay",
        required_fields=("facility_id", "municipality_code", "name", "facility_type"),
        optional_fields=("sus_linked",),
        code_systems=("CNES", "IBGE municipality code"),
        missingness_rules="Reject rows without CNES code or municipality.",
        duplicate_handling="Use latest snapshot per facility for the selected period.",
        privacy_level="public facility metadata",
        validation_checks=("unique facility code", "municipality exists in Territory"),
        caveats="CNES capacity proxies require domain review before operational interpretation.",
    ),
)


def get_source_contract(source_id: str) -> SourceContract:
    for contract in SOURCE_CONTRACTS:
        if contract.source_id == source_id:
            return contract
    raise KeyError(f"unknown source contract: {source_id}")
