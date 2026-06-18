from __future__ import annotations

from pathlib import Path

from scripts.quality_lib import (
    REQUIRED_AGENT_SECTIONS,
    dependency_report,
    detect_application_roots,
    find_local_imports,
    find_trailing_whitespace_lines,
    validate_documentation,
)


def test_validate_documentation_accepts_expected_baseline(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text(agent_document(), encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text(
        "# Contributing\n\nRun `make check`.\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Project\n\nRun `make check`.\n", encoding="utf-8")
    (tmp_path / "descricao_do_projeto.md").write_text(
        "# Descricao\n\nProjeto.\n",
        encoding="utf-8",
    )
    (tmp_path / "frentes_de_desenvolvimento.md").write_text(
        "# Frentes\n\nPlano.\n",
        encoding="utf-8",
    )

    result = validate_documentation(tmp_path)

    assert result.errors == []
    assert result.stats.markdown_files == 5


def test_validate_documentation_reports_missing_agent_sections_and_whitespace(
    tmp_path: Path,
) -> None:
    (tmp_path / "AGENTS.md").write_text(
        "# Agents\n\n## Project Overview\n\nText.\n",
        encoding="utf-8",
    )
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n\nNo command.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project\n\nRun `make check`. \n", encoding="utf-8")
    (tmp_path / "descricao_do_projeto.md").write_text(
        "# Descricao\n\nProjeto.\n",
        encoding="utf-8",
    )
    (tmp_path / "frentes_de_desenvolvimento.md").write_text(
        "# Frentes\n\nPlano.\n",
        encoding="utf-8",
    )

    result = validate_documentation(tmp_path)

    assert any("AGENTS.md is missing section" in error for error in result.errors)
    assert any("CONTRIBUTING.md" in error for error in result.errors)
    assert any("trailing whitespace" in error for error in result.errors)


def test_find_local_imports_returns_python_imports() -> None:
    imports = find_local_imports(
        "\n".join(
            [
                "import os",
                "import scripts.quality_lib",
                "from pathlib import Path",
                "from .quality_lib import validate_documentation",
                "from ..helpers import value",
            ]
        )
    )

    assert imports == [
        "os",
        "scripts.quality_lib",
        "pathlib",
        "pathlib.Path",
        ".quality_lib",
        "..helpers",
    ]


def test_find_trailing_whitespace_lines_reports_affected_line_numbers() -> None:
    assert find_trailing_whitespace_lines("ok\nbad \n\t\n") == [2, 3]


def test_dependency_report_detects_local_import_cycles(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "__init__.py").write_text("", encoding="utf-8")
    (scripts / "a.py").write_text("from scripts import b\n", encoding="utf-8")
    (scripts / "b.py").write_text("from scripts import a\n", encoding="utf-8")

    report = dependency_report(tmp_path)

    assert len(report.cycles) == 1
    assert report.cycles[0] == ["scripts/a.py", "scripts/b.py", "scripts/a.py"]


def test_detect_application_roots_ignores_tooling_and_detects_future_source_roots() -> None:
    roots = detect_application_roots(
        ["scripts/tool.py", "src/index.py", "backend/app.py", "README.md"]
    )

    assert roots == ["backend", "src"]


def agent_document() -> str:
    sections = "".join(f"## {section}\n\nText.\n\n" for section in REQUIRED_AGENT_SECTIONS)
    return f"# Codex Project Instructions\n\n{sections}"
