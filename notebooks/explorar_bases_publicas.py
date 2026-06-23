# %% [markdown]
# Exploracao inicial de bases publicas para TB-IA
#
# Este notebook baixa pequenas amostras de bases publicas recomendadas para o MVP 1 e organiza os dados no formato que o sistema deve consumir depois.
#
# O foco aqui e visualizacao e validacao inicial, nao ingestao de producao.
#
# Fontes executaveis diretamente neste notebook:
#
# - IBGE Localidades: municipios, UF, regioes.
# - IBGE SIDRA/agregados: populacao residente estimada.
# - IBGE Malhas: geometria municipal simplificada em GeoJSON.
#
# Fontes DATASUS/CNES/SINAN/SIM tambem podem ser exploradas por download direto de arquivos DBC publicos quando a URL do arquivo for estavel. O notebook baixa algumas amostras pequenas para visualizacao e mantem CSVs manuais como fallback.
#

# %% [markdown]
## Como rodar
#
# Instale as dependencias exploratorias fora do gate principal do projeto:
#
# ```bash
# python -m pip install -r requirements-notebook.txt
# jupyter lab notebooks/explorar_bases_publicas.ipynb
# ```
#
# Os dados baixados pelo notebook ficam em `data/raw/` e `data/processed/`, ambos ignorados pelo git.
#

# %%
from __future__ import annotations

import csv
import ftplib
import gzip
import json
from html import unescape
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
import pandas as pd

try:
    from IPython.display import display
except ImportError:
    def display(value):
        print(value)

# Detecta se o notebook foi aberto na raiz do repo ou dentro de notebooks/.
PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PUBLIC_CACHE_DIR = RAW_DIR / "public_sources"
MANUAL_DIR = RAW_DIR / "manual"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

for directory in [PUBLIC_CACHE_DIR, MANUAL_DIR, PROCESSED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 140)

def decode_http_payload(body: bytes, encoding: str | None) -> str:
    """Decodifica respostas JSON que alguns servicos retornam comprimidas."""
    if encoding and "gzip" in encoding.lower():
        body = gzip.decompress(body)
    elif body.startswith(b"\x1f\x8b"):
        body = gzip.decompress(body)
    return body.decode("utf-8")

def fetch_json(url: str, cache_name: str, refresh: bool = False, timeout: int = 60):
    """Baixa JSON com cache simples para evitar chamadas repetidas."""
    cache_path = PUBLIC_CACHE_DIR / cache_name
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text(encoding="utf-8"))

    request = Request(url, headers={"User-Agent": "TB-IA exploratory notebook"})
    with urlopen(request, timeout=timeout) as response:
        payload = decode_http_payload(response.read(), response.headers.get("Content-Encoding"))
    cache_path.write_text(payload, encoding="utf-8")
    return json.loads(payload)

def save_frame(df: pd.DataFrame, name: str) -> Path:
    path = PROCESSED_DIR / name
    df.to_csv(path, index=False)
    print(f"saved: {path.relative_to(PROJECT_ROOT)}")
    return path


# %%
# Configuracao inicial: Ceara e municipios de interesse para uma amostra leve.
UF_ID = 23
UF_SIGLA = "CE"
ANO_POPULACAO = 2025

MUNICIPIOS_AMOSTRA = {
    "Fortaleza": "2304400",
    "Caucaia": "2303709",
    "Juazeiro do Norte": "2307304",
    "Maracanau": "2307650",
    "Sobral": "2312908",
}

MUNICIPIO_MAPA_ID = MUNICIPIOS_AMOSTRA["Fortaleza"]


# %% [markdown]
# ## IBGE Localidades: municipios


# %%
# IBGE Localidades: municipios do Ceara.
municipios_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF_ID}/municipios"
municipios_json = fetch_json(municipios_url, f"ibge_municipios_{UF_SIGLA.lower()}.json")

