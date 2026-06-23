# TB-IA

Documentation and planning workspace for an intelligent tuberculosis public health decision-support platform.

The product concept focuses on helping primary care and municipal surveillance teams identify priority territories, missed screening opportunities, patient follow-up risks, and operational strategies for tuberculosis control. The current repository is not yet an application implementation.

The application is expected to be implemented in Python. The current Python tooling exists only to validate repository documentation and future development quality gates.

## Key Documents

- `descricao_do_projeto.md`: product vision, scope, MVP assumptions, data sources, and LGPD constraints.
- `frentes_de_desenvolvimento.md`: workstreams for product, evidence, data, rules, interface, architecture, and validation.
- `referencias.md`: related systems, papers, and design references for public health surveillance and TB decision support.
- `especificacao_tecnica_do_sistema.md`: engineering-oriented specification for MVP scope, data contracts, architecture, workflows, governance, and validation.
- `documentos/`: source PDFs and supporting reference documents used during project formulation.
- `notebooks/`: exploratory notebooks and scripts for public-data loading and visualization.
- `AGENTS.md`: project-specific instructions for future Codex sessions.
- `CONTRIBUTING.md`: setup and quality command reference.

## Setup

```bash
python -m pip install -r requirements-dev.txt
```

## Exploratory Notebooks

```bash
python -m pip install -r requirements-notebook.txt
jupyter lab notebooks/explorar_bases_publicas.ipynb
```

Notebook downloads and generated CSVs are written under `data/`, which is ignored by git.

## Quality Commands

```bash
make check
make coverage
make complexity
make deps
make mutation
```

`make check` is the standard fast gate for local development, CI, and future Codex sessions.

Because the repository is documentation-first today, application-specific coverage, dependency architecture, and mutation testing should be added when real source code and critical logic are introduced.
