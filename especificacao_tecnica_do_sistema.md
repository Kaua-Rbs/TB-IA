# Technical system specification

This document adapts the previous medical/product proposal into a systems and engineering specification for TB-IA. It keeps the same public health purpose, but makes the work more concrete for software design, data engineering, validation, governance, and incremental delivery.

The platform should support tuberculosis management in primary care and municipal surveillance. It should transform fragmented public, official, local, and questionnaire-based data into transparent indicators, territorial prioritization, operational queues, and evidence-linked recommendations.

The platform must not diagnose tuberculosis, prescribe treatment, replace professional judgment, or generate unsourced clinical recommendations. It is a decision-support and operational management system.

## Engineering interpretation of the proposal

The original proposal describes four implementation layers:

- Layer 0: questionnaire-based independent version;
- Layer 1: public and official aggregated data;
- Layer 2: local municipal data integration;
- Layer 3: micro-care and operational decision support.

From a systems perspective, these layers mix three separate dimensions:

- data maturity: questionnaire, public aggregate data, local exports, individual records;
- deployment maturity: standalone tool, public dashboard, municipal installation, integrated local system;
- product maturity: education/screening, territorial intelligence, operational management, patient-level decision support.

The implementation should keep these dimensions separate. A better engineering model is:

1. Data ingestion.
1. Canonical data store.
1. Indicator engine.
1. Scenario and prioritization engine.
1. Evidence and recommendation library.
1. Workflow and task engine.
1. Dashboards and reporting.
1. Audit, governance, privacy, and validation.

## Recommended MVP sequence

### MVP 0: questionnaire-only validation

Purpose:

- validate user experience;
- collect consented, non-diagnostic screening and access-barrier data;
- test language, flows, and risk explanations;
- support education, outreach, and community campaigns.

Core outputs:

- symptom screening summary;
- access-to-care barrier summary;
- contact-exposure summary;
- adherence-barrier summary for people already on treatment;
- aggregated neighborhood or municipality report when consent and minimum counts allow.

Engineering constraints:

- no CPF, CNS, exact address, or individual geolocation in the first independent version;
- no diagnosis labels;
- no official surveillance claims;
- no patient-level maps;
- explicit consent and purpose text;
- exportable aggregated dataset for analysis.

### MVP 1: public-data territorial intelligence

Purpose:

- demonstrate the first defensible epidemiological management product;
- use public and official aggregate data;
- classify municipalities or larger territories into scenarios and subscenarios;
- produce priority rankings and evidence-linked operational recommendations.

Core sources:

- SINAN-TB/DATASUS;
- SIM;
- SIH/SUS;
- CNES;
- IBGE population and territorial data;
- SISAB or other public APS aggregate indicators where useful;
- Boletim Epidemiologico Tuberculose 2026 as the official reference for Brazilian indicator
  definitions, formulas, periods, exclusions, and source caveats.

Core outputs:

- municipality-level TB indicator dashboard;
- municipality-level public aggregate choropleth using cached IBGE Malhas geometry;
- optional public submunicipal reference polygons for contextual municipality drill-down, not TB prioritization;
- incidence, mortality, cure, treatment interruption, retreatment, laboratory confirmation, TB-HIV, and demographic profiles;
- scenario and subscenario classification;
- priority territory ranking;
- no patient-level, address-level, or MVP 2 operational alert-point maps in the MVP 1 public view;
- recommendation summary linked to a strategy library;
- data-quality warnings and source freshness indicators.

Current MVP 1 UI implementation note: the React product at `/` and
`/territorios` is a responsive public aggregate workbench. It is
Portuguese-first with optional English through a `lang` query parameter and
exposes scope-aware data readiness, UF/year/comparison controls, municipality
search, automatic initial priority selection, and synchronized
map/ranking/dossier interactions. Its layer-specific legend reports values and
units, separates available, suppressed, and missing data, and identifies the
selected municipality and optional public reference overlays. The dossier
keeps transparent scenario explanations, recommendations, indicators, caveats,
and source freshness without patient-level maps or clinical automation. It also
exposes a non-scoring resistance-surveillance profile using retreatment,
culture-use, and TRM-TB-use signals. The profile distinguishes available,
suppressed, and missing data; carries comparison readiness and source
provenance; and explicitly states that confirmed resistance burden is not
available in the public aggregate sources. On mobile, the shell reflows
controls, rankings, status labels, and detail content without horizontal table
dependence. Bairros or other public intramunicipal polygons are reference
geography only; official UBS/team/microarea boundaries and TB outcomes by
health territory are unavailable in the public-only MVP.

This is the implemented first engineering slice. Recorded domain acceptance and
production deployment remain pending.

### MVP 2: municipal operational integration

Purpose:

- support a municipal partner with authorized local exports;
- move from public aggregate monitoring to local operational management;
- compare UBS, teams, neighborhoods, microareas, or other local territories when governance permits.

Possible inputs:

- municipal SINAN export;
- local laboratory or GAL export;
- pharmacy dispensing file;
- local contact investigation spreadsheet;
- UBS/team/microarea territorial registry;
- resource inventory by unit;
- validated operational spreadsheets from surveillance teams.

