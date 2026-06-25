from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REQUIRED_AGENT_SECTIONS = [
    "Project Overview",
    "Repository Structure",
    "Setup Commands",
    "Development Commands",
    "Test Commands",
    "Quality Gates",
    "Architecture Rules",
    "Definition Of Done",
    "Rules For Future Codex Sessions",
]

IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "build",
    "data",
    "dist",
    "htmlcov",
    "node_modules",
}

TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

TEXT_FILE_NAMES = {
    ".gitignore",
    "Makefile",
}

SOURCE_EXTENSIONS = {
    ".py",
}

APPLICATION_ROOT_NAMES = {
    "app",
    "backend",
    "client",
    "frontend",
    "packages",
    "server",
    "src",
}

REQUIRED_DOCUMENTATION_FILES = [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "descricao_do_projeto.md",
    "frentes_de_desenvolvimento.md",
]


@dataclass(frozen=True)
class DocumentationStats:
    files_checked: int
    markdown_files: int


@dataclass(frozen=True)
class DocumentationValidation:
    errors: list[str]
    warnings: list[str]
    stats: DocumentationStats


@dataclass(frozen=True)
class FileSizeRecord:
    file: str
    lines: int


@dataclass(frozen=True)
class DependencyReport:
    cycles: list[list[str]]
    files: list[str]
    graph: dict[str, list[str]]
    application_roots: list[str]


def list_files(root_directory: Path) -> list[str]:
    files: list[str] = []

    for path in root_directory.rglob("*"):
        if any(
            part in IGNORED_DIRECTORY_NAMES or part.endswith(".egg-info")
            for part in path.relative_to(root_directory).parts
        ):
            continue
        if path.is_file():
            files.append(to_posix(path.relative_to(root_directory)))

    return sorted(files)


def validate_documentation(root_directory: Path) -> DocumentationValidation:
    files = list_files(root_directory)
    file_set = set(files)
    text_files = [file for file in files if is_text_file(file)]
    errors = [
        *validate_required_documentation_files(file_set),
        *validate_agent_instructions(root_directory, file_set),
        *validate_standard_command_docs(root_directory, file_set),
        *validate_text_file_hygiene(root_directory, text_files),
    ]
    warnings = validate_application_root_warnings(files)

    return DocumentationValidation(
        errors=errors,
        warnings=warnings,
        stats=build_documentation_stats(text_files),
    )


def analyze_file_sizes(root_directory: Path, limit: int = 20) -> list[FileSizeRecord]:
    records: list[FileSizeRecord] = []

    for file in (file for file in list_files(root_directory) if is_text_file(file)):
        contents = read_text_file(root_directory, file)
        records.append(FileSizeRecord(file=file, lines=count_lines(contents)))

    return sorted(records, key=lambda record: (-record.lines, record.file))[:limit]


def dependency_report(root_directory: Path) -> DependencyReport:
    files = [file for file in list_files(root_directory) if Path(file).suffix == ".py"]
    file_set = set(files)
    graph: dict[str, list[str]] = {file: [] for file in files}

    for file in files:
        contents = read_text_file(root_directory, file)
        imports = [
            resolved
            for specifier in find_local_imports(contents)
            if (resolved := resolve_local_import(file, specifier, file_set)) is not None
        ]
        graph[file] = imports

    return DependencyReport(
        cycles=find_cycles(graph),
        files=files,
        graph=graph,
        application_roots=detect_application_roots(list_files(root_directory)),
    )


def detect_application_roots(files: list[str]) -> list[str]:
    roots: set[str] = set()

    for file in files:
        first_segment = file.split("/", maxsplit=1)[0]
        if first_segment in APPLICATION_ROOT_NAMES and Path(file).suffix in SOURCE_EXTENSIONS:
            roots.add(first_segment)

    return sorted(roots)


def find_local_imports(contents: str) -> list[str]:
    tree = ast.parse(contents)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.extend(import_from_specifiers(node))

    return imports