municipios = pd.json_normalize(municipios_json)
municipios_df = municipios.rename(
    columns={
        "id": "municipality_id",
        "nome": "municipality_name",
        "microrregiao.mesorregiao.UF.id": "uf_id",
        "microrregiao.mesorregiao.UF.sigla": "uf_sigla",
        "microrregiao.mesorregiao.UF.nome": "uf_name",
        "microrregiao.mesorregiao.UF.regiao.id": "region_id",
        "microrregiao.mesorregiao.UF.regiao.sigla": "region_sigla",
        "microrregiao.mesorregiao.UF.regiao.nome": "region_name",
    }
)[
    [
        "municipality_id",
        "municipality_name",
        "uf_id",
        "uf_sigla",
        "uf_name",
        "region_id",
        "region_sigla",
        "region_name",
    ]
]
municipios_df["municipality_id"] = municipios_df["municipality_id"].astype(str)
municipios_df.head()


# %% [markdown]
# ## IBGE SIDRA: populacao municipal


# %%
# IBGE SIDRA/agregados: populacao residente estimada.
# Agregado 6579, variavel 9324: Populacao residente estimada.
municipality_ids = ",".join(MUNICIPIOS_AMOSTRA.values())
pop_url = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/"
    f"periodos/{ANO_POPULACAO}/variaveis/9324?localidades=N6%5B{municipality_ids}%5D"
)
pop_json = fetch_json(pop_url, f"ibge_populacao_estimada_{ANO_POPULACAO}_{UF_SIGLA.lower()}_amostra.json")

def parse_sidra_population(payload: list[dict], year: int) -> pd.DataFrame:
    rows = []
    for variable in payload:
        for result in variable.get("resultados", []):
            for item in result.get("series", []):
                localidade = item["localidade"]
                rows.append(
                    {
                        "municipality_id": str(localidade["id"]),
                        "municipality_name_sidra": localidade["nome"],
                        "year": year,
                        "population": int(item["serie"][str(year)]),
                        "source": "IBGE SIDRA aggregate 6579 variable 9324",
                    }
                )
    return pd.DataFrame(rows)

population_df = parse_sidra_population(pop_json, ANO_POPULACAO)
population_df = population_df.merge(municipios_df, on="municipality_id", how="left")
population_df = population_df[
    ["municipality_id", "municipality_name", "uf_sigla", "year", "population", "source"]
].sort_values("population", ascending=False)

save_frame(population_df, f"ibge_populacao_amostra_{UF_SIGLA.lower()}_{ANO_POPULACAO}.csv")
population_df


# %%
ax = population_df.sort_values("population").plot.barh(
    x="municipality_name",
    y="population",
    figsize=(8, 4),
    legend=False,
    color="#2F6B4F",
)
ax.set_title(f"Populacao estimada - amostra {UF_SIGLA}, {ANO_POPULACAO}")
ax.set_xlabel("Populacao")
ax.set_ylabel("")
ax.grid(axis="x", alpha=0.25)
plt.tight_layout()
plt.show()


# %% [markdown]
# ## IBGE Malhas: geometria para mapas


# %%
# IBGE Malhas: geometria municipal simplificada em GeoJSON.
malha_url = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/"
    f"municipios/{MUNICIPIO_MAPA_ID}?formato=application/vnd.geo+json&qualidade=minima"
)
malha_geojson = fetch_json(malha_url, f"ibge_malha_municipio_{MUNICIPIO_MAPA_ID}.geojson")
malha_geojson["features"][0]["properties"]


# %%
def plot_geojson_feature(feature: dict, title: str) -> None:
    geometry = feature["geometry"]
    if geometry["type"] == "Polygon":
        polygons = [geometry["coordinates"]]
    elif geometry["type"] == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        raise ValueError(f"Geometry type not supported: {geometry['type']}")

    fig, ax = plt.subplots(figsize=(6, 6))
    for polygon in polygons:
        exterior = polygon[0]
        xs = [point[0] for point in exterior]
        ys = [point[1] for point in exterior]
        ax.fill(xs, ys, color="#DCE8F2", edgecolor="#23415C", linewidth=1.2)

    ax.set_title(title)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.show()

plot_geojson_feature(malha_geojson["features"][0], "Malha simplificada - Fortaleza (IBGE)")


# %% [markdown]
## Contratos de dados para as bases do MVP
#
# A tabela abaixo e o primeiro esqueleto de contrato: onde buscar, como estruturar e quem consome. Ela nao baixa todos os dados ainda; serve para guiar a ingestao incremental.
#

