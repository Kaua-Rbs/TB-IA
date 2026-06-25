from __future__ import annotations

from pathlib import Path

from tbia.ingest.readers import (
    read_case_aggregates_csv,
    read_ibge_municipalities,
    read_sidra_population_payload,
)
from tbia.ingest.tabnet import parse_tabnet_prn_html


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
