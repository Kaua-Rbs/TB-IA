from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from pytest import MonkeyPatch

from tbia.domain.models import (
    HospitalizationAggregate,
    PopulationDenominator,
    Territory,
)
from tbia.ingest.datasus import datasus_demo_files, format_month
from tbia.ingest.readers import (
    read_case_aggregates_csv,
    read_ibge_malhas_municipality_geometries,
    read_ibge_municipalities,
    read_public_subterritory_geojson,
    read_sidra_population_payload,
    read_sidra_values_population_payload,
)
from tbia.ingest.tabnet import parse_tabnet_prn_html
from tbia.pipeline import (
    Mvp1Config,
    build_and_store_scenarios,
    compute_and_store_indicators,
    datasus_source_candidates,
    ibge_malhas_url,
    ibge_population_url,
    ingest_ibge_malhas_geometries,
    ingest_public_subterritory_geometries,
    load_datasus_source,
    load_optional_csv_source,
    population_source_year,
    preserve_existing_geometries,
    seed_reference_data,
    select_existing_datasus_paths,
)
from tbia.storage import (
    create_engine_for_url,
    create_session_factory,
    initialize_database,
    latest_import_runs,
    latest_import_runs_for_scope,
    load_hospitalizations,
    load_indicator_values,
    load_territories,
    load_territory_scenarios,
    save_hospitalizations,
    save_populations,
    save_territories,
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


def test_read_ibge_municipalities_accepts_immediate_region_uf_fallback() -> None:
    payload = [
        {
            "id": 5101837,
            "nome": "Boa Esperança do Norte",
            "microrregiao": None,
            "regiao-imediata": {"regiao-intermediaria": {"UF": {"id": 51, "sigla": "MT"}}},
        }
    ]

    territories = read_ibge_municipalities(payload, "MT")

    assert [territory.territory_id for territory in territories] == ["5101837"]
    assert territories[0].name == "Boa Esperança do Norte"
    assert territories[0].uf_code == "51"


def test_population_source_year_defaults_to_2022_census() -> None:
    config = Mvp1Config(year=2023)

    assert population_source_year(config) == 2022
    assert ibge_population_url("23", 2022) == (
        "https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%2023/v/93/p/2022"
    )


def test_preserve_existing_geometries_keeps_cached_map_geometry() -> None:
    geometry = {"type": "Polygon", "coordinates": []}

    territories = preserve_existing_geometries(
        [Territory("2304400", "Fortaleza", "municipality", "23", "CE")],
        [
            Territory(
                "2304400",
                "Fortaleza",
                "municipality",
                "23",
                "CE",
                geometry=geometry,
            )
        ],
    )

    assert territories[0].geometry == geometry


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


def test_datasus_demo_files_for_brazil_downloads_sinan_once_and_regional_files() -> None:
    files = datasus_demo_files("BR", 2023, sih_months=(1,), cnes_month=12)

    local_names = [file.local_name for file in files]

    assert local_names.count("sinan_tb_br_2023.dbc") == 1
    assert "sim_ce_2023.dbc" in local_names
    assert "sim_pe_2023.dbc" in local_names
    assert "sih_ce_2023_01.dbc" in local_names
    assert "cnes_st_sp_2023_12.dbc" in local_names
    assert len(files) == 1 + (27 * 3)


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


def test_read_public_subterritory_geojson_keeps_only_polygonal_reference_children() -> None:
    geometry = {"type": "Polygon", "coordinates": [[[-39.0, -5.0], [-38.9, -5.0], [-39.0, -5.0]]]}
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "territory_id": "2304400-bairro-001",
                    "name": "Centro",
                    "territory_type": "neighborhood_reference",
                    "parent_id": "2304400",
                    "uf_code": "23",
                    "uf_sigla": "CE",
                },
                "geometry": geometry,
            },
            {
                "type": "Feature",
                "properties": {
                    "territory_id": "2304400-line",
                    "name": "Linha",
                    "territory_type": "neighborhood_reference",
                    "parent_id": "2304400",
                    "uf_code": "23",
                    "uf_sigla": "CE",
                },
                "geometry": {"type": "LineString", "coordinates": []},
            },
            {
                "type": "Feature",
                "properties": {
                    "territory_id": "2303709-bairro-001",
                    "name": "Outro",
                    "territory_type": "neighborhood_reference",
                    "parent_id": "2303709",
                    "uf_code": "23",
                    "uf_sigla": "CE",
                },
                "geometry": geometry,
            },
        ],
    }

    territories = read_public_subterritory_geojson(payload, {"2304400"})

    assert [territory.territory_id for territory in territories] == ["2304400-bairro-001"]
    assert territories[0].territory_type == "neighborhood_reference"
    assert territories[0].parent_id == "2304400"
    assert territories[0].geometry == geometry