# %%
data_contracts = pd.DataFrame(
    [
        {
            "source": "SINAN-TB / DATASUS",
            "grain": "territory-period-strata aggregate for MVP 1; line list only with authorization",
            "format": "TabNet export CSV or DBC/DBF converted to CSV/Parquet",
            "canonical_entity": "CaseAggregate",
            "consumers": "Indicator engine; scenario engine; dashboards",
            "mvp_status": "manual CSV/converted file first",
        },
        {
            "source": "SIM",
            "grain": "territory-period-strata aggregate; CID-10 A15-A19 for TB deaths",
            "format": "TabNet export CSV or DBC/DBF converted to CSV/Parquet",
            "canonical_entity": "MortalityAggregate",
            "consumers": "Mortality indicators; scenario engine; dashboards",
            "mvp_status": "manual CSV/converted file first",
        },
        {
            "source": "IBGE Populacao/SIDRA",
            "grain": "municipality-year population denominator",
            "format": "JSON API",
            "canonical_entity": "PopulationDenominator",
            "consumers": "Indicator engine; incidence/mortality denominators",
            "mvp_status": "implemented above",
        },
        {
            "source": "IBGE Malhas",
            "grain": "territory geometry",
            "format": "GeoJSON API",
            "canonical_entity": "TerritoryGeometry",
            "consumers": "Dashboard map layer",
            "mvp_status": "implemented above for one municipality",
        },
        {
            "source": "CNES",
            "grain": "facility-month or facility snapshot",
            "format": "TabNet export CSV or DBC/DBF converted to CSV/Parquet",
            "canonical_entity": "Facility",
            "consumers": "Recommendation engine; capacity context; dashboards",
            "mvp_status": "manual CSV/converted file first",
        },
        {
            "source": "SISAB/e-Gestor APS",
            "grain": "territory-period APS aggregate",
            "format": "public report export CSV/XLSX/ODS when available",
            "canonical_entity": "ApsContextAggregate",
            "consumers": "APS context; recommendation engine",
            "mvp_status": "optional enrichment",
        },
        {
            "source": "SIH/SUS",
            "grain": "territory-period hospitalization aggregate",
            "format": "TabNet export CSV or DBC/DBF converted to CSV/Parquet",
            "canonical_entity": "HospitalizationAggregate",
            "consumers": "Severity context; dashboards",
            "mvp_status": "optional enrichment",
        },
    ]
)
data_contracts



# %% [markdown]
## Amostras DATASUS por codigo
#
# Esta secao tenta baixar poucos arquivos publicos `.dbc` diretamente do DATASUS para inspecao visual no notebook. Ela usa o protocolo `ftp://`, porque o host `ftp.datasus.gov.br` pode nao responder bem por `https://`.
#
# Ela nao substitui a ingestao definitiva: os nomes dos arquivos podem mudar por sistema, ano e UF, e alguns servidores podem ficar lentos ou indisponiveis. No SINAN-TB, o FTP publico disponibiliza arquivos nacionais `TUBEBRYY.dbc`; o recorte Ceara deve ser filtrado depois da leitura.
#
# Para transformar `.dbc` em `DataFrame`, o notebook converte DBC para DBF e depois carrega o DBF. Instale as dependencias do notebook:
#
# ```bash
# python -m pip install -r requirements-notebook.txt
# ```
#
# Se algum download falhar, a celula apenas registra o erro e segue para a proxima fonte.
#

# %%
DATASUS_SAMPLE_DIR = PUBLIC_CACHE_DIR / "datasus_samples"
DATASUS_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

