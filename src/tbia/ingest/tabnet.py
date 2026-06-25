from __future__ import annotations

import csv
import io
import re

PRE_BLOCK_PATTERN = re.compile(r"<pre[^>]*>(.*?)</pre>", re.IGNORECASE | re.DOTALL)


def parse_tabnet_prn_html(html: str) -> list[dict[str, str]]:
    match = PRE_BLOCK_PATTERN.search(html)
    if match is None:
        raise ValueError("TabNet response did not contain a PRN <PRE> block")
    return parse_tabnet_prn_text(match.group(1))


def parse_tabnet_prn_text(text: str) -> list[dict[str, str]]:
    cleaned_lines = [
        line.strip()
        for line in text.replace("&nbsp;", " ").splitlines()
        if line.strip() and not line.startswith("Fonte:")
    ]
    reader = csv.DictReader(io.StringIO("\n".join(cleaned_lines)), delimiter=";")
    return [dict(row) for row in reader]
