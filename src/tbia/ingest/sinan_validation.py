from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tbia.ingest.datasus_transforms import record_text, record_year

Record = Mapping[str, Any]

REPORT_STATUS = "technical_audit_pending_domain_review"
SINAN_VALIDATION_FIELDS = (
    "TRATAMENTO",
    "SITUA_ENCE",
    "FORMA",
    "HIV",
    "AGRAVAIDS",
    "BACILOSC_E",
    "CULTURA_ES",
    "RIFAMPICIN",
)

CURRENT_MAPPING_EFFECTS: dict[str, dict[str, str]] = {
    "TRATAMENTO": {
        "1": "counted as new case",
        "2": "counted as retreatment",
        "3": "counted as retreatment",
    },
    "SITUA_ENCE": {
        "1": "counted as cure and closed case",
        "2": "counted as treatment interruption and closed case",
        "3": "counted as closed case only",
        "4": "counted as closed case only",
        "5": "counted as closed case only",
        "7": "counted as closed case only",
        "8": "counted as closed case only",
        "9": "counted as closed case only",
        "10": "counted as closed case only",
    },
    "FORMA": {
        "1": "counted as pulmonary",
        "2": "not counted as pulmonary",
        "3": "counted as pulmonary",
    },
    "HIV": {
        "1": "counted as HIV tested and TB-HIV burden",
        "2": "counted as HIV tested",
        "3": "not counted as HIV tested",
        "4": "not counted as HIV tested",
    },
    "AGRAVAIDS": {
        "1": "counted as TB-HIV burden",
        "2": "not counted as TB-HIV burden",
        "9": "not counted as TB-HIV burden",
    },
    "BACILOSC_E": {
        "1": "counted as laboratory confirmation",
        "2": "not counted as laboratory confirmation",
        "3": "not counted as laboratory confirmation",
        "4": "not counted as laboratory confirmation",
    },
    "CULTURA_ES": {
        "1": "counted as laboratory confirmation and culture use among retreatment",
        "2": "counted as culture use among retreatment only",
        "3": "not counted as laboratory confirmation",
        "4": "not counted as laboratory confirmation",
    },
    "RIFAMPICIN": {
        "1": "counted as TRM-TB use and laboratory confirmation",
        "2": "counted as TRM-TB use and laboratory confirmation",
        "": "not counted as TRM-TB use",
    },
}

FIELD_CAVEATS: dict[str, str] = {
    "TRATAMENTO": (
        "Current effects must be compared with the official SINAN-TB entry-type dictionary."
    ),
    "SITUA_ENCE": (
        "Current effects must be compared with the official closure-status dictionary "
        "and cohort definition."
    ),
    "FORMA": (
        "Current effects assume pulmonary and mixed forms are included in pulmonary indicators."
    ),
    "HIV": "Current effects distinguish tested from not tested using provisional code categories.",
    "AGRAVAIDS": (
        "Current effects combine AIDS comorbidity with HIV-positive result for TB-HIV burden."
    ),
    "BACILOSC_E": "Current effects use initial sputum smear as one lab-confirmation component.",
    "CULTURA_ES": (
        "Current effects treat culture performed for retreatment separately from culture "
        "positivity."
    ),
    "RIFAMPICIN": "Current effects use nonblank rifampicin testing as a TRM-TB use proxy.",
}


def build_sinan_mapping_report(
    records: Iterable[Record],
    *,
    year: int,
    uf_code: str,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    counters = {field: Counter[str]() for field in SINAN_VALIDATION_FIELDS}
    record_count = 0

    for record in records:
        if record_year(record.get("NU_ANO")) != year:
            continue
        if not record_text(record, "ID_MN_RESI").startswith(uf_code):
            continue
        record_count += 1
        for field in SINAN_VALIDATION_FIELDS:
            counters[field][record_text(record, field)] += 1

    timestamp = generated_at or datetime.now(UTC)
    return {
        "status": REPORT_STATUS,
        "generated_at": timestamp.isoformat(),
        "scope": {"year": year, "uf_code": uf_code},
        "record_count": record_count,
        "fields": [field_report(field, counters[field]) for field in SINAN_VALIDATION_FIELDS],
        "caveats": [
            "This is a technical audit of current transform effects, not an official validation.",
            (
                "A domain reviewer must compare these effects with official SINAN-TB "
                "dictionaries and indicator handbooks before official use."
            ),
        ],
    }


def field_report(field: str, counter: Counter[str]) -> dict[str, Any]:
    mapping = CURRENT_MAPPING_EFFECTS[field]
    frequencies = [
        {
            "value": display_value(value),
            "count": count,
            "mapped": value in mapping,
            "current_effect": mapping.get(value, "unmapped by current transform"),
        }
        for value, count in sorted(counter.items(), key=lambda item: display_value(item[0]))
    ]
    return {
        "field": field,
        "mapped_codes": {display_value(key): value for key, value in mapping.items()},
        "unmapped_values": [
            display_value(value) for value in sorted(counter) if value not in mapping
        ],
        "frequencies": frequencies,
        "caveat": FIELD_CAVEATS[field],
    }


def display_value(value: str) -> str:
    return "<blank>" if value == "" else value


def write_sinan_mapping_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    year = report["scope"]["year"]
    uf_code = report["scope"]["uf_code"]
    output_path = output_dir / f"sinan_mapping_audit_{uf_code}_{year}.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