DATASUS_SAMPLE_SOURCES = [
    {
        "name": "sim_ce_2023",
        "label": "SIM obitos CE 2023",
        "canonical_entity": "MortalityAggregate",
        "candidate_urls": [
            "ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DOCE2023.dbc",
        ],
        "tb_filter_column": "CAUSABAS",
        "tb_filter_prefixes": ("A15", "A16", "A17", "A18", "A19"),
    },
    {
        "name": "sih_ce_2024_01",
        "label": "SIH/SUS AIH reduzida CE jan/2024",
        "canonical_entity": "HospitalizationAggregate",
        "candidate_urls": [
            "ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/RDCE2401.dbc",
        ],
        "tb_filter_column": "DIAG_PRINC",
        "tb_filter_prefixes": ("A15", "A16", "A17", "A18", "A19"),
    },
    {
        "name": "cnes_st_ce_2024_01",
        "label": "CNES estabelecimentos CE jan/2024",
        "canonical_entity": "Facility",
        "candidate_urls": [
            "ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/ST/STCE2401.dbc",
        ],
    },
    {
        "name": "sinan_tb_br_2023",
        "label": "SINAN-TB Brasil 2023, filtrar CE apos leitura",
        "canonical_entity": "CaseAggregate",
        "candidate_urls": [
            "ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/PRELIM/TUBEBR23.dbc",
            "ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/TUBEBR19.dbc",
        ],
    },
]


def download_ftp_file(url: str, destination: Path, timeout: int, max_bytes: int) -> None:
    """Baixa arquivo FTP publico DATASUS usando ftplib em vez de urllib."""
    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError(f"missing FTP host in {url}")

    remote_path = parsed.path.lstrip("/")
    directory, file_name = remote_path.rsplit("/", 1)
    tmp_path = destination.with_suffix(destination.suffix + ".part")
    total = 0

    with ftplib.FTP(parsed.hostname, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(directory)
        size = ftp.size(file_name)
        if size is not None and size > max_bytes:
            raise ValueError(f"file exceeded {max_bytes:,} bytes: {size:,} bytes")

        with tmp_path.open("wb") as output:
            def write_chunk(chunk: bytes) -> None:
                nonlocal total
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"file exceeded {max_bytes:,} bytes")
                output.write(chunk)

            ftp.retrbinary(f"RETR {file_name}", write_chunk)

    tmp_path.replace(destination)


def fetch_binary_file(
    candidate_urls: list[str],
    cache_name: str,
    timeout: int = 45,
    max_bytes: int = 30_000_000,
) -> tuple[Path, str] | None:
    """Baixa o primeiro arquivo disponivel entre URLs candidatas, com cache local."""
    cache_path = DATASUS_SAMPLE_DIR / cache_name
    if cache_path.exists():
        print(f"cached: {cache_path.relative_to(PROJECT_ROOT)}")
        return cache_path, "cache"

    for url in candidate_urls:
        try:
            if url.startswith("ftp://"):
                download_ftp_file(url, cache_path, timeout=timeout, max_bytes=max_bytes)
            else:
                request = Request(url, headers={"User-Agent": "TB-IA exploratory notebook"})
                with urlopen(request, timeout=timeout) as response:
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > max_bytes:
                        print(f"skip large file: {url} ({int(content_length):,} bytes)")
                        continue

                    chunks = []
                    total = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        chunks.append(chunk)
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError(f"file exceeded {max_bytes:,} bytes")

                cache_path.write_bytes(b"".join(chunks))

            print(f"downloaded: {cache_path.relative_to(PROJECT_ROOT)} from {url}")
            return cache_path, url
        except (HTTPError, URLError, TimeoutError, ValueError, ftplib.Error) as exc:
            partial_path = cache_path.with_suffix(cache_path.suffix + ".part")
            if partial_path.exists():
                partial_path.unlink()
            print(f"could not download {url}: {type(exc).__name__}: {exc}")

    print(f"not downloaded: {cache_name}")
    return None


def read_dbc_dataframe(path: Path) -> pd.DataFrame | None:
    """Converte DBC para DBF e carrega em DataFrame quando as dependencias existem."""
    try:
        import pyreaddbc
        from dbfread import DBF
    except ImportError:
        print("DBC reader not installed. Run: python -m pip install -r requirements-notebook.txt")
        return None

    dbf_path = path.with_suffix(".dbf")
    if not dbf_path.exists():
        pyreaddbc.dbc2dbf(str(path), str(dbf_path))

    table = DBF(str(dbf_path), encoding="latin1", char_decode_errors="ignore")
    df = pd.DataFrame(iter(table))
    df.columns = [str(col).strip() for col in df.columns]
    return df


