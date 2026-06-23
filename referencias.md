# References for system design

This document collects prior work and related systems that can inform the design and development
of the TB-IA platform. The focus is not limited to tuberculosis. The most useful references are
those that combine public health surveillance, territorial analysis, operational dashboards, risk
prioritization, data quality, and human-in-the-loop decision support.

## Local project reference documents

The `documentos/` directory stores source PDFs used during project formulation and technical
planning. These files should be treated as evidence and context, not as application assets.

### Boletim Epidemiologico Tuberculose 2026

- Local file: `documentos/boletim_epidemiologico_tuberculose_2026.pdf`
- Domain: official Brazilian tuberculosis epidemiological and operational indicators.
- Why it matters: this is the strongest source for the MVP 1 indicator dictionary. It defines
  official Brazilian formulas, periods, and data sources for incidence, mortality, laboratory
  confirmation, HIV testing, TB-HIV coinfection, contacts examined, treatment outcomes,
  retreatment, directly observed treatment, molecular testing, culture, drug-resistant TB,
  BPaL coverage, and preventive treatment.
- Useful design ideas:
  - make the MVP 1 indicator dictionary traceable to official Brazilian definitions;
  - store numerator, denominator, source, period, exclusions, and caveats per indicator;
  - separate Sinan indicators from SIM, IBGE, Site-TB, IL-TB/Silt/Vigilantos, and laboratory
    network indicators;
  - expose data freshness and source limitations on dashboards.

### Original Biochallenge project scope

- Local file: `documentos/Escopo - Biochallenge Brasil 2026.docx.pdf`
- Domain: original project proposal and challenge submission.
- Why it matters: it is the historical source for the project's product intent, beneficiaries,
  validation feedback, initial data assumptions, and 12-week roadmap.
- Useful design ideas:
  - preserve the public-data-first MVP premise;
  - keep local micro-care integration as a future partnership-dependent layer;
  - maintain the health-safety boundary that the platform supports decision-making and does not
    diagnose, prescribe, or replace professionals.

### Effectiveness of Using AI-Driven Hotspot Mapping for Active Case Finding of Tuberculosis in Southwestern Nigeria

- Local file: `documentos/tropicalmed-09-00099.pdf`
- Link: <https://doi.org/10.3390/tropicalmed9050099>
- Domain: TB active case-finding site selection using Bayesian hotspot mapping and a geoportal.
- Why it matters: this is the closest direct reference for the proposed territorial AI module. It
  combines active case-finding outputs, contextual covariates, population clusters, predictive
  hotspot mapping, a geoportal for field teams, and a feedback loop where new screening results
  improve future predictions.
- Useful design ideas:
  - start with transparent public indicators, but design the architecture so local ACF events can
    later feed hotspot models;
  - model hotspot recommendations as decision support for field planning, not as autonomous
    targeting;
  - compare model-selected areas against conventional notification-based planning;
  - track yield, number screened, positivity, and whether the site was model-recommended.

### Strengthening the TB response with artificial intelligence and the right to health

- Local file: `documentos/ijtldopen25-0271.pdf`
- Link: <https://doi.org/10.5588/ijtldopen.25.0271>
- Domain: rights-based assessment of AI use in TB response.
- Why it matters: this paper directly supports governance requirements for privacy,
  confidentiality, bias, accessibility, acceptability, sustainability, informed consent, and
  community participation.
- Useful design ideas:
  - evaluate AI features through availability, accessibility, acceptability, and quality;
  - require privacy and non-discrimination review for sensitive hotspot, adherence, chatbot, and
    community-monitoring features;
  - treat digital literacy, connectivity, and sustainability as product constraints;
  - keep community and professional oversight visible in the system design.

### Cost-effectiveness of artificial intelligence monitoring for active tuberculosis treatment

- Local file: `documentos/journal.pone.0254950.pdf`
- Link: <https://doi.org/10.1371/journal.pone.0254950>
- Domain: cost-effectiveness model comparing AI treatment monitoring with directly observed
  therapy.
- Why it matters: this is useful for future adherence and treatment-monitoring modules, not the
  first public-data MVP. It gives a structure for comparing staff time, travel burden, video review,
  treatment completion, costs, QALYs, and sensitivity analyses.
- Useful design ideas:
  - include cost and operational burden in future strategy scoring;
  - model staff time and travel as major implementation constraints;
  - avoid generalizing AI monitoring results beyond eligible, uncomplicated patient groups without
    local validation;
  - use sensitivity analysis when recommending resource-intensive interventions.

## Closest platform analogues

### InfoDengue

- Link: <https://info.dengue.mat.br/>
- Domain: dengue and other arbovirus surveillance in Brazil.
- Why it matters: this is one of the closest Brazilian references for a public health intelligence
  platform. It combines surveillance data, territorial indicators, public reports, an API-oriented
  data access layer, and operational outputs for municipalities and states.