Core outputs:

- local hot-zone analysis;
- pending lab result alerts;
- medication pickup delay alerts;
- contact investigation pending lists;
- unit-level operational indicators;
- one resistance-vigilance alert per case, separating explicit final synthetic evidence, treatment-history or legacy unverified risk, and missing completed culture/DST surveillance.

Current first implementation slice:

- use synthetic, pseudonymized municipal CSVs under `data/raw/municipal_demo/`;
- keep the MVP 2 dashboard visibly labeled as synthetic/pseudonymized until authorized local-data governance, integration, and validation exist;
- reject obvious identifiable columns before local operational ingestion;
- persist local teams, TB cases, lab events, optional structured synthetic
  resistance evidence, pharmacy dispensing events, contact investigations,
  resource inventory, and generated operational alerts;
- generate transparent alert queues for pending lab results, delayed medication pickup, pending contact evaluation, and resistance vigilance;
- expose `/acompanhamento` and `/api/operations/*` as the canonical product
  routes for local operations review;
- provide URL-backed filters by alert type, resistance signal kind, severity,
  status, facility, and team, with active-filter count and reset;
- identify high-severity and overdue items with text and icons as well as color;
- keep alert detail sticky beside the desktop queue and expandable in place on
  mobile;
- retain the Jinja `/mvp2` route and `/api/mvp2/*` as backend compatibility
  paths;
- remain without patient-level maps, task assignment, authentication, or RBAC.

This starter slice is a workflow and data-contract pilot. It is not
authorization to load real municipal patient data. Real exports require
institutional approval, governance, local deployment controls, auditability,
and role-based access decisions before production use.

The CAP-04 resistance rules remain `pending_domain_review`. Their technical
contract, evidence classes, severity, response and user comprehension must be
reviewed through `guia_validacao_de_dominio.md`; GOV-01 is mandatory before
any real municipal source is enabled.

### MVP 3: micro-care decision support

Purpose:

- support individual and microterritorial action lists;
- detect missed screening opportunities;
- estimate operational risk of treatment interruption;
- provide professional validation workflows.

Prerequisites:

- authorized patient-level data;
- local installation or equivalent governance agreement;
- role-based access control;
- audit logs;
- data minimization and pseudonymization strategy;
- validated clinical and operational rules;
- professional review before recommendations are used in care.

This should not be attempted before MVP 1 and MVP 2 establish data quality, workflows, and trust.

## Core system modules

### Data ingestion module

Responsibilities:

- import public DATASUS, IBGE, CNES, and other official sources;
- import local CSV/XLSX/DBF/DBC-derived files when authorized;
- validate schemas, required fields, and code systems;
- record import provenance, version, source URL or file name, extraction date, and processing date;
- reject or quarantine malformed files;
- generate source-specific data-quality reports.

Engineering requirements:

- every imported dataset must have a declared grain;
- every dataset must have a refresh cadence;
- every transformation must be reproducible;
- raw inputs should be preserved or checksummed;
- derived tables should be regenerated from source transformations.

### Canonical data store

The platform should not let every module depend directly on source-specific fields. It should map source files into a canonical internal model.

Starter entities:

| Entity | Purpose | Typical grain |
| --- | --- | --- |
| `DataSource` | Source metadata, owner, update frequency, access method | one record per source |
| `ImportRun` | Scoped ingestion execution, coverage, and validation result | source-geographic scope-year-execution |
| `Territory` | UF, municipality, neighborhood, microarea, UBS catchment | one record per territory |
| `PopulationDenominator` | Population by territory, year, age, sex where available | territory-period-group |
| `Facility` | CNES/UBS/service unit metadata | one record per facility |
| `Team` | APS or local health team | one record per team |
| `CaseAggregate` | Aggregated TB cases by territory, time, and stratifier | territory-period-strata |
| `MortalityAggregate` | TB deaths by territory, time, and stratifier | territory-period-strata |
| `HospitalizationAggregate` | TB-related admissions and outcomes | territory-period-strata |
| `IndicatorDefinition` | Numerator, denominator, filters, caveats | one record per indicator |
| `IndicatorValue` | Computed indicator value with metadata | territory-period-indicator |
| `ScenarioRule` | Scenario and subscenario rule definition | one record per rule |
| `ScenarioRuleEvaluation` | Rule readiness, coverage, and threshold audit by comparison scope | geographic scope-period-comparison-rule |
| `TerritoryScenario` | Rule output for a territory and period | territory-period-scenario |
| `Strategy` | Evidence-linked intervention option | one record per strategy |
| `Recommendation` | Strategy suggested for a scenario | territory-period-strategy |
| `Alert` | Operational signal requiring review | one record per alert |
| `Task` | Action assigned to a user/team | one record per task |
| `ValidationEvent` | Human review of alert/recommendation | one record per review |
| `AuditEvent` | Security and user activity log | one record per event |

