from __future__ import annotations

import sys
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from scripts import quality_gates, validate_docs


def test_validate_docs_main_reports_success(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    write_documentation_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = validate_docs.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Documentation checks passed" in captured.out
    assert "No application source root found yet" in captured.err


def test_validate_docs_main_reports_errors(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = validate_docs.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Missing required documentation file" in captured.err


def test_quality_gates_main_rejects_unknown_command(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["quality_gates.py", "unknown"])

    exit_code = quality_gates.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Usage:" in captured.err


def test_quality_gates_main_dispatches_complexity(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["quality_gates.py", "complexity"])

    exit_code = quality_gates.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Largest source/documentation files" in captured.out


def test_quality_gates_dependency_report_handles_cycles(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "__init__.py").write_text("", encoding="utf-8")
    (scripts / "a.py").write_text("from scripts import b\n", encoding="utf-8")
    (scripts / "b.py").write_text("from scripts import a\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = quality_gates.run_dependency_report()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Import cycle" in captured.err


def test_quality_gates_mutation_report_is_skipped_without_application_source(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = quality_gates.run_mutation_report()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Mutation testing skipped" in captured.out


def test_quality_gates_mutation_report_requires_configuration_for_application_source(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = quality_gates.run_mutation_report()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "mutation testing is not configured" in captured.err


def write_documentation_baseline(root: Path) -> None:
    agent_sections = "\n".join(
        [
            "## Project Overview",
            "## Repository Structure",
            "## Setup Commands",
            "## Development Commands",
            "## Test Commands",
            "## Quality Gates",
            "## Architecture Rules",
            "## Definition Of Done",
            "## Rules For Future Codex Sessions",
        ]
    )
    (root / "AGENTS.md").write_text(f"# Agents\n\n{agent_sections}\n", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text("Run `make check`.\n", encoding="utf-8")
    (root / "README.md").write_text("Run `make check`.\n", encoding="utf-8")
    (root / "descricao_do_projeto.md").write_text("# Descricao\n", encoding="utf-8")
    (root / "frentes_de_desenvolvimento.md").write_text("# Frentes\n", encoding="utf-8")
