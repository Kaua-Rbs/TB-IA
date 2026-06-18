from __future__ import annotations

import sys
from pathlib import Path

from scripts.quality_lib import analyze_file_sizes, dependency_report


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command == "complexity":
        run_complexity_report()
        return 0
    if command == "deps":
        return run_dependency_report()
    if command == "mutation":
        return run_mutation_report()

    print("Usage: python scripts/quality_gates.py <complexity|deps|mutation>", file=sys.stderr)
    return 1


def run_complexity_report() -> None:
    largest_files = analyze_file_sizes(Path.cwd())

    print("Largest source/documentation files by line count:")
    for record in largest_files:
        print(f"{record.lines:>5} {record.file}")

    print("Cyclomatic complexity for Python tooling is reported by radon.")


def run_dependency_report() -> int:
    report = dependency_report(Path.cwd())

    print(f"Checked {len(report.files)} local Python tooling files for import cycles.")

    if report.application_roots:
        print(f"Application roots detected: {', '.join(report.application_roots)}")
    else:
        print(
            "No application source roots found yet; "
            "architecture rules are limited to tooling imports."
        )

    if report.cycles:
        for cycle in report.cycles:
            print(f"Import cycle: {' -> '.join(cycle)}", file=sys.stderr)
        return 1

    print("No local Python import cycles found.")
    return 0


def run_mutation_report() -> int:
    report = dependency_report(Path.cwd())

    if not report.application_roots:
        print("Mutation testing skipped: no critical application source root exists yet.")
        print("Add mutmut or another Python mutation tool when domain rules or risk logic exist.")
        return 0

    print(
        "Application source exists, but mutation testing is not configured for it yet.",
        file=sys.stderr,
    )
    print(
        "Add mutmut or the appropriate mutation tool for the selected Python package layout.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