The implemented `ImportRun` stores `year`, `geographic_scope`, and optional
`loaded_months` in addition to status, counts, timestamps, and message. Public
source freshness and indicator validation are selected for the requested
geography and year; reuse of a national source for a UF is explicit, and
synthetic municipal imports do not satisfy public territorial readiness.

SIH/SUS annual readiness requires all 12 months for the selected UF. Partial or
coverage-unknown hospitalization aggregates remain stored for audit but do not
produce annual hospitalization indicators or scenarios. National
hospitalization readiness additionally requires complete coverage for every
component UF.

Additional patient-level entities should only be introduced for MVP 2 or MVP 3 with institutional authorization:

- `Patient`;
- `TbCase`;
- `Contact`;
- `LabOrder`;
- `LabResult`;
- `MedicationDispensing`;
- `Appointment`;
- `QuestionnaireResponse`;
- `CareAction`.

### Indicator engine

Each indicator must be defined before implementation. A good indicator definition includes:

- indicator ID;
- name;
- public health question answered;
- numerator;
- denominator;
- filters;
- geography;
- time window;
- source tables;
- update cadence;
- interpretation;
- caveats;
- minimum count or suppression rule;
- owner/reviewer;
- version.

For the Brazilian public-data MVP, the indicator dictionary should be traceable to the Boletim
Epidemiologico Tuberculose 2026 and the Caderno de Indicadores da Tuberculose. This means each
implemented indicator should keep the official formula, source, analysis period, exclusions, and
source caveats alongside the computed value.

Starter indicators for MVP 1:

| Indicator | Public-data status | Numerator | Denominator | Corrected public source | Implementation note |
| --- | --- | --- | --- | --- | --- |
| TB incidence | Obtainable | new TB cases in period | population denominator | SINAN-TB public DBC/TabNet, IBGE population | Use residence territory and the official new-case entry-type definition before ranking territories. |
| TB mortality | Obtainable | TB deaths in period | population denominator | SIM public DBC, IBGE population | Filter underlying cause of death to CID-10 A15-A19 and use residence territory unless explicitly analyzing place of occurrence. |
| Cure proportion | Obtainable | cases closed as cure | cases with closure status | SINAN-TB public DBC/TabNet | Requires official closure-status mapping and cohort period definition. |
| Treatment interruption proportion | Obtainable | cases closed as abandonment/interruption | cases with closure status | SINAN-TB public DBC/TabNet | Requires official closure-status mapping; label should follow the current Brazilian indicator terminology. |
| Retreatment proportion | Obtainable | retreatment cases | notified TB cases | SINAN-TB public DBC/TabNet | Use entry type categories such as recurrence and re-entry after abandonment according to the official dictionary. |
| Laboratory confirmation proportion | Obtainable with transformation | pulmonary cases confirmed by smear microscopy, rapid molecular test, or culture | new pulmonary TB cases | SINAN-TB public DBC | Prefer DBC-derived transformation because the numerator combines multiple lab fields and should avoid double counting. |
| HIV testing proportion | Obtainable | new TB cases tested for HIV | new TB cases | SINAN-TB public DBC/TabNet | MVP 1 counts completed positive or negative HIV results inside the new-case universe. |
| TB-HIV burden | Obtainable | new TB cases with positive HIV result | new TB cases | SINAN-TB public DBC/TabNet | MVP 1 uses HIV-positive result for the public indicator; AIDS comorbidity remains in the mapping audit until domain review. |
| Contacts examined proportion | Conditional, requires validation | examined contacts of lab-confirmed new pulmonary TB cases | identified contacts of lab-confirmed new pulmonary TB cases | SINAN-TB public DBC fields, not TabNet-ready | Public DBC contains contact count fields, but public TabNet notes contact indicators cannot be calculated there; keep out of mandatory MVP until validated against the official indicator handbook. |
| TRM-TB use proportion | Obtainable | new pulmonary TB cases with `TEST_MOLEC` result codes 1-4 | new pulmonary TB cases | SINAN-TB public DBC/TabNet | Codes 1-4 represent a performed molecular test; code 5, ignored, and blank values do not count. Only detected results (codes 1-2) contribute to laboratory confirmation. `RIFAMPICIN` is audited but is not a TRM-TB-use proxy. |
| Culture use among retreatment | Obtainable with transformation | retreatment pulmonary TB cases with sputum culture | retreatment pulmonary TB cases | SINAN-TB public DBC | Requires combining entry type, pulmonary form, and culture fields. |
| Drug-resistant TB burden | Not publicly obtainable from the cited source | new drug-resistant TB cases by initial resistance pattern | applicable TB DR case universe | Site-TB only with authorized access; SINAN-TB has limited resistance-related fields | Do not include as a mandatory public-data MVP indicator. Use only as a local/institutional integration or as a crude surveillance-gap flag after domain validation. |
| Preventive treatment initiation | Not publicly obtainable from the cited source | people starting TB preventive treatment | applicable eligible group or period total | IL-TB, Silt, or Vigilantos only with authorized access or specific public reports | Do not include as a mandatory public-data MVP indicator. Treat as a future integration or manual-report import. |
| Hospitalization burden | Obtainable | TB-related admissions | population or TB cases | SIH/SUS public DBC, IBGE population and/or SINAN-TB | Filter primary/secondary TB diagnoses using CID-10 A15-A19; interpret as severe disease or care-pathway proxy, not incidence. |
| APS service capacity proxy | Obtainable for CNES capacity; partial for APS production | selected CNES/APS resources | population or territory | CNES public DBC, IBGE population; SISAB/e-Gestor public reports when available | CNES supports facility/capacity proxies. SISAB/e-Gestor can enrich APS context but should not block MVP 1. |

