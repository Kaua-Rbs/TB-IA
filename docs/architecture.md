# Arquitetura

## Visao geral

O MVP usa uma arquitetura modular simples:

```text
Cliente/API docs -> FastAPI -> Servicos de aplicacao -> Motor de regras -> Repositorio em memoria
```

## Componentes

- `backend/main.py`: aplicacao FastAPI e rotas HTTP.
- `backend/schemas.py`: contratos de entrada e saida.
- `backend/rules_engine.py`: regras puras e explicaveis de priorizacao.
- `backend/storage.py`: repositorio em memoria para demonstracao.
- `backend/seed.py`: dados sinteticos.
- `scripts/seed_synthetic.py`: carregamento de dados via API ou inspecao local.
- `tests/`: verificacao basica de regras e fluxo da API.

## Decisoes de MVP

- Armazenamento em memoria para reduzir complexidade de demonstracao.
- Sem autenticacao real neste momento.
- Sem dados pessoais reais.
- Sem integracoes com e-SUS, SINAN, GAL ou prontuario.
- Regras deterministicas para explicabilidade e auditoria.
- Validacao humana explicita antes de tratar alerta como revisado.

## Evolucao tecnica

- Banco relacional com trilhas de auditoria.
- Autenticacao e perfis de acesso.
- Interface web para APS.
- Logs estruturados e observabilidade.
- Exportacao agregada para gestao.
- Integracoes oficiais somente com autorizacao institucional, base legal e seguranca adequada.

## Fronteiras de responsabilidade

O sistema produz sinalizacao operacional. Profissionais e gestores continuam responsaveis por avaliacao clinica, conduta, notificacao, exames, tratamento e registros oficiais.

