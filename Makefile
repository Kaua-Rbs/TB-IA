PYTHON ?= python3
MARKDOWN_FILES = AGENTS.md CONTRIBUTING.md README.md descricao_do_projeto.md frentes_de_desenvolvimento.md mvp2_municipal_contracts.md referencias.md especificacao_tecnica_do_sistema.md

.PHONY: install lint format format-check type test coverage complexity deps mutation check frontend-install frontend-dev frontend-check frontend-build

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	$(PYTHON) -m ruff check src scripts tests
	$(PYTHON) -m scripts.validate_docs

format:
	$(PYTHON) -m ruff format src scripts tests
	$(PYTHON) -m mdformat $(MARKDOWN_FILES)

format-check:
	$(PYTHON) -m ruff format --check src scripts tests
	$(PYTHON) -m mdformat --check $(MARKDOWN_FILES)

type:
	$(PYTHON) -m mypy src scripts tests

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=scripts --cov=src/tbia/domain --cov=src/tbia/ingest --cov=tbia.storage --cov-report=term-missing --cov-fail-under=80

complexity:
	$(PYTHON) -m scripts.quality_gates complexity
	$(PYTHON) -m radon cc src scripts tests -s -a
	$(PYTHON) -m radon mi src scripts tests

deps:
	$(PYTHON) -m scripts.quality_gates deps

mutation:
	$(PYTHON) -m scripts.quality_gates mutation

check: lint format-check type test


frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-check:
	cd frontend && npm run check

frontend-build:
	cd frontend && npm run build
