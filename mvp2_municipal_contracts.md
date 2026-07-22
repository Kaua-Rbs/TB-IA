# MVP2 Municipal Demo Contracts

MVP2 starts as a synthetic, pseudonymized municipal operational pilot. It is intended for local workflow validation without real patient data, municipal production exports, authentication, RBAC, or governance approval. MVP1 public-data and privacy boundaries remain unchanged.

## Demo Workflow

The default `make demo` preparation includes this municipal slice. Run the
individual commands below only when preparing or debugging the operational
slice separately:

```bash
python -m tbia generate-mvp2-sample-data --output-dir data/raw/municipal_demo
python -m tbia ingest-local --raw-dir data/raw/municipal_demo --year 2023
python -m tbia build-operational-alerts --year 2023 --reference-date 2026-06-29
python -m tbia serve
```

The product operations dashboard is available at `/acompanhamento`. It works
with these canonical product API endpoints:

- `/api/operations/summary`
- `/api/operations/alerts`
- `/api/operations/alerts/{alert_id}`

The alerts collection accepts `year`, `alert_type`, `severity`, `status`,
`facility_id`, `team_id`, and `lang` query parameters. The summary accepts the
selected `year`.

The queue keeps the synthetic/pseudonymized scope visible, shows severity and
overdue state without relying on color alone, provides URL-backed filters with
an active count and reset, keeps alert detail beside the queue on desktop, and
expands detail in place on mobile.

The older Jinja `/mvp2` route and `/api/mvp2/*` endpoints remain available for
backend compatibility; new product code should use the canonical routes above.

## Privacy Boundary

The demo files must be synthetic or already pseudonymized. Do not place real CPF, CNS, person names, addresses, phone numbers, or free-text identifiers under `data/raw/municipal_demo/`.

The local CSV readers reject patient-level files containing obvious identifiable columns: `cpf`, `cns`, `nome`, `name`, `endereco`, `address`, `telefone`, or `phone`. The `name` column is accepted only in `local_territories.csv` and `local_teams.csv`, where it is an operational territory/team label rather than a person name.

`pseudonymized_patient_id` is required in local TB case, lab, resistance-evidence, and pharmacy files. `pseudonymized_contact_id` is required in contact investigation files. The MVP2 API and dashboard do not expose patient or contact pseudonym columns.

## CSV Contracts

All date values use `YYYY-MM-DD`. Empty optional date cells are accepted. Duplicate natural keys are rejected.

### `local_territories.csv`

```text
territory_id,name,territory_type,parent_id,uf_code,uf_sigla,facility_id,team_id
```

Natural key: `territory_id`.

### `local_teams.csv`

```text
team_id,facility_id,name,team_type,active
```

Natural key: `team_id`. `active` is a boolean-like value such as `true`, `false`, `1`, `0`, `sim`, or `nao`.

### `local_tb_cases.csv`

```text
local_case_id,pseudonymized_patient_id,territory_id,facility_id,team_id,notification_date,diagnosis_date,treatment_start_date,entry_type,clinical_form,closure_status,closure_date,rifampicin_resistance,retreatment,previous_treatment_failure
```

Natural key: `local_case_id`. Resistance and treatment-history flags are boolean-like values. The legacy `rifampicin_resistance` flag is only an unverified operational signal and never counts as confirmed resistance.

### `local_lab_events.csv`

```text
local_lab_id,local_case_id,pseudonymized_patient_id,test_type,request_date,collection_date,result_date,result,status
```

Natural key: `local_lab_id`.

### `local_resistance_evidence.csv`

This file is optional so older synthetic bundles remain ingestible.

```text
resistance_record_id,local_case_id,pseudonymized_patient_id,recorded_date,evidence_type,resistance_scope,resistance_status,record_status,source_system
```

Natural key: `resistance_record_id`. The case must exist in the same selected year
and the pseudonym must match the case registry. Accepted values are:

- `evidence_type`: `laboratory_result` or `authorized_clinical_record`;
- `resistance_status`: `confirmed`, `not_confirmed`, or `indeterminate`;
- `record_status`: `final`, `preliminary`, or `cancelled`;
- `source_system`: only `synthetic_demo` in the current implementation.

Only a `final` record explicitly marked `confirmed` may be presented as
confirmed synthetic evidence. Preliminary, cancelled, indeterminate, legacy,
and risk-history records remain vigilance signals. A real municipal source must
not use this contract until authorization, provenance, access control, and
governance decisions under GOV-01 are approved.

### `local_pharmacy_dispensing.csv`

```text
dispensing_id,local_case_id,pseudonymized_patient_id,dispensing_date,days_supplied,medication_group
```

Natural key: `dispensing_id`. `days_supplied` must be positive.

### `local_contacts.csv`

```text
contact_id,index_case_id,pseudonymized_contact_id,identified_date,evaluation_date,symptomatic,tpt_started_date,status
```

Natural key: `contact_id`. `symptomatic` is a boolean-like value.

### `local_resources.csv`

```text
facility_id,sputum_collection,rapid_molecular_access,xray_access,sample_transport,pharmacy_tb_meds,chw_count
```

Natural key: `facility_id` for the selected ingestion year. Resource access fields are boolean-like values. `chw_count` must be non-negative.

## Alert Rules

Generated alerts use status `open`. This slice does not implement task assignment, ownership, authentication, or status updates.

| Alert type | Severity | Rule |
| --- | --- | --- |
| `pending_lab_result` | `moderate` | Lab request date plus 7 days is before the reference date, `result_date` is empty, and `status` is not complete. |
| `medication_pickup_delay` | `high` | Latest dispensing date plus `days_supplied` plus a 7-day grace period is before the reference date for an open case. |
| `contact_pending_evaluation` | `moderate` | Contact identified date plus 7 days is before the reference date and `evaluation_date` is empty. |
| `resistance_vigilance` | `high` | Case has retreatment, previous treatment failure, rifampicin resistance, or pulmonary retreatment without completed culture/DST evidence in the lab file. |

Alerts are operational signals for human review. They must not be interpreted as diagnosis, prescription, or replacement for professional judgment.
