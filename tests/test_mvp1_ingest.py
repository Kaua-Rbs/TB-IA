from __future__ import annotations

from pathlib import Path

from tbia.ingest.datasus import datasus_demo_files, format_month
from tbia.ingest.readers import (
    read_case_aggregates_csv,
    read_ibge_municipalities,
    read_sidra_population_payload,
    read_sidra_values_population_payload,
)
from tbia.ingest.tabnet import parse_tabnet_prn_html
from tbia.pipeline import (
    Mvp1Config,
    datasus_source_candidates,
    ibge_population_url,
    population_source_year,
    select_existing_datasus_paths,
)


def test_read_ibge_municipalities_filters_requested_uf() -> None:
    payload = [
        {
            "id": 2304400,
            "nome": "Fortaleza",
            "microrregiao": {"mesorregiao": {"UF": {"id": 23, "sigla": "CE"}}},
        },
        {
            "id": 2607901,
            "nome": "Jaboatao dos Guararapes",
            "microrregiao": {"mesorregiao": {"UF": {"id": 26, "sigla": "PE"}}},
        },
    ]

    territories = read_ibge_municipalities(payload, "CE")

    assert [territory.territory_id for territory in territories] == ["2304400"]
    assert territories[0].name == "Fortaleza"


def test_population_source_year_defaults_to_2022_census() -> None:
    config = Mvp1Config(year=2023)

    assert population_source_year(config) == 2022
    assert ibge_population_url("23", 2022) == (
        "https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%2023/v/93/p/2022"
    )


def test_read_sidra_population_payload_extracts_municipality_year() -> None:
    payload = [
        {
            "resultados": [
                {
                    "series": [
                        {"localidade": {"id": "2304400"}, "serie": {"2023": "2570000"}},
                        {"localidade": {"id": "2303709"}, "serie": {"2023": "..."}},
                    ]
                }
            ]
        }
    ]

    populations = read_sidra_population_payload(payload, 2023)

    assert len(populations) == 1
    assert populations[0].territory_id == "2304400"
    assert populations[0].population == 2_570_000


def test_read_sidra_values_population_payload_extracts_census_denominator() -> None:
    payload = [
        {"V": "Valor", "D1C": "Município (Código)"},
        {"V": "2428708", "D1C": "2304400"},
        {"V": "-", "D1C": "2303709"},
    ]

    populations = read_sidra_values_population_payload(payload, analysis_year=2023)

    assert len(populations) == 1
    assert populations[0].territory_id == "2304400"
    assert populations[0].year == 2023
    assert populations[0].population == 2_428_708


def test_read_case_aggregates_csv_collapses_duplicate_municipality_year(tmp_path: Path) -> None:
    csv_path = tmp_path / "case_aggregates.csv"
    csv_path.write_text(
        "\n".join(
            [
                "municipality_code,year,notified_cases,new_cases,closed_cases,cured_cases,"
                "treatment_interruption_cases,retreatment_cases,new_pulmonary_cases,"
                "lab_confirmed_pulmonary_cases,hiv_tested_cases,tb_hiv_cases,trm_tb_cases,"
                "retreatment_pulmonary_cases,culture_retreated_cases",
                "2304400,2023,10,8,7,5,1,2,6,4,6,1,3,2,1",
                "2304400,2023,3,2,3,2,1,1,2,1,2,0,1,1,1",
            ]
        ),
        encoding="utf-8",
    )

    aggregates = read_case_aggregates_csv(csv_path)

    assert len(aggregates) == 1
    assert aggregates[0].new_cases == 10
    assert aggregates[0].cured_cases == 7
    assert aggregates[0].culture_retreated_cases == 2


def test_parse_tabnet_prn_html_reads_pre_block() -> None:
    rows = parse_tabnet_prn_html(
        "<html><body><pre>Municipio;Casos\nFortaleza;10\n"
        "Sobral;5\nFonte: TabNet</pre></body></html>"
    )

    assert rows == [
        {"Municipio": "Fortaleza", "Casos": "10"},
        {"Municipio": "Sobral", "Casos": "5"},
    ]


def test_datasus_demo_files_align_with_ingestion_names() -> None:
    files = datasus_demo_files("CE", 2023, sih_months=(1, 2), cnes_month=12)

    local_names = [file.local_name for file in files]

    assert local_names == [
        "sim_ce_2023.dbc",
        "sinan_tb_br_2023.dbc",
        "sih_ce_2023_01.dbc",
        "sih_ce_2023_02.dbc",
        "cnes_st_ce_2023_12.dbc",
    ]
    assert files[0].ftp_url == (
        "ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DOCE2023.dbc"
    )
    assert files[2].remote_path.endswith("RDCE2301.dbc")


def test_format_month_rejects_invalid_month() -> None:
    try:
        format_month(13)
    except ValueError as exc:
        assert "between 1 and 12" in str(exc)
    else:
        raise AssertionError("format_month accepted an invalid month")


def test_datasus_source_candidates_keep_cnes_in_configured_year(tmp_path: Path) -> None:
    sample_dir = tmp_path / "datasus_samples"
    sample_dir.mkdir()
    current_snapshot = sample_dir / "cnes_st_ce_2023_12.dbc"
    old_snapshot = sample_dir / "cnes_st_ce_2024_01.dbc"
    current_snapshot.touch()
    old_snapshot.touch()

    candidates = datasus_source_candidates(Mvp1Config(uf="CE", year=2023, raw_dir=tmp_path), "cnes")

    assert candidates == (current_snapshot,)


def test_select_existing_datasus_paths_prefers_dbf_over_dbc(tmp_path: Path) -> None:
    dbf_path = tmp_path / "sim_ce_2023.dbf"
    dbc_path = tmp_path / "sim_ce_2023.dbc"
    other_dbc_path = tmp_path / "sih_ce_2023_01.dbc"
    dbf_path.touch()
    dbc_path.touch()
    other_dbc_path.touch()

    selected = select_existing_datasus_paths((dbc_path, dbf_path, other_dbc_path))

    assert selected == [dbf_path, other_dbc_path]
