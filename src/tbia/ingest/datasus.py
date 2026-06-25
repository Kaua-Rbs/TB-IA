from __future__ import annotations

from dataclasses import dataclass
from ftplib import FTP
from pathlib import Path


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


DATASUS_DEMO_FILES: tuple[DatasusFile, ...] = (
    DatasusFile(
        source_id="sim",
        label="SIM deaths CE 2023",
        host="ftp.datasus.gov.br",
        remote_path="dissemin/publicos/SIM/CID10/DORES/DOCE2023.dbc",
        local_name="sim_ce_2023.dbc",
    ),
    DatasusFile(
        source_id="sih_sus",
        label="SIH/SUS reduced AIH CE Jan/2024",
        host="ftp.datasus.gov.br",
        remote_path="dissemin/publicos/SIHSUS/200801_/Dados/RDCE2401.dbc",
        local_name="sih_ce_2024_01.dbc",
    ),
    DatasusFile(
        source_id="cnes",
        label="CNES establishments CE Jan/2024",
        host="ftp.datasus.gov.br",
        remote_path="dissemin/publicos/CNES/200508_/Dados/ST/STCE2401.dbc",
        local_name="cnes_st_ce_2024_01.dbc",
    ),
    DatasusFile(
        source_id="sinan_tb",
        label="SINAN-TB Brazil 2023 preliminary",
        host="ftp.datasus.gov.br",
        remote_path="dissemin/publicos/SINAN/DADOS/PRELIM/TUBEBR23.dbc",
        local_name="sinan_tb_br_2023.dbc",
    ),
)


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


def read_dbc_with_pandas(path: Path) -> object:
    try:
        import pyreaddbc
    except ImportError as exc:
        raise RuntimeError(
            "Reading DBC files requires pyreaddbc. "
            "Install notebook or app dependencies, or use canonical CSV fallback."
        ) from exc

    return pyreaddbc.read_dbc(str(path))