Mandatory MVP 1 indicators should be limited to the rows marked `Obtainable` or `Obtainable with transformation`. Rows marked `Conditional` require explicit validation before they affect scenario
classification. Rows marked `Not publicly obtainable` must remain outside the public-data MVP unless
there is institutional authorization, a curated local extract, or a specific public report.

Current MVP 1 SINAN transform choices are provisional but explicit: case type codes `1`, `4`, and `6` form the new-case universe, matching the Boletim 2026 note for caso novo, não sabe, and pós-óbito; case type codes `2` and `3` form the retreatment universe. Treatment outcome proportions are calculated only among new cases with outcome denominator closures for cure, interruption, death, ignored, or not evaluated; diagnosis change, TB-DR, regimen change, and failure-style closure codes are excluded pending domain review. Bounded proportions with numerator greater than denominator are suppressed in public outputs and reported as validation violations; zero-over-zero denominators are reported as missingness warnings.

The CAP-03 contact-investigation audit uses a separate candidate contract and
does not extend the production aggregate while validation is open. It reads
`NU_CONTATO` as identified contacts and `NU_COMU_EX` as examined contacts after
selecting the notification year and municipality of residence. Candidate cases
use entry types `1`, `4`, and `6`, pulmonary or mixed form, every closure except
change of diagnosis, and laboratory confirmation through positive initial
smear (`BACILOSC_E`), positive second smear (`BACILOS_E2`), positive culture, or
detected TRM-TB. Missing contact counts are reported both as independently
recorded sums and as complete numerator/denominator pairs; neither treatment is
accepted as the official indicator until source reconciliation and domain
review. The audit must not persist person-level rows or feed scenarios, APIs, or
rankings.

### Scenario and prioritization engine

The first version should use transparent rules and scoring, not opaque AI.

Example subscenarios:

- high incidence;
- rising incidence;
- high mortality;
- high treatment interruption;
- low cure;
- high retreatment;
- low laboratory confirmation;
- high TB-HIV burden;
- high hospitalization burden;
- possible surveillance gap;
- possible service fragility.

Each subscenario rule should define:

- input indicators;
- threshold method;
- comparison group;
- minimum data requirements;
- severity level;
- explanation text;
- recommended strategies;
- validation status.

Thresholds should initially be configurable:

- absolute threshold;
- percentile within state or region;
- trend threshold;
- comparison against national target;
- composite score.

The current MVP 1 implementation uses an intentionally simple percentile-based composite score.
This score is not an official Ministry of Health indicator and should not be interpreted as a
validated epidemiological risk model. Its purpose is to produce a transparent first ranking that a
domain reviewer can audit from the source indicators.

Current rule thresholds are calculated within the selected UF and year, after small-count
suppression removes unavailable public values:

- for indicators where higher values are worse, the rule threshold is the 75th percentile (`p75`);
- for indicators where lower values are worse, the rule threshold is the 25th percentile (`p25`).

Three diagnostic-coverage rules are implemented as provisional comparative
signals:

| Rule | Indicator | Threshold | Severity | Ranking dimension | Strategy |
| --- | --- | --- | --- | --- | --- |
| `low_hiv_testing` | `hiv_testing_proportion` | `p25` | moderate | `tb_hiv_integration` | `tb_hiv_integration` |
| `low_trm_tb_use` | `trm_tb_use_proportion` | `p25` | moderate | `diagnostic_access` | `diagnostic_flow_review` |
| `low_culture_use_among_retreatment` | `culture_use_among_retreatment` | `p25` | moderate | `resistance_surveillance` | `resistance_surveillance_review` |

These rules are evaluated separately for each geographic scope, year, and
comparison scope. A diagnostic rule is ready only when both conditions are met:

- at least 10 available municipality values;
- available municipality values cover at least 5% of the canonical
  municipalities in scope.

Available values exclude missing and suppressed observations. The engine stores
one evaluation per rule with the canonical territory count, available,
suppressed, and unavailable counts, coverage ratio, threshold, and one of these
states:

- `ready`: both gates pass and a threshold may generate scenarios;
- `missing_indicator`: the scoped indicator has no stored observations;
- `insufficient_comparison`: observations exist, but available coverage does
  not pass both gates.

No threshold or scenario is generated unless the evaluation is `ready`.
Suppressed observations never become low-performance signals. The API exposes
the detailed evaluations and an aggregate diagnostic-readiness item so sparse
coverage remains visible instead of silently removing a rule.

All three rules and their generated scenarios carry
`review_status=pending_domain_review`. Their explanations call them
provisional comparative rules. The acceptance fixture validates transformation
behavior, but epidemiology/domain review of thresholds, severity, and suggested
strategies remains required before CAP-01 can be considered complete.

