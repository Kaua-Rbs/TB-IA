from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from ftplib import FTP
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from tbia.geography import BRAZIL_SCOPE, ufs_for_scope


@dataclass(frozen=True)
class DatasusFile:
    source_id: str
    label: str
    host: str
    remote_path: str
    local_name: str

    @property
    def ftp_url(self) -> str:
        return f"ftp://{self.host}/{self.remote_path}"


DATASUS_DEMO_FILES: tuple[DatasusFile, ...] = ()


def datasus_demo_files(
    uf: str,
    year: int,
    *,
    sih_months: Sequence[int] = (1,),
    cnes_month: int = 12,
) -> tuple[DatasusFile, ...]:
    scope = uf.upper()
    year_suffix = str(year)[-2:]
    sinan_file = DatasusFile(
        source_id="sinan_tb",
        label=f"SINAN-TB Brazil {year} preliminary",
        host="ftp.datasus.gov.br",
        remote_path=f"dissemin/publicos/SINAN/DADOS/PRELIM/TUBEBR{year_suffix}.dbc",
        local_name=f"sinan_tb_br_{year}.dbc",
    )
    if scope == BRAZIL_SCOPE:
        files: list[DatasusFile] = [sinan_file]
        for uf_sigla in ufs_for_scope(BRAZIL_SCOPE):
            files.extend(regional_datasus_demo_files(uf_sigla, year, sih_months, cnes_month))
        return tuple(files)
    regional_files = regional_datasus_demo_files(scope, year, sih_months, cnes_month)
    return (regional_files[0], sinan_file, *regional_files[1:])


def regional_datasus_demo_files(
    uf: str,
    year: int,
    sih_months: Sequence[int],
    cnes_month: int,
) -> tuple[DatasusFile, ...]:
    uf_code = uf.upper()
    uf_slug = uf.lower()
    year_suffix = str(year)[-2:]
    files: list[DatasusFile] = [
        DatasusFile(
            source_id="sim",
            label=f"SIM deaths {uf_code} {year}",
            host="ftp.datasus.gov.br",
            remote_path=f"dissemin/publicos/SIM/CID10/DORES/DO{uf_code}{year}.dbc",
            local_name=f"sim_{uf_slug}_{year}.dbc",
        )
    ]
    files.extend(
        DatasusFile(
            source_id="sih_sus",
            label=f"SIH/SUS reduced AIH {uf_code} {year}-{format_month(month)}",
            host="ftp.datasus.gov.br",
            remote_path=(
                "dissemin/publicos/SIHSUS/200801_/Dados/"
                f"RD{uf_code}{year_suffix}{format_month(month)}.dbc"
            ),
            local_name=f"sih_{uf_slug}_{year}_{format_month(month)}.dbc",
        )
        for month in sih_months
    )
    files.append(
        DatasusFile(
            source_id="cnes",
            label=f"CNES establishments {uf_code} {year}-{format_month(cnes_month)}",
            host="ftp.datasus.gov.br",
            remote_path=(
                "dissemin/publicos/CNES/200508_/Dados/ST/"
                f"ST{uf_code}{year_suffix}{format_month(cnes_month)}.dbc"
            ),
            local_name=f"cnes_st_{uf_slug}_{year}_{format_month(cnes_month)}.dbc",
        )
    )
    return tuple(files)


def format_month(month: int) -> str:
    if month < 1 or month > 12:
        raise ValueError(f"month must be between 1 and 12: {month}")
    return f"{month:02d}"


DATASUS_DEMO_FILES = datasus_demo_files("CE", 2023)


def download_datasus_file(file: DatasusFile, output_dir: Path, *, timeout: int = 60) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / file.local_name
    remote_dir, remote_name = file.remote_path.rsplit("/", maxsplit=1)

    with FTP(file.host, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(remote_dir)
        with output_path.open("wb") as output:
            ftp.retrbinary(f"RETR {remote_name}", output.write)

    return output_path


def read_datasus_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".dbf":
        return read_dbf_records(path)
    if path.suffix.lower() == ".dbc":
        return read_dbc_records(path)
    raise ValueError(f"unsupported DATASUS file format: {path}")


def read_dbf_records(path: Path) -> list[dict[str, Any]]:
    try:
        from dbfread import DBF
    except ImportError as exc:
        raise RuntimeError(
            "Reading DBF files requires dbfread. Install application dependencies."
        ) from exc

    table = DBF(path, load=False, encoding="latin1", char_decode_errors="ignore")
    return [dict(record) for record in table]


def read_dbc_records(path: Path) -> list[dict[str, Any]]:
    try:
        import pyreaddbc
    except ImportError as exc:
        raise RuntimeError(
            "Reading DBC files requires pyreaddbc. Install application dependencies, "
            "or use converted DBF files."
        ) from exc

    with TemporaryDirectory() as tmp_dir:
        dbf_path = Path(tmp_dir) / f"{path.stem}.dbf"
        pyreaddbc.dbc2dbf(str(path), str(dbf_path))
        return read_dbf_records(dbf_path)