datasus_downloads = []
for source in DATASUS_SAMPLE_SOURCES:
    downloaded = fetch_binary_file(source["candidate_urls"], f"{source['name']}.dbc")
    if downloaded is None:
        datasus_downloads.append(
            {
                "source": source["label"],
                "canonical_entity": source["canonical_entity"],
                "status": "not downloaded",
                "path": None,
                "bytes": None,
            }
        )
        continue

    path, url = downloaded
    datasus_downloads.append(
        {
            "source": source["label"],
            "canonical_entity": source["canonical_entity"],
            "status": "downloaded",
            "path": str(path.relative_to(PROJECT_ROOT)),
            "bytes": path.stat().st_size,
            "url": url,
        }
    )

datasus_downloads_df = pd.DataFrame(datasus_downloads)
display(datasus_downloads_df)


# %%
# Mostra a estrutura dos arquivos DBC baixados. Para fontes grandes, isso ainda le o arquivo inteiro,
# mas exibe apenas colunas, dimensoes e as primeiras linhas.
for source in DATASUS_SAMPLE_SOURCES:
    path = DATASUS_SAMPLE_DIR / f"{source['name']}.dbc"
    if not path.exists():
        continue

    print(f"\n{source['label']} -> {path.relative_to(PROJECT_ROOT)}")
    df = read_dbc_dataframe(path)
    if df is None:
        continue

    print(f"rows={len(df):,} columns={len(df.columns):,}")
    print("columns:", ", ".join(df.columns[:40]))
    display(df.head())

    filter_column = source.get("tb_filter_column")
    prefixes = source.get("tb_filter_prefixes")
    if filter_column in df.columns and prefixes:
        tb_df = df[df[filter_column].astype(str).str.startswith(prefixes, na=False)]
        print(f"TB filter {filter_column} startswith {prefixes}: rows={len(tb_df):,}")
        display(tb_df.head())


# %% [markdown]
## Fallback TabNet agregado
#
# Quando o FTP de arquivos DBC do DATASUS falhar, ainda da para visualizar dados agregados via TabNet. Esta rota usa o formulario publico SINAN-TB do Ceara e pede saida em formato `prn`, que vem como texto separado por `;` dentro do HTML.
#
# Isto e apenas para exploracao e validacao visual. Para ingestao robusta, ainda e melhor usar DBC/DBF ou exportacoes controladas.
#

# %%
TABNET_SINAN_TB_CE_URL = "http://tabnet.datasus.gov.br/cgi/tabcgi.exe?sinannet/cnv/tubercce.def"


def fetch_text(
    url: str,
    cache_name: str,
    data: dict[str, str] | None = None,
    encoding: str = "iso-8859-1",
    timeout: int = 45,
    refresh: bool = False,
) -> str:
    cache_path = PUBLIC_CACHE_DIR / cache_name
    if cache_path.exists() and not refresh:
        return cache_path.read_text(encoding=encoding)

    body = None
    if data is not None:
        body = urlencode(data, encoding=encoding).encode("ascii")

    request = Request(
        url,
        data=body,
        headers={
            "User-Agent": "TB-IA exploratory notebook",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        text = response.read().decode(encoding, errors="replace")
    cache_path.write_text(text, encoding=encoding)
    return text


def parse_tabnet_prn(html_text: str) -> pd.DataFrame:
    if "<PRE>" not in html_text or "</PRE>" not in html_text:
        raise ValueError("TabNet response did not contain a PRN <PRE> block")

    pre_block = html_text.split("<PRE>", 1)[1].split("</PRE>", 1)[0]
    lines = [
        unescape(line.strip())
        for line in pre_block.splitlines()
        if line.strip() and line.strip() != "&"
    ]
    rows = list(csv.reader(StringIO("\n".join(lines)), delimiter=";"))
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows[1:], columns=rows[0])
    for column in df.columns[1:]:
        normalized = df[column].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        numeric = pd.to_numeric(normalized, errors="coerce")
        if numeric.notna().any():
            df[column] = numeric.astype("Int64")
    return df


def fetch_tabnet_sinan_tb_ce(
    line: str,
    file_name: str = "tubece23.dbf",
    cache_slug: str | None = None,
) -> pd.DataFrame | None:
    cache_slug = cache_slug or line.lower().replace(" ", "_")
    params = {
        "Linha": line,
        "Coluna": "--Não-Ativa--",
        "Incremento": "Casos_confirmados",
        "Arquivos": file_name,
        "formato": "prn",
        "mostre": "Mostra",
    }
    try:
        html_text = fetch_text(
            TABNET_SINAN_TB_CE_URL,
            f"tabnet_sinan_tb_ce_{cache_slug}_{file_name}.html",
            data=params,
            encoding="iso-8859-1",
        )
        return parse_tabnet_prn(html_text)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"could not fetch TabNet sample {line}: {type(exc).__name__}: {exc}")
        return None