def test_read_ibge_malhas_geometries_extracts_codarea() -> None:
    geometry = {"type": "Polygon", "coordinates": [[[-39.0, -5.0], [-38.9, -5.0], [-39.0, -5.0]]]}
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "ignored",
                "properties": {"codarea": "2304400"},
                "geometry": geometry,
            }
        ],
    }

    territories = read_ibge_malhas_municipality_geometries(
        payload, [Territory("2304400", "Fortaleza", "municipality", "23", "CE")]
    )

    assert len(territories) == 1
    assert territories[0].territory_id == "2304400"
    assert territories[0].geometry == geometry


def test_read_ibge_malhas_geometries_uses_feature_id_fallback() -> None:
    geometry = {"type": "MultiPolygon", "coordinates": []}
    payload = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "id": 2303709, "properties": {}, "geometry": geometry}],
    }

    territories = read_ibge_malhas_municipality_geometries(
        payload, [Territory("2303709", "Caucaia", "municipality", "23", "CE")]
    )

    assert [territory.territory_id for territory in territories] == ["2303709"]
    assert territories[0].geometry == geometry


def test_read_ibge_malhas_geometries_skips_unmatched_or_missing_geometry() -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"codarea": "9999999"},
                "geometry": {"type": "Polygon", "coordinates": []},
            },
            {"type": "Feature", "properties": {"codarea": "2304400"}},
        ],
    }

    territories = read_ibge_malhas_municipality_geometries(
        payload, [Territory("2304400", "Fortaleza", "municipality", "23", "CE")]
    )

    assert territories == []


def test_ingest_ibge_malhas_records_import_and_persists_geometry(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    geometry = {"type": "Polygon", "coordinates": [[[-39.0, -5.0], [-38.9, -5.0], [-39.0, -5.0]]]}
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"codarea": "2304400"},
                "geometry": geometry,
            }
        ],
    }

    def fake_fetch_json(url: str) -> object:
        assert url == ibge_malhas_url("23")
        return payload

    monkeypatch.setattr("tbia.pipeline.fetch_json", fake_fetch_json)
    with session_factory() as session:
        save_territories(session, [Territory("2304400", "Fortaleza", "municipality", "23", "CE")])
        ingest_ibge_malhas_geometries(session, Mvp1Config(uf="CE", uf_code="23", raw_dir=tmp_path))
        session.commit()
        territory = load_territories(session, "CE")[0]
        runs = latest_import_runs(session)

    engine.dispose()

    assert territory.geometry == geometry
    assert (tmp_path / "ibge_malhas" / "ce_23_municipios.geojson").exists()
    assert runs[0]["source_id"] == "ibge_malhas"
    assert runs[0]["status"] == "success"
    assert runs[0]["row_count"] == 1