- Useful design ideas:
  - municipality-level indicators;
  - public data access separated from reports and dashboards;
  - epidemiological alert outputs;
  - transparent communication of indicators and glossary terms.

### Mosqlimate

- Link: <https://api.mosqlimate.org/docs/>
- Domain: data and forecasting platform for arbovirus diseases in Brazil.
- Why it matters: Mosqlimate exposes disease notification data, climate time series, mosquito
  abundance data, a model registry, and forecast outputs. Its model/data separation is directly
  relevant for a future TB-IA architecture.
- Useful design ideas:
  - data store separated from model registry;
  - documented API access;
  - forecast dashboard fed by registered model outputs;
  - reproducibility expectations for models through code repositories.

### DHIS2

- Link: <https://dhis2.org/health/>
- Domain: open-source health management information system and surveillance platform.
- Why it matters: DHIS2 is a mature reference for configurable health data systems. It supports
  data collection, validation, analysis, dashboards, maps, user roles, APIs, and integration with
  external sources.
- Useful design ideas:
  - metadata-driven indicators;
  - organizational hierarchy for territories and services;
  - dashboard, chart, pivot table, and map layers;
  - role-based access and data sharing;
  - custom apps on top of a stable data platform.

### SORMAS

- Link: <https://www.sormas.org/>
- Domain: open-source disease surveillance and outbreak response management.
- Why it matters: SORMAS focuses on indicator- and event-based surveillance, early detection,
  outbreak management, laboratory integration, interoperability, and field use.
- Useful design ideas:
  - surveillance workflows instead of only static dashboards;
  - case, contact, lab, and follow-up concepts;
  - real-time operational views;
  - offline and field constraints;
  - governance and maintainability of public health software.

## Tuberculosis-specific references

### WHO handbook on digital technologies for TB medication adherence

- Link: <https://www.who.int/publications/i/item/9789241513456>
- Domain: digital technologies for TB treatment adherence.
- Why it matters: this is directly relevant to the future patient follow-up and adherence layer. It
  covers SMS, medication event monitoring systems, and video-supported treatment.
- Useful design ideas:
  - keep adherence tools separate from diagnosis and prescribing;
  - evaluate implementation context before selecting technology;
  - treat patient-level adherence as a partnership and governance-dependent module;
  - document evidence, cost, workflow impact, and user responsibilities.

### Learning to Prescribe Interventions for Tuberculosis Patients Using Digital Adherence Data

- Link: <https://arxiv.org/abs/1902.01506>
- Domain: TB adherence risk prediction using 99DOTS data in India.
- Why it matters: the paper uses real digital adherence data from about 17,000 patients and 2.1
  million dose records to predict missed doses and target interventions.
- Useful design ideas:
  - intervention targeting should account for health worker actions already present in the data;
  - risk outputs should be interpretable and operational;
  - model evaluation should compare against practical rule-based baselines;
  - decision-focused evaluation can be more useful than prediction metrics alone.

### Predicting Treatment Adherence of Tuberculosis Patients at Scale

- Link: <https://arxiv.org/abs/2211.02943>
- Domain: large-scale early prediction of TB treatment non-adherence.
- Why it matters: the paper discusses a large deployment-oriented ML problem using nearly 700,000
  patients from India.
- Useful design ideas:
  - plan for low-prevalence targets;
  - handle high-cardinality categorical variables;
  - test for distribution shift across territories and cohorts;
  - evaluate fairness and explainability before operational use;
  - optimize for prioritization/ranking, not only binary classification.

### Predictive Analysis of Tuberculosis Treatment Outcomes Using Machine Learning

- Link: <https://arxiv.org/abs/2403.08834>
- Domain: TB treatment outcome prediction using NIKSHAY data from India.
- Why it matters: it frames treatment outcome prediction as a large tabular ML problem using
  national TB program data.
- Useful design ideas:
  - patient-level outcome prediction requires authorized microdata;
  - tabular preprocessing and outcome definitions are central;
  - high performance in another country should not be treated as local validity;
  - local validation is mandatory before use in care prioritization.

### Epidemic-guided deep learning for spatiotemporal forecasting of Tuberculosis outbreak

- Link: <https://arxiv.org/abs/2502.10786>
- Domain: TB incidence forecasting with mechanistic epidemic modeling and deep learning.
- Why it matters: useful as a later research direction for forecasting TB incidence, not as a first
  MVP dependency.
- Useful design ideas:
  - combine mechanistic epidemic structure with data-driven models;
  - include uncertainty in forecasts;
  - avoid black-box forecasts without epidemiological interpretation;
  - start with simpler transparent indicators before advanced models.

## Surveillance and modeling methods

### Spatio-Temporal Analysis of Epidemic Phenomena Using the R Package surveillance