tabnet_samples = {
    "cases_by_residence_municipality": fetch_tabnet_sinan_tb_ce(
        "Município_de_residência",
        cache_slug="municipio_residencia",
    ),
    "cases_by_form": fetch_tabnet_sinan_tb_ce("Forma", cache_slug="forma"),
    "cases_by_entry_type": fetch_tabnet_sinan_tb_ce(
        "Tipo_de_entrada__",
        cache_slug="tipo_entrada",
    ),
}

for sample_name, df in tabnet_samples.items():
    if df is None:
        continue
    print(f"\n{sample_name}: rows={len(df):,} columns={len(df.columns):,}")
    display(df.head(15))


# %%
# Exemplo de grafico com a amostra agregada do TabNet.
municipal_cases = tabnet_samples.get("cases_by_residence_municipality")
if municipal_cases is not None and "Casos confirmados" in municipal_cases.columns:
    plot_df = municipal_cases[municipal_cases.iloc[:, 0] != "Total"].copy()
    plot_df = plot_df.sort_values("Casos confirmados", ascending=False).head(15)

    ax = plot_df.sort_values("Casos confirmados").plot.barh(
        x=plot_df.columns[0],
        y="Casos confirmados",
        figsize=(8, 6),
        legend=False,
        color="#B54434",
    )
    ax.set_title("SINAN-TB CE 2023: casos confirmados por municipio de residencia")
    ax.set_xlabel("Casos confirmados")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.show()

# %% [markdown]
## Entrada opcional para CSVs DATASUS/CNES/SINAN/SIM
#
# Coloque arquivos exportados manualmente ou convertidos de DBC/DBF em `data/raw/manual/`.
#
# Nomes esperados por este notebook:
#
# - `sinan_tb_tabnet.csv`
# - `sim_tb_tabnet.csv`
# - `cnes_estabelecimentos.csv`
# - `sih_tb_tabnet.csv`
# - `sisab_aps.csv`
#
# Links uteis para exportacao manual:
#
# - SINAN-TB Ceara TabNet: <http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sinannet/cnv/tubercce.def>
# - DATASUS transferencia de arquivos: <https://datasus.saude.gov.br/transferencia-de-arquivos/>
#
# A primeira versao do projeto deve aceitar CSVs manuais antes de automatizar POSTs do TabNet ou conversao de DBC.
#

# %%
def read_optional_csv(file_name: str) -> pd.DataFrame | None:
    path = MANUAL_DIR / file_name
    if not path.exists():
        print(f"not found: {path.relative_to(PROJECT_ROOT)}")
        return None

    for encoding in ["utf-8", "latin1"]:
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=encoding)
            df.columns = [str(col).strip() for col in df.columns]
            print(f"loaded: {path.relative_to(PROJECT_ROOT)} rows={len(df):,} columns={len(df.columns)}")
            return df
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"could not decode {path}")

sinan_tb = read_optional_csv("sinan_tb_tabnet.csv")
sim_tb = read_optional_csv("sim_tb_tabnet.csv")
cnes = read_optional_csv("cnes_estabelecimentos.csv")
sih_tb = read_optional_csv("sih_tb_tabnet.csv")
sisab_aps = read_optional_csv("sisab_aps.csv")


