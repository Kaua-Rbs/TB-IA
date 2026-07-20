from __future__ import annotations

import pytest

from tbia.domain.models import Territory
from tbia.ingest.datasus_transforms import (
    build_datasus_municipality_map,
    transform_cnes_records,
    transform_sih_records,
    transform_sim_records,
    transform_sinan_tb_records,
)


def municipality_map() -> dict[str, str]:
    return build_datasus_municipality_map(
        [
            Territory("2304400", "Fortaleza", "municipality", "23", "CE"),
            Territory("2312908", "Sobral", "municipality", "23", "CE"),
        ]
    )


def test_transform_sinan_tb_records_builds_case_aggregates() -> None:
    records = [
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "1",
            "FORMA": "1",
            "SITUA_ENCE": "1",
            "HIV": "1",
            "AGRAVAIDS": "2",
            "BACILOSC_E": "1",
            "CULTURA_ES": "4",
            "TEST_MOLEC": "1",
            "RIFAMPICIN": "",
        },
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "3",
            "FORMA": "3",
            "SITUA_ENCE": "2",
            "HIV": "2",
            "AGRAVAIDS": "1",
            "BACILOSC_E": "2",
            "CULTURA_ES": "2",
            "TEST_MOLEC": "5",
            "RIFAMPICIN": "2",
        },
        {
            "NU_ANO": "2022",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "1",
        },
    ]

    aggregates = transform_sinan_tb_records(records, municipality_map(), year=2023)

    assert len(aggregates) == 1
    aggregate = aggregates[0]
    assert aggregate.territory_id == "2304400"
    assert aggregate.notified_cases == 2
    assert aggregate.new_cases == 1
    assert aggregate.cured_cases == 1
    assert aggregate.treatment_interruption_cases == 0
    assert aggregate.retreatment_cases == 1
    assert aggregate.new_pulmonary_cases == 1
    assert aggregate.lab_confirmed_pulmonary_cases == 1
    assert aggregate.trm_tb_cases == 1
    assert aggregate.hiv_tested_cases == 1
    assert aggregate.tb_hiv_cases == 1
    assert aggregate.culture_retreated_cases == 1


@pytest.mark.parametrize(
    ("test_molec", "expected_use", "expected_confirmation"),
    [
        ("1", 1, 1),
        ("2", 1, 1),
        ("3", 1, 0),
        ("4", 1, 0),
        ("5", 0, 0),
        ("9", 0, 0),
        ("", 0, 0),
    ],
)
def test_transform_sinan_uses_test_molec_for_trm_and_confirmation(
    test_molec: str,
    expected_use: int,
    expected_confirmation: int,
) -> None:
    records = [
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "1",
            "FORMA": "1",
            "SITUA_ENCE": "1",
            "BACILOSC_E": "2",
            "CULTURA_ES": "4",
            "TEST_MOLEC": test_molec,
            "RIFAMPICIN": "1",
        }
    ]

    aggregate = transform_sinan_tb_records(records, municipality_map(), year=2023)[0]

    assert aggregate.trm_tb_cases == expected_use
    assert aggregate.lab_confirmed_pulmonary_cases == expected_confirmation


def test_transform_sinan_tb_records_restricts_hiv_and_outcomes_to_new_case_universe() -> None:
    records = [
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "4",
            "FORMA": "2",
            "SITUA_ENCE": "10",
            "HIV": "2",
            "AGRAVAIDS": "2",
        },
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "6",
            "FORMA": "1",
            "SITUA_ENCE": "7",
            "HIV": "1",
            "AGRAVAIDS": "2",
        },
        {
            "NU_ANO": "2023",
            "ID_MN_RESI": "230440",
            "TRATAMENTO": "2",
            "FORMA": "1",
            "SITUA_ENCE": "2",
            "HIV": "1",
            "AGRAVAIDS": "1",
        },
    ]

    aggregates = transform_sinan_tb_records(records, municipality_map(), year=2023)

    aggregate = aggregates[0]
    assert aggregate.notified_cases == 3
    assert aggregate.new_cases == 2
    assert aggregate.retreatment_cases == 1
    assert aggregate.closed_cases == 1
    assert aggregate.treatment_interruption_cases == 1
    assert aggregate.hiv_tested_cases == 2
    assert aggregate.tb_hiv_cases == 1
    assert aggregate.new_pulmonary_cases == 1
    assert aggregate.retreatment_pulmonary_cases == 1


def test_transform_sim_records_filters_tb_deaths_by_residence() -> None:
    records = [
        {"DTOBITO": "01012023", "CAUSABAS": "A150", "CODMUNRES": "230440"},
        {"DTOBITO": "02012023", "CAUSABAS": "I219", "CODMUNRES": "230440"},
        {"DTOBITO": "03012024", "CAUSABAS": "A169", "CODMUNRES": "230440"},
    ]

    aggregates = transform_sim_records(records, municipality_map(), year=2023)

    assert len(aggregates) == 1
    assert aggregates[0].territory_id == "2304400"
    assert aggregates[0].tb_deaths == 1


def test_transform_sih_records_filters_tb_admissions_by_year_and_diagnosis() -> None:
    records = [
        {"ANO_CMPT": "2023", "DIAG_PRINC": "A150", "DIAG_SECUN": "0000", "MUNIC_RES": "230440"},
        {"ANO_CMPT": "2023", "DIAG_PRINC": "J189", "DIAG_SECUN": "A169", "MUNIC_RES": "230440"},
        {"ANO_CMPT": "2024", "DIAG_PRINC": "A150", "DIAG_SECUN": "0000", "MUNIC_RES": "230440"},
    ]

    aggregates = transform_sih_records(records, municipality_map(), year=2023)

    assert len(aggregates) == 1
    assert aggregates[0].territory_id == "2304400"
    assert aggregates[0].tb_admissions == 2


def test_transform_cnes_records_builds_facilities() -> None:
    records = [
        {
            "CNES": "000001",
            "CODUFMUN": "230440",
            "TP_UNID": "02",
            "VINC_SUS": "1",
        },
        {
            "CNES": "000002",
            "CODUFMUN": "999999",
            "TP_UNID": "02",
            "VINC_SUS": "1",
        },
    ]

    facilities = transform_cnes_records(records, municipality_map())

    assert len(facilities) == 1
    assert facilities[0].facility_id == "000001"
    assert facilities[0].territory_id == "2304400"
    assert facilities[0].sus_linked is True
