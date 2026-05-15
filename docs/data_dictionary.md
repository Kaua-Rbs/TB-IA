# Dicionario de Dados

Todos os exemplos do MVP sao sinteticos. Identificadores como `synthetic_person_id` nao representam CPF, CNS, nome ou qualquer identificador real.

## Questionnaire

| Campo | Tipo | Descricao |
| --- | --- | --- |
| `id` | UUID | Identificador interno sintetico do questionario. |
| `synthetic_person_id` | string | Codigo sintetico da pessoa ou domicilio. |
| `territory_id` | string | Codigo sintetico do territorio. |
| `territory_name` | string | Nome sintetico do territorio. |
| `micro_area` | string | Microarea sintetica. |
| `age_range` | string | Faixa etaria, sem data de nascimento. |
| `symptoms` | object | Sinais autorreferidos no questionario. |
| `contact` | object | Informacoes sinteticas de contato com caso conhecido. |
| `adherence` | object | Situacao sintetica de acompanhamento/tratamento. |
| `barriers` | list[string] | Barreiras operacionais ou sociais relatadas. |
| `vulnerabilities` | list[string] | Vulnerabilidades sinteticas relevantes ao cuidado. |
| `submitted_by` | string | Perfil ou usuario sintetico que registrou. |
| `created_at` | datetime | Data de criacao no MVP. |

## Alert

| Campo | Tipo | Descricao |
| --- | --- | --- |
| `id` | UUID | Identificador do alerta. |
| `questionnaire_id` | UUID | Questionario que gerou o alerta. |
| `synthetic_person_id` | string | Codigo sintetico associado. |
| `territory_id` | string | Territorio do alerta. |
| `micro_area` | string | Microarea do alerta. |
| `category` | string | Tipo do alerta operacional. |
| `priority` | string | `low`, `moderate`, `high` ou `critical`. |
| `score` | integer | Pontuacao explicavel do motor de regras. |
| `title` | string | Titulo operacional. |
| `rationale` | list[string] | Motivos que elevaram o risco. |
| `recommended_action` | string | Sugestao operacional nao clinica. |
| `status` | string | `pending`, `validated`, `dismissed` ou `completed`. |
| `validation` | object/null | Decisao humana registrada. |
| `actions` | list[object] | Acoes operacionais registradas. |

## Categorias de alerta

- `respiratory_symptom_screening`: sintomatico respiratorio ou sinais associados.
- `contact_investigation`: contato de caso conhecido.
- `adherence_support`: risco operacional de abandono ou baixa adesao.
- `territorial_vulnerability`: vulnerabilidades sociais/territoriais que exigem atencao da equipe.