def test_ingest_public_subterritory_geometries_loads_normalized_geojson(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    geometry = {"type": "MultiPolygon", "coordinates": []}
    intramunicipal_dir = tmp_path / "ibge_intramunicipal"
    intramunicipal_dir.mkdir()
    (intramunicipal_dir / "fortaleza_bairros.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "territory_id": "2304400-bairro-001",
                            "name": "Centro",
                            "territory_type": "neighborhood_reference",
                            "parent_id": "2304400",
                            "uf_code": "23",
                            "uf_sigla": "CE",
                        },
                        "geometry": geometry,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with session_factory() as session:
        save_territories(session, [Territory("2304400", "Fortaleza", "municipality", "23", "CE")])
        ingest_public_subterritory_geometries(session, Mvp1Config(uf="CE", raw_dir=tmp_path))
        session.commit()
        bairros = load_territories(session, "CE", "neighborhood_reference")
        municipalities = load_territories(session, "CE")
        runs = latest_import_runs(session)

    engine.dispose()

    assert [territory.territory_id for territory in municipalities] == ["2304400"]
    assert [territory.territory_id for territory in bairros] == ["2304400-bairro-001"]
    assert bairros[0].geometry == geometry
    assert runs[0]["source_id"] == "ibge_intramunicipal"
    assert runs[0]["status"] == "success"
    assert runs[0]["row_count"] == 1


def test_ingest_ibge_malhas_failure_records_failed_run(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'mvp1.db'}"
    engine = create_engine_for_url(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    def fake_fetch_json(_: str) -> object:
        raise RuntimeError("offline")

    monkeypatch.setattr("tbia.pipeline.fetch_json", fake_fetch_json)
    with session_factory() as session:
        save_territories(session, [Territory("2304400", "Fortaleza", "municipality", "23", "CE")])
        ingest_ibge_malhas_geometries(session, Mvp1Config(uf="CE", uf_code="23", raw_dir=tmp_path))
        session.commit()
        runs = latest_import_runs(session)

    engine.dispose()

    assert runs[0]["source_id"] == "ibge_malhas"
    assert runs[0]["status"] == "failed"
    assert "offline" in runs[0]["message"]


def test_partial_sih_coverage_is_persisted_but_excluded_from_ranking(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    config = Mvp1Config(
        uf="CE",
        year=2023,
        raw_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
    )
    config.datasus_sample_dir.mkdir(parents=True)
    sih_paths = [
        config.datasus_sample_dir / f"sih_ce_2023_{month:02d}.dbc" for month in range(1, 13)
    ]
    for path in sih_paths:
        path.touch()

    monkeypatch.setattr("tbia.pipeline.read_datasus_records", lambda path: [{}])
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'coverage.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    territory_ids = {f"23{index:05d}" for index in range(1, 6)}

    def transformed_hospitalizations(
        records: Sequence[dict[str, object]],
    ) -> list[HospitalizationAggregate]:
        return [
            HospitalizationAggregate(territory_id, 2023, len(records) * 10)
            for territory_id in sorted(territory_ids)
        ]

    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [
                Territory(territory_id, territory_id, "municipality", "23", "CE")
                for territory_id in sorted(territory_ids)
            ],
        )
        save_populations(
            session,
            [
                PopulationDenominator(territory_id, 2023, 100_000, "ibge_population")
                for territory_id in sorted(territory_ids)
            ],
        )

        assert load_datasus_source(
            session,
            config,
            source_id="sih_sus",
            paths=sih_paths,
            transform=transformed_hospitalizations,
            saver=lambda active_session, rows: save_hospitalizations(
                active_session,
                rows,
                replace_territory_ids=territory_ids,
            ),
            track_month_coverage=True,
        )
        compute_and_store_indicators(session, config)
        build_and_store_scenarios(session, config)
        session.commit()

        full_source = next(
            row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="CE")
            if row["source_id"] == "sih_sus"
        )
        full_indicator_ids = {value.indicator_id for value in load_indicator_values(session, 2023)}
        full_scenario_ids = {
            scenario.rule_id for scenario in load_territory_scenarios(session, 2023, "uf")
        }

        assert load_datasus_source(
            session,
            config,
            source_id="sih_sus",
            paths=sih_paths[:1],
            transform=transformed_hospitalizations,
            saver=lambda active_session, rows: save_hospitalizations(
                active_session,
                rows,
                replace_territory_ids=territory_ids,
            ),
            track_month_coverage=True,
        )
        compute_and_store_indicators(session, config)
        build_and_store_scenarios(session, config)
        session.commit()

        partial_source = next(
            row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="CE")
            if row["source_id"] == "sih_sus"
        )
        partial_indicator_ids = {
            value.indicator_id for value in load_indicator_values(session, 2023)
        }
        partial_scenario_ids = {
            scenario.rule_id for scenario in load_territory_scenarios(session, 2023, "uf")
        }
        persisted_hospitalizations = load_hospitalizations(session, 2023)
    engine.dispose()

    assert full_source["status"] == "success"
    assert full_source["month_coverage"]["complete"] is True
    assert full_source["month_coverage"]["loaded_months"] == list(range(1, 13))
    assert "hospitalization_burden_per_100k" in full_indicator_ids
    assert "high_hospitalization_burden" in full_scenario_ids

    assert partial_source["status"] == "partial"
    assert partial_source["month_coverage"]["complete"] is False
    assert partial_source["month_coverage"]["loaded_months"] == [1]
    assert partial_source["month_coverage"]["missing_months"] == list(range(2, 13))
    assert "hospitalization_burden_per_100k" not in partial_indicator_ids
    assert "high_hospitalization_burden" not in partial_scenario_ids
    assert {row.tb_admissions for row in persisted_hospitalizations} == {10}


def test_manual_sih_without_month_provenance_is_excluded_from_indicators(
    tmp_path: Path,
) -> None:
    config = Mvp1Config(
        uf="CE",
        year=2023,
        raw_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
    )
    config.manual_dir.mkdir(parents=True)
    manual_path = config.manual_csv("hospitalization_aggregates.csv")
    manual_path.write_text("fixture", encoding="utf-8")

    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'manual-coverage.db'}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        seed_reference_data(session)
        save_territories(
            session,
            [Territory("2304400", "Fortaleza", "municipality", "23", "CE")],
        )
        save_populations(
            session,
            [PopulationDenominator("2304400", 2023, 100_000, "ibge_population")],
        )
        load_optional_csv_source(
            session,
            config,
            "sih_sus",
            manual_path.name,
            lambda path: [HospitalizationAggregate("2304400", 2023, 10)],
            save_hospitalizations,
            skip_sources=set(),
        )
        compute_and_store_indicators(session, config)
        session.commit()

        source = next(
            row
            for row in latest_import_runs_for_scope(session, year=2023, geographic_scope="CE")
            if row["source_id"] == "sih_sus"
        )
        indicator_ids = {value.indicator_id for value in load_indicator_values(session, 2023)}
        hospitalizations = load_hospitalizations(session, 2023)
    engine.dispose()

    assert source["status"] == "partial"
    assert source["month_coverage"]["loaded_months"] is None
    assert source["month_coverage"]["complete"] is False
    assert "hospitalization_burden_per_100k" not in indicator_ids
    assert hospitalizations[0].tb_admissions == 10
