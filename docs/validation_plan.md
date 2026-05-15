# Plano de Validacao

## Objetivo

Validar se o TB-IA e compreensivel, util e seguro como apoio operacional para APS no cuidado da tuberculose, antes de qualquer uso com dados reais.

## Etapa 1: Validacao tecnica

- Testar endpoints minimos.
- Testar motor de regras com casos sinteticos.
- Verificar que alertas trazem justificativas.
- Confirmar que seed nao contem dados reais.

## Etapa 2: Validacao com especialistas

- Revisar categorias de alerta.
- Ajustar pesos e recomendacoes operacionais.
- Confirmar linguagem nao diagnostica.
- Identificar riscos de falso senso de seguranca ou excesso de alertas.

## Etapa 3: Validacao de fluxo APS

- Simular uso por ACS, enfermagem e coordenacao.
- Medir tempo para entender alerta.
- Medir clareza da justificativa.
- Avaliar se o dashboard apoia planejamento territorial.

## Indicadores de MVP

- Percentual de alertas com validacao humana registrada.
- Tempo entre registro sintetico e acao operacional registrada.
- Distribuicao de alertas por territorio e prioridade.
- Concordancia qualitativa de profissionais com a prioridade sugerida.
- Taxa de alertas descartados por baixa relevancia.

## Criterios de seguranca

- Nenhum dado real no MVP.
- Aviso de nao diagnostico visivel na documentacao e API.
- Regras auditaveis.
- Acoes sempre registradas como operacionais.
- Ausencia de integracoes oficiais ate aprovacao institucional.