def import_from_specifiers(node: ast.ImportFrom) -> list[str]:
    prefix = "." * node.level
    module = node.module or ""

    if node.level > 0 and module:
        return [f"{prefix}{module}"]

    if node.level > 0:
        return [f"{prefix}{alias.name}" for alias in node.names]

    specifiers = [module] if module else []
    specifiers.extend(f"{module}.{alias.name}" for alias in node.names if module)
    return specifiers


def find_trailing_whitespace_lines(contents: str) -> list[int]:
    return [
        index
        for index, line in enumerate(contents.splitlines(), start=1)
        if line.rstrip(" \t") != line
    ]


def validate_required_documentation_files(file_set: set[str]) -> list[str]:
    return [
        f"Missing required documentation file: {file}"
        for file in REQUIRED_DOCUMENTATION_FILES
        if file not in file_set
    ]


def validate_agent_instructions(root_directory: Path, file_set: set[str]) -> list[str]:
    if "AGENTS.md" not in file_set:
        return []

    agents = read_text_file(root_directory, "AGENTS.md")
    return [
        f"AGENTS.md is missing section: {section}"
        for section in REQUIRED_AGENT_SECTIONS
        if f"## {section}" not in agents
    ]


def validate_standard_command_docs(root_directory: Path, file_set: set[str]) -> list[str]:
    checks = [
        ("CONTRIBUTING.md", "CONTRIBUTING.md must document the standard make check command."),
        ("README.md", "README.md must document the standard make check command."),
    ]
    errors: list[str] = []

    for file, error in checks:
        if file in file_set and "make check" not in read_text_file(root_directory, file):
            errors.append(error)

    return errors


def validate_text_file_hygiene(root_directory: Path, text_files: list[str]) -> list[str]:
    errors: list[str] = []

    for file in text_files:
        contents = read_text_file(root_directory, file)

        if not contents.endswith("\n"):
            errors.append(f"{file} must end with a newline.")

        trailing_whitespace_lines = find_trailing_whitespace_lines(contents)
        if trailing_whitespace_lines:
            errors.append(f"{file} has trailing whitespace on line {trailing_whitespace_lines[0]}.")

    return errors


def validate_application_root_warnings(files: list[str]) -> list[str]:
    if detect_application_roots(files):
        return []

    return ["No application source root found yet; code-specific gates remain documented only."]


def build_documentation_stats(text_files: list[str]) -> DocumentationStats:
    return DocumentationStats(
        files_checked=len(text_files),
        markdown_files=sum(1 for file in text_files if Path(file).suffix == ".md"),
    )


def read_text_file(root_directory: Path, relative_path: str) -> str:
    return (root_directory / relative_path).read_text(encoding="utf-8")


def is_text_file(file: str) -> bool:
    return Path(file).suffix in TEXT_EXTENSIONS or file in TEXT_FILE_NAMES


def count_lines(contents: str) -> int:
    if not contents:
        return 0

    return len(contents.splitlines())


def resolve_local_import(importer: str, specifier: str, file_set: set[str]) -> str | None:
    if specifier.startswith("."):
        base_path = resolve_relative_import_base(importer, specifier)
    else:
        base_path = specifier.replace(".", "/")

    candidates = [
        f"{base_path}.py",
        f"{base_path}/__init__.py",
        f"src/{base_path}.py",
        f"src/{base_path}/__init__.py",
    ]

    return next((candidate for candidate in candidates if candidate in file_set), None)


def resolve_relative_import_base(importer: str, specifier: str) -> str:
    level = len(specifier) - len(specifier.lstrip("."))
    module_part = specifier[level:].replace(".", "/")
    base = PurePosixPath(importer).parent

    for _ in range(max(level - 1, 0)):
        base = base.parent

    return to_posix(base / module_part)


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            cycle_start = stack.index(node)
            cycles.append([*stack[cycle_start:], node])
            return

        if node in visited:
            return

        visiting.add(node)
        stack.append(node)

        for next_node in graph.get(node, []):
            visit(next_node)

        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    return cycles


def to_posix(path: Path | PurePosixPath) -> str:
    return path.as_posix()
