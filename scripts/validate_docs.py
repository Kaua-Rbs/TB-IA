from __future__ import annotations

import sys
from pathlib import Path

from scripts.quality_lib import validate_documentation


def main() -> int:
    result = validate_documentation(Path.cwd())

    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if result.errors:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        "Documentation checks passed for "
        f"{result.stats.files_checked} text files and "
        f"{result.stats.markdown_files} Markdown files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