# %%
# Visualizacao generica para qualquer CSV opcional carregado.
# Se o arquivo tiver colunas numericas, mostra as maiores somas por coluna.
for name, df in {
    "sinan_tb": sinan_tb,
    "sim_tb": sim_tb,
    "cnes": cnes,
    "sih_tb": sih_tb,
    "sisab_aps": sisab_aps,
}.items():
    if df is None:
        continue
    display(df.head())
    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        totals = numeric.sum(numeric_only=True).sort_values(ascending=False).head(10)
        ax = totals.sort_values().plot.barh(figsize=(8, 4), color="#7353BA")
        ax.set_title(f"{name}: maiores somas numericas")
        ax.set_xlabel("soma")
        plt.tight_layout()
        plt.show()


# %% [markdown]
## Estrutura analitica esperada
#
# Para o MVP 1, a ingestao real deve convergir para tabelas canonicas. Esta celula cria exemplos vazios com os campos esperados. Use isso como contrato para transformar CSVs brutos em dados consumidos pelo indicador engine.
#

# %%
canonical_tables = {
    "Territory": [
        "territory_id",
        "territory_name",
        "territory_level",
        "parent_territory_id",
        "ibge_code",
    ],
    "PopulationDenominator": [
        "territory_id",
        "year",
        "sex",
        "age_group",
        "population",
        "source_id",
        "import_run_id",
    ],
    "CaseAggregate": [
        "territory_id",
        "period",
        "territory_role",
        "case_form",
        "entry_type",
        "sex",
        "age_group",
        "race_color",
        "education_level",
        "vulnerability_group",
        "lab_confirmation_status",
        "hiv_test_status",
        "hiv_result",
        "contact_investigation_status",
        "tdo_status",
        "closure_status",
        "count",
        "source_id",
        "import_run_id",
    ],
    "MortalityAggregate": [
        "territory_id",
        "period",
        "cid10_group",
        "sex",
        "age_group",
        "race_color",
        "death_count",
        "source_id",
        "import_run_id",
    ],
    "Facility": [
        "facility_id",
        "cnes_id",
        "facility_name",
        "territory_id",
        "facility_type",
        "management_type",
        "has_sus_service",
        "source_id",
        "import_run_id",
    ],
}

for table, columns in canonical_tables.items():
    print(f"{table}: {', '.join(columns)}")


# %% [markdown]
## Primeiro indicador calculavel quando houver CSV de casos
#
# Quando `data/raw/manual/tb_indicadores_municipais.csv` existir com as colunas abaixo, o notebook calcula incidencia e mortalidade rapidamente:
#
# - `municipality_id`
# - `municipality_name`
# - `year`
# - `new_cases`
# - `deaths`
# - `population`
#
# Esse arquivo pode ser montado manualmente a partir do TabNet enquanto a ingestao automatica ainda nao existe.
#

# %%
indicator_input = read_optional_csv("tb_indicadores_municipais.csv")
if indicator_input is not None:
    required = {"municipality_id", "municipality_name", "year", "new_cases", "deaths", "population"}
    missing = required - set(indicator_input.columns)
    if missing:
        raise ValueError(f"missing columns in tb_indicadores_municipais.csv: {sorted(missing)}")

    indicators = indicator_input.copy()
    indicators["tb_incidence_per_100k"] = indicators["new_cases"] / indicators["population"] * 100_000
    indicators["tb_mortality_per_100k"] = indicators["deaths"] / indicators["population"] * 100_000
    display(indicators.sort_values("tb_incidence_per_100k", ascending=False).head(20))

    ax = indicators.sort_values("tb_incidence_per_100k").plot.barh(
        x="municipality_name",
        y="tb_incidence_per_100k",
        figsize=(8, 6),
        color="#B54434",
        legend=False,
    )
    ax.set_title("Incidencia de TB por 100 mil habitantes")
    ax.set_xlabel("casos novos / 100 mil hab.")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.show()


# %% [markdown]
## Proximos passos
#
# 1. Exportar uma tabela pequena do TabNet SINAN-TB para `data/raw/manual/sinan_tb_tabnet.csv`.
# 2. Exportar ou montar `tb_indicadores_municipais.csv` para validar incidencia e mortalidade contra o Boletim 2026.
# 3. Decidir se a ingestao DATASUS inicial sera por CSV exportado do TabNet ou por arquivos DBC convertidos.
# 4. Criar transformadores para preencher `CaseAggregate`, `MortalityAggregate`, `Facility` e `IndicatorValue`.
#