Scenario generation also writes
`diagnostic_ranking_impact_<scope>_<year>.json` under the processed validation
directory. The report isolates CAP-01 impact by comparing the current
dimension-capped ranking with and without the three diagnostic rules. It
records score and rank changes, top-ten overlap, newly ranked municipalities,
and the amount of correlated scenario weight removed by dimension caps. Both
versions use the production ranking function; the baseline is not a separate
scoring implementation.

The report status remains
`technical_validation_pending_domain_review`. It is reproducible technical
evidence and cannot approve the percentile, severity, grouping, or strategy.

A scenario is triggered when the municipality value crosses the rule threshold:

```text
high_bad rule triggers when value >= threshold
low_bad rule triggers when value <= threshold
```

Each triggered scenario receives a score:

```text
scenario_score = severity_weight * score_multiplier
```

Severity weights are:

```text
high = 3.0
moderate = 2.0
low = 1.0
```

The multiplier rewards how far the municipality is beyond the threshold while keeping every
triggered scenario worth at least its base severity weight:

```text
high_bad score_multiplier = max(1.0, value / threshold)
low_bad score_multiplier = max(1.0, threshold / max(value, 0.01))
```

Each rule declares a ranking dimension. All triggered scenarios remain visible for audit, but
correlated scenarios cannot accumulate weight indefinitely: only the strongest score in each
dimension contributes to the municipality score.

```text
dimension_score = max(triggered scenario_score in dimension)
municipality_score = sum(dimension_score)
```

The dashboard reports both triggered scenario count and contributing dimension count, and sorts
municipalities by:

```text
municipality_score descending
contributing dimension count descending
territory name ascending
```

Triggered scenario count is display-only and does not break ranking ties. Recommendations that map
to the same strategy are grouped, while their contributing rule identifiers remain available for
audit.

This formula was chosen because it satisfies the first MVP engineering criteria: it is deterministic,
easy to explain, uses only public aggregate indicators, avoids opaque AI, and gives stronger weight
to both more severe subscenarios and more extreme deviations from the comparison group. It was not
selected through formal optimization, prospective validation, cost-effectiveness analysis, expert
elicitation, or comparison against tuberculosis program outcomes. Future work should validate or
replace this scoring model using official indicator definitions, domain-reviewer feedback,
sensitivity analysis, historical municipal outcomes, and comparison with simpler baselines such as
unweighted scenario counts or incidence-only ranking.

A future hotspot module can follow the design pattern from the Nigeria AI-driven hotspot mapping
study: local active case-finding events, contact investigation yield, facility screening yield, and
contextual covariates are mapped into population clusters; a model predicts positivity or priority
for unscreened clusters; a geoportal supports field team planning; and new screening results feed
back into the next model cycle. This should be treated as a municipal-partnership feature because it
requires local screening-event data, geocoding, governance, and prospective validation against
conventional notification-based planning.

### Evidence and recommendation library

Recommendations should not be generated freely by a language model. They should come from a structured strategy library linked to evidence and guidelines.

Recommended fields:

| Field | Description |
| --- | --- |
| `strategy_id` | Stable identifier |
| `name` | Strategy name |
| `target_problem` | Scenario/subscenario addressed |
| `target_population` | Territory, cases, contacts, vulnerable group, service unit |
| `evidence_source` | WHO, Brazilian guideline, manual, paper, or local protocol |
| `evidence_strength` | Guideline level, evidence grade, or local expert validation |
| `required_resources` | CHW, nurse, lab access, transport, pharmacy, social support |
| `estimated_cost_level` | low, medium, high, or unknown |
| `operational_complexity` | low, medium, high |
| `prerequisites` | data, authorization, service capacity |
| `contraindications_or_limits` | when not to suggest it |
| `monitoring_indicators` | indicators to reassess after implementation |
| `review_date` | last evidence review |
| `owner` | person/team responsible for maintaining the strategy |

Generative AI may help explain or summarize recommendations, but only after the structured recommendation has already been selected by rules, evidence, and human-governed configuration.

### Workflow and task engine

Dashboards are not enough. The system needs to represent work.

Common workflow states:

- created;
- assigned;
- in review;
- action planned;
- action performed;
- waiting for exam;
- waiting for contact;
- referred;
- discarded;
- impossible at the moment;
- resolved;
- reopened.

Each alert or recommendation should support:

- responsible user or team;
- due date;
- priority;
- source indicators;
- explanation;
- action history;
- human validation status;
- audit events.

### Dashboard and reporting module

Dashboards should be separated by user role.

Manager dashboard:

- territory ranking;
- municipality-level public aggregate scenario map;
- trend indicators;
- data freshness;
- resource capacity;
- strategy recommendations;
- monitoring after intervention.

Surveillance dashboard:

- notification trends;
- treatment outcomes;
- retreatment;
- laboratory confirmation;
- TB-HIV markers;
- mortality and hospitalization;
- data completeness.

Primary care dashboard:

- unit/team indicators;
- active task queues when local data exist;
- contact follow-up;
- missed screening opportunities when supported by data;
- adherence barriers and follow-up tasks.

Public or demonstration dashboard:

- aggregated and non-identifiable information only;
- no individual records;
- no small-count exposure;
- clear caveats about source and delay.

## Data contracts

Every source must have a small contract before implementation.

Minimum fields:

- source name;
- owner;
- access method;
- file/API/table format;
- grain;
- geographic coverage;
- time coverage;
- refresh cadence;
- required fields;
- optional fields;
- code systems;
- missingness rules;
- duplicate handling;
- privacy level;
- transformation owner;
- validation checks.

Example contract summary:

| Source | Grain | Format | MVP use |
| --- | --- | --- | --- |
| SINAN-TB/DATASUS | national public TB records by year; aggregate TabNet tables for validation | FTP DBC files such as `SINAN/DADOS/PRELIM/TUBEBR23.dbc` or older `FINAIS/TUBEBRYY.dbc`; TabNet PRN/HTML fallback | case burden, outcomes, lab confirmation, HIV, TRM-TB, culture, and conditional contact indicators |
| SIM | UF mortality records by year | FTP DBC files such as `SIM/CID10/DORES/DOCE2023.dbc` | TB mortality filtered by CID-10 A15-A19 |
| SIH/SUS | UF-month hospital admission records | FTP DBC files such as `SIHSUS/200801_/Dados/RDCE2401.dbc` | TB-related hospitalization burden and severity proxy only with explicit 12-month coverage; partial or unknown coverage is audit-only and excluded from annual rankings |
| CNES | facility and service capacity snapshots by module, UF, and month | FTP DBC files by submodule, for example `CNES/200508_/Dados/ST/STCE2401.dbc` | facility inventory, SUS linkage, establishment type, selected service/capacity proxies |
| IBGE population | territory-year demographics | SIDRA/API JSON, CSV/XLSX export | denominators for incidence, mortality, hospitalizations, and capacity ratios |
| IBGE malhas | municipality territorial geometry | GeoJSON from the Malhas API, cached during ingestion | MVP 1 public aggregate municipality maps only |
| IBGE intramunicipal or municipal open geography, normalized | public submunicipal reference polygons | normalized GeoJSON under `data/raw/public_sources/ibge_intramunicipal/`; FeatureCollection properties `territory_id`, `name`, `territory_type`, `parent_id`, `uf_code`, `uf_sigla`; Polygon or MultiPolygon geometry | contextual bairro/reference overlays only; no TB indicators, ranking, scenarios, or health-territory inference |
| SIA/SUS | UF-month ambulatory production records | FTP DBC files by SIA layout/module; procedure interpretation requires SIGTAP | optional diagnostic/ambulatory production proxies, not a required first release source |
| SIGTAP | procedure terminology and attributes | public tables/downloads | procedure-code dictionary for SIA/SUS and selected SIH/SUS analyses |
| SISAB/e-Gestor APS | aggregate APS production and coverage | public reports, CSV/XLSX/ODS where available | optional APS context; not required for first public-data MVP |
| Site-TB | drug-resistant TB management records | restricted/authorized access; not open public bulk data | future institutional integration for DR-TB burden and follow-up |
| IL-TB/Silt/Vigilantos | TB preventive treatment records | restricted/authorized access or specific public reports | future institutional/manual-report integration for preventive treatment initiation |
| Local SINAN export | line list or local aggregate | CSV/XLSX/DBF depending on partner | local operational management |
| Local lab export | lab request/result line list | CSV/XLSX/API depending on partner | diagnostic workflow |
| Local pharmacy export | medication dispensing events | CSV/XLSX/API depending on partner | adherence proxy |
| Questionnaire | voluntary response | app database, CSV export | screening and barriers |

## Interoperability strategy

The project should avoid designing a custom universe where standards already exist.

Relevant patterns:

- FHIR `Patient`, `Observation`, `Condition`, `DiagnosticReport`, `MedicationRequest`, `MedicationDispense`, `Encounter`, `Questionnaire`, and `QuestionnaireResponse` for future patient-level integration;
- WHO SMART Guidelines and TB Digital Adaptation Kit for data dictionary, workflows, decision logic, indicators, and requirements;
- CSV/XLSX import templates for realistic municipal pilots;
- DBF/DBC conversion pipeline for DATASUS source files;
- GeoJSON/TopoJSON/PostGIS-compatible geometries for territorial analysis;
- API-first design for dashboards and future integrations.

Interoperability should be incremental. The first implementation can use documented file imports, but the canonical model should not prevent later FHIR mapping.

## Security, privacy, and LGPD requirements

Security is a product feature, not a final checklist.

Minimum requirements:

- role-based access control;
- separation between public aggregate data and restricted local/patient data;
- audit logs for login, record view, export, edit, recommendation validation, and admin changes;
- no patient-level public maps;
- small-count suppression for public or shared maps;
- pseudonymization for patient-level analytics whenever possible;
- no CPF/CNS in independent MVPs;
- explicit legal basis and governance agreement for local data;
- retention policy by data source;
- secure backup and restore procedure;
- data export controls;
- environment separation between development, demonstration, and production;
- explicit review of availability, accessibility, acceptability, and quality impacts for AI-enabled
  features, especially hotspot mapping, adherence monitoring, chatbots, and community-led
  monitoring.

