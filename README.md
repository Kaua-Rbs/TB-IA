# TB-IA Gestao Territorial e Microassistencial

MVP para apoio operacional a equipes de Atencao Primaria a Saude (APS) e vigilancia municipal no cuidado da tuberculose, com foco em busca ativa, investigacao de contatos, prevencao de abandono e priorizacao explicavel de alertas.

Este projeto esta sendo preparado para o BioChallenge, competicao organizada pelo Inatel em parceria com a SBEB. A proposta combina software funcional, documentacao de produto, narrativa de problema-solucao, demonstracao e materiais de pitch.

## Aviso clinico e regulatorio

O TB-IA nao diagnostica tuberculose, nao prescreve condutas, nao substitui profissionais de saude e nao executa decisao clinica automatizada. O MVP usa apenas dados sinteticos e gera alertas operacionais explicaveis para apoiar organizacao do trabalho. Qualquer acao assistencial deve seguir protocolos oficiais, julgamento profissional e fluxos municipais.

## O que o MVP faz

- Cadastra respostas sinteticas de questionarios de rastreio, contatos e adesao/barreiras.
- Calcula risco por motor de regras simples, transparente e auditavel.
- Gera alertas operacionais priorizados por territorio e microarea.
- Exibe fila de alertas para revisao humana.
- Permite validacao humana do alerta.
- Registra acoes realizadas pela equipe.
- Exibe dashboard agregado por territorio.
- Documenta limites, governanca, LGPD, demonstracao e evolucao pos-competicao.

## Estrutura

```text
backend/                  API FastAPI, modelos, regras, seed e repositorio em memoria
docs/                     Documentacao de produto, competicao, arquitetura e governanca
scripts/                  Scripts auxiliares para seed sintetico
tests/                    Testes basicos de regras e endpoints
```

## Como executar localmente

Requisitos: Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.main:app --reload
```

API local:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

Carregar dados sinteticos para demonstracao:

```bash
python scripts/seed_synthetic.py --api http://127.0.0.1:8000
```

Ou via API:

```bash
curl -X POST http://127.0.0.1:8000/seed/synthetic
```

## Fluxo de demonstracao

1. Abrir `/docs` e mostrar o aviso de uso nao diagnostico.
2. Executar `/seed/synthetic` para carregar exemplos.
3. Abrir `GET /alerts` para mostrar fila priorizada.
4. Validar um alerta com `POST /alerts/{alert_id}/validation`.
5. Registrar uma acao com `POST /alerts/{alert_id}/actions`.
6. Abrir `GET /dashboard/territories` para mostrar agregacao territorial.

Roteiro completo: [docs/demo_script.md](docs/demo_script.md).

## Testes

```bash
pytest
```

## Documentacao principal

- [Brief de produto](docs/product_brief.md)
- [Contexto BioChallenge](docs/biochallenge_context.md)
- [Entregaveis de competicao](docs/competition_deliverables.md)
- [Roteiro de demonstracao](docs/demo_script.md)
- [Roteiro de pitch](docs/pitch_outline.md)
- [Arquitetura](docs/architecture.md)
- [Dicionario de dados](docs/data_dictionary.md)
- [Motor de regras](docs/rules.md)
- [Governanca e LGPD](docs/lgpd_governance.md)
- [Plano de validacao](docs/validation_plan.md)

