from __future__ import annotations

BRAZIL_SCOPE = "BR"

UF_CODES: dict[str, str] = {
    "AC": "12",
    "AL": "27",
    "AP": "16",
    "AM": "13",
    "BA": "29",
    "CE": "23",
    "DF": "53",
    "ES": "32",
    "GO": "52",
    "MA": "21",
    "MT": "51",
    "MS": "50",
    "MG": "31",
    "PA": "15",
    "PB": "25",
    "PR": "41",
    "PE": "26",
    "PI": "22",
    "RJ": "33",
    "RN": "24",
    "RS": "43",
    "RO": "11",
    "RR": "14",
    "SC": "42",
    "SP": "35",
    "SE": "28",
    "TO": "17",
}

UF_SIGLAS: tuple[str, ...] = tuple(UF_CODES)


def normalize_geographic_scope(uf: str) -> str:
    scope = uf.upper()
    if scope == BRAZIL_SCOPE or scope in UF_CODES:
        return scope
    raise ValueError(f"unsupported geographic scope: {uf}")


def uf_code_for(uf: str) -> str:
    scope = normalize_geographic_scope(uf)
    if scope == BRAZIL_SCOPE:
        return ""
    return UF_CODES[scope]


def is_brazil_scope(uf: str) -> bool:
    return normalize_geographic_scope(uf) == BRAZIL_SCOPE


def ufs_for_scope(uf: str) -> tuple[str, ...]:
    scope = normalize_geographic_scope(uf)
    if scope == BRAZIL_SCOPE:
        return UF_SIGLAS
    return (scope,)