Suggested roles:

| Role | Access |
| --- | --- |
| Public viewer | public aggregate dashboards only |
| Municipal manager | aggregate indicators, rankings, recommendations |
| Surveillance professional | case and operational data authorized for surveillance |
| APS professional | assigned unit/team tasks and authorized patient/contact data |
| Data steward | import validation, source quality, metadata |
| Evidence steward | strategy library and guideline updates |
| System administrator | user and configuration management, no unnecessary clinical access |

## AI and model governance

The platform should start rule-based. AI should be introduced only where it solves a defined problem and can be validated.

Acceptable early uses:

- guideline summarization for internal drafting;
- explanation of why a rule fired;
- manager-facing report drafting from structured facts;
- clustering or trend detection for exploratory analysis;
- prioritization models after baseline rules exist.

Uses that should not be allowed:

- autonomous diagnosis;
- treatment prescription;
- unsourced clinical advice;
- hidden scoring that cannot be explained to users;
- patient-level risk models without validation, monitoring, and governance;
- using sensitive predictors without ethical review and fairness analysis.

ML-ready requirements:

- labeled outcome definition;
- training/validation split by time and territory;
- baseline rule comparison;
- drift monitoring;
- fairness review;
- model card;
- human override;
- rollback plan;
- audit trail for model version used in each output;
- assessment of privacy, confidentiality, non-discrimination, digital literacy, connectivity, and
  sustainability risks before deployment.

Cost and operational burden should be first-class inputs for future strategy scoring. The AI
treatment-monitoring cost-effectiveness literature suggests that staff time, travel, video review,
dose frequency, and eligibility criteria can dominate the practical value of adherence technologies.
Those results should not be generalized to complex, drug-resistant, extrapulmonary, or highly
comorbid cases without local validation.

## Similar systems and design lessons

| System | Relevance | Main lesson |
| --- | --- | --- |
| WHO SMART Guidelines / TB Digital Adaptation Kit | Software-neutral TB digital requirements | Use structured personas, workflows, data dictionary, decision logic, indicators, and requirements before coding |
| Ni-kshay | National TB patient management and surveillance system in India | TB systems need case registration, lab orders, treatment details, adherence monitoring, transfer workflows, and surveillance reporting |
| DHIS2 | Health information, disease surveillance, dashboards, maps, Tracker, interoperability | Use configurable metadata, organizational hierarchy, aggregate and line-listed data, APIs, validation, and dashboards |
| SORMAS | Open-source disease surveillance and outbreak response | Model cases, contacts, labs, tasks, follow-up, field constraints, and operational states |
| WHO Go.Data | Outbreak case investigation and contact tracing | Support low-connectivity data collection, contact follow-up, real-time analysis, and field operations |
| OpenMRS | Open-source EMR | Use concept dictionaries, modular clinical records, REST/FHIR APIs, and local adaptation patterns |
| CommCare | Frontline data collection and case management | Offline-first questionnaire and case workflows can be a product, not only a form |
| OpenSRP | FHIR-native frontline health worker platform | Community/facility workflows benefit from registries, offline operation, and standards-based data models |
| InfoDengue | Brazilian public-data surveillance dashboard | Public territorial intelligence should expose indicators, reports, APIs, and clear communication |
| Mosqlimate | Brazilian data and model platform for arboviruses | Separate datastore, model registry, predictions, and dashboards |
| Boletim Epidemiologico Tuberculose 2026 | Official Brazilian TB epidemiological and operational indicator reference | Use official formulas, sources, exclusions, and periods for the MVP 1 indicator dictionary |
| AI-driven TB hotspot mapping in Nigeria | TB active case-finding site selection using Bayesian modeling and a geoportal | Future hotspot modules need local screening-event data, contextual covariates, field planning workflows, and prospective validation |
| AI and right-to-health analysis for TB | Rights-based review of TB AI technologies | AI features must be evaluated for privacy, bias, acceptability, accessibility, quality, community participation, and sustainability |
| AI treatment monitoring cost-effectiveness study | Cost-effectiveness comparison of AI monitoring and DOT | Future adherence modules should model staff time, travel, review workload, eligibility, cost, and uncertainty |

## Validation and quality plan

Validation should happen at multiple levels.

Data validation:

- schema checks;
- required field checks;
- code list checks;
- time range checks;
- duplicate detection;
- denominator availability;
- source freshness matched to geographic scope and year;
- explicit SIH/SUS monthly coverage for annual outputs;
- missingness reports.

Indicator validation:

- reproduce known public values for selected municipalities;
- compare against TabNet/manual calculations;
- unit tests for numerator and denominator logic;
- snapshot tests for scenario classification;
- audit CAP-04 public-signal availability, overlap, provenance, ranking isolation,
  and the absence of confirmed public resistance burden;
