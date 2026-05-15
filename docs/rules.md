# Motor de Regras

## Objetivo

O motor de regras transforma respostas sinteticas de questionarios em alertas operacionais explicaveis. Ele nao estima probabilidade clinica real, nao diagnostica e nao substitui protocolos.

## Faixas de prioridade

| Score | Prioridade |
| --- | --- |
| 0-29 | `low` |
| 30-59 | `moderate` |
| 60-89 | `high` |
| 90+ | `critical` |

## Pontuacao inicial

| Condicao sintetica | Pontos |
| --- | --- |
| Tosse por 2 semanas ou mais | +30 |
| Febre | +15 |
| Sudorese noturna | +15 |
| Perda de peso | +15 |
| Contato conhecido com caso de TB | +30 |
| Contato domiciliar | +20 |
| Em tratamento com faltas recentes | +25 |
| Interrupcao de tratamento relatada | +30 |
| Efeitos adversos como barreira | +15 |
| Barreira de transporte | +10 |
| Inseguranca alimentar | +10 |
| Estigma ou medo de exposicao | +10 |
| Vulnerabilidade relevante | +15 cada, limitado a +45 |

## Gatilhos de categorias

- `respiratory_symptom_screening`: tosse prolongada, febre, sudorese noturna ou perda de peso.
- `contact_investigation`: contato conhecido, especialmente domiciliar.
- `adherence_support`: pessoa em acompanhamento/tratamento com faltas, interrupcao ou barreiras.
- `territorial_vulnerability`: vulnerabilidades sociais ou territoriais relevantes.

## Explicabilidade

Cada alerta inclui:

- score total;
- prioridade;
- categoria;
- lista de razoes;
- acao operacional recomendada.

## Revisao humana

Todo alerta nasce com status `pending`. Ele deve ser validado, descartado ou complementado por profissional autorizado antes de orientar qualquer fluxo assistencial.