- Link: <https://arxiv.org/abs/1411.0416>
- Domain: statistical surveillance of infectious disease events and counts.
- Why it matters: this is a practical reference for working with aggregated regional/time-series
  disease counts, which is closer to the current public-data MVP than patient-level ML.
- Useful design ideas:
  - separate endemic background risk from epidemic deviations;
  - support visualization, inference, and simulation;
  - use aggregation by time and territory as a valid surveillance unit;
  - compare alerts against statistical baselines.

### Hierarchical Bayesian Modeling of Dengue in Recife

- Link: <https://arxiv.org/abs/2510.13672>
- Domain: spatial and temporal dengue risk mapping in Recife.
- Why it matters: not TB-specific, but relevant for territorial public health prioritization with
  socioeconomic and environmental covariates.
- Useful design ideas:
  - account for spatial autocorrelation;
  - include uncertainty intervals in maps and rankings;
  - test whether finer spatial granularity improves or harms reliability;
  - combine disease data with census and vulnerability covariates.

### Time Series Methods and Ensemble Models to Nowcast Dengue at the State Level in Brazil

- Link: <https://arxiv.org/abs/2006.02483>
- Domain: dengue nowcasting in Brazil using heterogeneous data streams.
- Why it matters: useful for thinking about future TB trend monitoring, although TB has a slower
  temporal dynamic than dengue.
- Useful design ideas:
  - compare multiple simple and complex time-series models;
  - use ensembles only when they clearly improve performance;
  - document the contribution of each data stream;
  - validate by geography because model performance can vary by state.

### An Accurate Gaussian Process-Based Early Warning System for Dengue Fever

- Link: <https://arxiv.org/abs/1608.03343>
- Domain: Bayesian non-parametric early warning for dengue.
- Why it matters: useful as a reference for probabilistic alerting and for thinking about
  uncertainty, even though TB should not be modeled as a dengue outbreak process.
- Useful design ideas:
  - probabilistic alerts are often more useful than point predictions;
  - flexible models may capture local dynamics better than rigid assumptions;
  - model outputs must still be translated into actionable public health signals.

### Early Detection of COVID-19 Hotspots Using Spatio-Temporal Data

- Link: <https://arxiv.org/abs/2106.00072>
- Domain: hotspot detection using spatio-temporal Bayesian methods.
- Why it matters: useful for hotspot concepts and early warning design, with the caveat that TB
  surveillance has different time scales and reporting delays.
- Useful design ideas:
  - define hotspot events explicitly;
  - model latent spatio-temporal dynamics;
  - compare hotspot detection performance against simpler baselines;
  - keep interpretability visible to public health users.

### A Bayesian modelling framework to quantify multiple sources of spatial variation for disease mapping

- Link: <https://arxiv.org/abs/2206.01500>
- Domain: Bayesian disease mapping with spatial variation.
- Why it matters: useful for understanding how to model spatial heterogeneity without forcing all
  areas to share the same risk process.
- Useful design ideas:
  - spatial structure can come from geography, mobility, shared vulnerability, or service access;
  - disease maps should communicate uncertainty;
  - use spatial models to generate hypotheses, not automatic causal claims.

## Dashboard and product evaluation

### A Framework for Evaluating Dashboards in Healthcare

- Link: <https://arxiv.org/abs/2009.04792>
- Domain: evaluation framework for healthcare dashboards.
- Why it matters: TB-IA should not be validated only by whether charts render. It should be
  validated by whether users can make safer, faster, and more auditable decisions.
- Useful design ideas:
  - evaluate task performance;
  - evaluate workflow fit;
  - evaluate perceived utility;
  - evaluate algorithm performance separately from interface usability;
  - include implementation and adoption risks in validation.

### OUTBREAK: A user-friendly georeferencing online tool for disease surveillance

- Link: <https://arxiv.org/abs/2004.10490>
- Domain: web-based georeferencing and outbreak visualization.
- Why it matters: useful as a lightweight prototype reference for non-specialist users who need to
  visualize epidemiological data.
- Useful design ideas:
  - make data upload and map generation simple;
  - keep visual tools accessible to non-technical public health teams;
  - avoid dependency on expensive proprietary geospatial tools for the MVP.

## Design implications for TB-IA

The MVP should be closer to InfoDengue, Mosqlimate, and DHIS2 than to a pure machine learning
paper. A pragmatic first version should emphasize:

- public aggregate data first;
- transparent indicators and denominators;
- municipality and territory-level rankings;
- reproducible data ingestion;
- auditable rules for prioritization;
- clear limits: support decision-making, do not diagnose or prescribe;
- visible uncertainty and data quality warnings;
- human validation before operational recommendations.

Patient-level adherence prediction, individualized risk scoring, and treatment intervention
assignment should remain future modules dependent on authorized local data, governance, LGPD
review, and validation with health professionals.