- review by epidemiology/domain expert.

Workflow validation:

- task creation from rule output;
- task assignment and closure;
- alert discard path;
- audit log generation;
- role permission tests.
- preserve resistance evidence classes and source provenance without exposing
  patient pseudonyms;

Usability validation:

- manager can identify top priority territories;
- surveillance professional can understand why a territory was flagged;
- APS professional can act on a queue item without duplicate data entry;
- users can distinguish recommendation, alert, and diagnosis.
- users can distinguish a public territorial surveillance gap from explicit,
  risk-history, and missing-evidence operational signals;

Safety validation:

- no diagnosis language in Layer 0 outputs;
- no patient location exposure;
- no small-count public maps;
- no generative AI recommendation without evidence source;
- clear human validation requirement.
- no confirmed resistance burden inferred from public aggregate signals;
- no new CAP-04 ranking contribution before an explicit reviewed decision;
- no real municipal source before GOV-01 approval.

## Non-functional requirements

Initial targets:

- reproducible local development environment;
- deterministic indicator generation;
- source import logs;
- dashboard response time acceptable for municipal datasets;
- accessible UI language for health teams;
- Portuguese-first interface for Brazilian users;
- exportable reports for meetings and validation;
- clear degraded mode when data are stale or incomplete.

Future municipal deployment requirements:

- local installation option;
- backup and restore;
- encrypted storage for sensitive data;
- HTTPS and secure authentication;
- environment-specific configuration;
- monitoring and error reporting;
- update and migration process;
- documented administrator operations.

## Open engineering decisions

The following decisions remain open for validation or later deployment;
implemented choices are recorded explicitly:

The current execution order and completion status for these decisions are
maintained in `proximos_passos.md`.

1. Which Boletim 2026 indicators are mandatory for the first public-data release, and which should
   remain backlog items?
1. MVP 1 now supports direct DATASUS file transfer into local DBC samples, DBF/DBC ingestion, and manual CSV fallback. For CE/2023, the default denominator is IBGE Census 2022 resident population from SIDRA table 4714; rates must be labeled as 2023 events over 2022 Census population. Remaining decision: which public-source extracts become the validated acceptance dataset.
1. The implemented public geographic scopes are one UF at a time or Brazil (`uf=BR`). National scope orchestrates the 27 UFs and uses national percentiles for national ranking; UF views can use either intra-UF percentiles or national comparison when national scenarios are available.
1. The implemented demonstration reference year is 2023. Remaining decision: which historical and
   prospective periods form the validated acceptance and trend-analysis windows?
1. Which indicators are mandatory for the first scenario classification?
1. Which thresholds are fixed by guidelines and which are relative rankings?
1. The public demonstration map is municipality-level, with optional public submunicipal reference
   overlays that do not affect TB prioritization. Any future health-territory granularity remains a
   governance and data-availability decision.
1. The implemented first UI combines the dashboard, territorial dossier, and read-only transparent
   recommendations. Recommendation approval and workflow validation remain future work.
1. Will the strategy library be stored as structured configuration, database tables, or Markdown?
1. What user roles exist in MVP 1 if there is no patient-level data?
1. What is the minimum validation dataset for acceptance?
1. The implemented demo target is local FastAPI, SQLite, and a compiled React SPA. No production
   deployment target has been selected.
1. Which parts of the WHO TB Digital Adaptation Kit will be adopted directly?
1. What evidence threshold is required before adopting any hotspot model beyond transparent
   rule-based territorial prioritization?
1. How should cost, staff time, travel, and operational complexity be measured for strategy scoring?

## Definition of done for MVP 1

MVP 1 is complete only when:

1. Public source contracts are documented.
1. Data ingestion is reproducible.
1. Canonical territory and indicator tables exist.
1. Indicator definitions are versioned.
1. At least one indicator can be reproduced against a public source manually.
1. Scenario rules are transparent and configurable.
1. Priority ranking includes explanations and caveats.
1. Recommendations come from a structured strategy library.
1. Dashboard displays data freshness and source caveats.
1. Small-count and privacy rules are enforced for public outputs.
1. Tests cover indicator calculations and scenario rules.
1. A domain reviewer can audit why a territory was classified as priority.

## Practical build recommendation

The implemented first slice intentionally focuses on the smallest coherent
public-data product through this sequence:

1. Import IBGE territorial identifiers and 2022 Census resident population denominators for CE/2023.
1. Import or load selected SINAN-TB public indicators.
1. Compute a small indicator dictionary.
1. Classify territories with transparent rules.
1. Link each subscenario to a strategy in the evidence library.
1. Show a dashboard with rankings, explanations, and caveats.
1. Validate results against manual public-source calculations.
1. Generate SINAN mapping and indicator sanity validation reports, and keep SINAN-derived formulas provisional until domain review.

Public ingestion, canonical storage, transparent rules, recommendations, the
dashboard, and technical validation reports are implemented for the demo.
Manual reproduction against an acceptance dataset and domain review remain
required. The synthetic municipal data-contract pilot is implemented as a
separate governed slice; questionnaires and real municipal integrations remain
future work.
