from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

DEFAULT_LANGUAGE = "pt"
FALLBACK_LANGUAGE = "en"
SUPPORTED_LANGUAGES = frozenset({"pt", "en"})

UI_TEXT: dict[str, dict[str, Any]] = {
    "en": {
        "language_name": "English",
        "other_language_name": "Português",
        "language_label": "Language",
        "nav_label": "Product navigation",
        "product_subtitle": "Tuberculosis intelligence",
        "territorial_nav": "Territorial analysis",
        "care_nav": "Care follow-up",
        "current_context": "Current context",
        "year": "Year",
        "mvp1_nav": "Territorial analysis",
        "mvp2_nav": "Care follow-up",
        "apply": "Apply",
        "all": "All",
        "comparison_scope_labels": {
            "uf": "selected UF",
            "national": "Brazil",
        },
        "mvp1": {
            "title": "Territorial analysis",
            "subtitle": "Public municipality-level intelligence for tuberculosis planning",
            "badge_public": "public aggregate",
            "scope_label": "Current data scope",
            "scope_controls": "Scope controls",
            "comparison_scope": "Comparison",
            "comparison_badge_prefix": "comparison",
            "caveat": (
                "Public aggregate dashboard. Small counts are suppressed and outputs are "
                "decision support for professional review, not diagnosis."
            ),
            "data_readiness": "Data readiness",
            "data_governance": "Data and governance",
            "data_governance_note": (
                "Source status, public-data limits, and readiness for health-territory context."
            ),
            "summary_metrics": "Summary metrics",
            "territories": "territories",
            "indicator_values": "indicator values",
            "triggered_scenarios": "active signals",
            "territorial_map": "Territorial priority map",
            "map_view": "Map view",
            "municipality_priority": "Municipal priority",
            "reference_neighborhoods": "Reference neighborhoods",
            "health_territories": "Health territories",
            "health_territory_note": (
                "Public-source readiness for health-territory context; TB priority remains "
                "municipality-level."
            ),
            "municipality": "Municipality",
            "search_municipality": "Search municipality",
            "severity": "Severity",
            "data_status": "Data status",
            "layer": "Layer",
            "map_alt": "Municipality choropleth map",
            "map_legend": "Map legend",
            "lower_concern": "lower concern",
            "moderate_concern": "moderate concern",
            "higher_concern": "higher concern",
            "priority_ranking": "Priority municipalities",
            "loading_ranking": "Loading ranking...",
            "territory": "Territory",
            "score": "Score",
            "scenarios": "Signals",
            "top_scenario": "Main signal",
            "data": "Data",
            "explanation": "Explanation",
            "no_scenarios_generated": (
                "No territorial signals have been generated yet. Run the ingest, "
                "compute-indicators, and build-scenarios commands."
            ),
            "source_freshness": "Source freshness",
            "source": "Source",
            "status": "Status",
            "rows": "Rows",
            "message": "Message",
            "caveats": "Caveats",
            "no_import_runs": "No import runs recorded yet.",
        },
        "mvp2": {
            "title": "Care follow-up",
            "subtitle": "operational review queue",
            "badge_synthetic": "synthetic/pseudonymized demo",
            "caveat": (
                "Synthetic/pseudonymized operational pilot. Alerts are transparent review queues "
                "and do not diagnose, prescribe, or replace professional judgment."
            ),
            "local_cases": "local cases",
            "total_alerts": "total alerts",
            "open_alerts": "open alerts",
            "filters": "Worklist filters",
            "type": "Type",
            "severity": "Severity",
            "facility": "Facility",
            "team": "Team",
            "status": "Status",
            "queues": "Queues by facility/team",
            "alerts": "Alerts",
            "high": "High",
            "moderate": "Moderate",
            "open": "Open",
            "no_operational_alerts": "No operational alerts generated yet.",
            "alert_queue": "Operational alert queue",
            "case": "Case",
            "due": "Due",
            "signal": "Signal",
            "no_alert_matches": "No alerts match the selected filters.",
        },
        "health_territory_readiness": {
            "public_subterritory_geometry": "Public reference geometry",
            "cnes_facility_context": "CNES facility context",
            "official_health_territory_boundaries": "Official health-territory boundaries",
            "tb_health_territory_indicators": "TB indicators by health territory",
            "public_reference_polygons": "public reference polygons",
            "cnes_facilities": "CNES facilities",
            "municipalities": "municipalities",
            "not_available_public_mvp": "not available from current public sources",
        },
        "readiness": {
            "public_sources": "Public sources",
            "hospitalization_coverage": "Annual SIH/SUS coverage",
            "geometry": "Geometry",
            "indicator_validation": "Indicator validation",
            "generated_scenarios": "Generated signals",
            "diagnostic_scenario_rules": "Diagnostic coverage prioritization",
            "core_sources_successful": "core public source runs successful",
            "municipalities_with_geometry": "municipalities with geometry",
            "with": "with",
            "warnings": "warning(s)",
            "no_validation_run": "No validation run recorded",
            "scenarios_in": "scenarios in",
            "territories": "territories",
        },
        "status_labels": {
            "ready": "ready",
            "partial": "partial",
            "warning": "warning",
            "missing": "missing",
            "missing_indicator": "indicator missing",
            "insufficient_comparison": "insufficient comparison coverage",
            "pending_domain_review": "pending domain review",
            "success": "success",
            "failed": "failed",
            "skipped": "skipped",
            "complete": "complete",
            "open": "open",
            "resolved": "resolved",
            "dismissed": "dismissed",
        },
        "severity_labels": {
            "high": "high",
            "moderate": "moderate",
            "low": "low",
            "none": "none",
        },
        "alert_types": {
            "pending_lab_result": "pending lab result",
            "medication_pickup_delay": "medication pickup delay",
            "contact_pending_evaluation": "contact pending evaluation",
            "resistance_vigilance": "resistance vigilance",
        },
        "js": {
            "layer_labels": {
                "priority_score": "Priority score",
                "scenario_count": "Scenario count",
                "tb_incidence_per_100k": "TB incidence",
                "tb_mortality_per_100k": "TB mortality",
                "cure_proportion": "Cure proportion",
                "treatment_interruption_proportion": "Treatment interruption proportion",
                "laboratory_confirmation_proportion": "Laboratory confirmation proportion",
            },
            "municipality_detail": "Municipality detail",
            "select_municipality": "Select a municipality.",
            "map_renderer_unavailable": (
                "Map renderer unavailable. Check access to the Leaflet CDN."
            ),
            "map_data_unavailable": (
                "Map data unavailable. Run ingestion and verify cached IBGE Malhas geometry."
            ),
            "no_geometry": (
                "No municipality geometries available. Run ingestion to cache IBGE Malhas data."
            ),
            "subterritory_caveat": (
                "Reference neighborhoods are public geographic context; TB indicators and "
                "prioritization remain municipality-level."
            ),
            "subterritory_select_municipality": (
                "Select a municipality to view reference neighborhoods."
            ),
            "subterritory_loading": "Loading reference neighborhoods...",
            "subterritory_empty": (
                "No public reference neighborhoods available for this municipality."
            ),
            "subterritory_unavailable": "Reference neighborhoods unavailable.",
            "reference_neighborhoods": "Reference neighborhoods",
            "public_reference": "public reference",
            "unavailable": "Unavailable",
            "loading": "Loading...",
            "detail_unavailable": "Detail unavailable.",
            "municipalities": "municipalities",
            "no_ranking_matches": "No municipalities match the selected filters.",
            "no_scenario": "No scenario",
            "why_flagged": "Why flagged",
            "recommended_response": "Recommended response",
            "indicators": "Indicators",
            "caveats": "Caveats",
            "priority_score": "Priority score",
            "scenarios": "Signals",
            "top_severity": "Top severity",
            "data_status": "Data status",
            "no_scenarios_triggered": "No scenarios triggered.",
            "no_recommendations": "No recommendations generated.",
            "no_indicators": "No indicator values.",
            "no_caveats": "No caveats recorded.",
            "indicator": "Indicator",
            "value": "Value",
            "status": "Status",
            "direction": "Direction",
            "public_aggregate": "public aggregate",
            "suppressed_caveat": (
                "Suppressed public values are hidden by minimum-count rules and are "
                "not treated as zero."
            ),
            "missing_caveat": (
                "Missing values indicate unavailable, suppressed, or not computable public data."
            ),
            "suppressed": "suppressed",
            "missing": "missing",
            "reported": "reported",
            "higher_needs_attention": "higher needs attention",
            "lower_needs_attention": "lower needs attention",
            "context": "context",
            "per_100k": "per 100k",
            "status_labels": {
                "complete": "complete",
                "partial": "partial",
                "missing": "missing",
            },
            "severity_labels": {
                "high": "high",
                "moderate": "moderate",
                "low": "low",
                "none": "none",
            },
        },
    },
    "pt": {
        "language_name": "Português",
        "other_language_name": "English",
        "language_label": "Idioma",
        "nav_label": "Navegação do produto",
        "product_subtitle": "Inteligência em tuberculose",
        "territorial_nav": "Análise territorial",
        "care_nav": "Acompanhamento da atenção",
        "current_context": "Contexto atual",
        "year": "Ano",
        "mvp1_nav": "Análise territorial",
        "mvp2_nav": "Acompanhamento da atenção",
        "apply": "Aplicar",
        "all": "Todos",
        "comparison_scope_labels": {
            "uf": "UF selecionada",
            "national": "Brasil",
        },
        "mvp1": {
            "title": "Análise territorial",
            "subtitle": "Inteligência pública municipal para planejamento em tuberculose",
            "badge_public": "dado público agregado",
            "scope_label": "Escopo de dados atual",
            "scope_controls": "Controles de escopo",
            "comparison_scope": "Comparação",
            "comparison_badge_prefix": "comparação",
            "caveat": (
                "Painel com dados públicos agregados. Pequenos números são suprimidos e as "
                "saídas apoiam a revisão profissional; não são diagnóstico."
            ),
            "data_readiness": "Prontidão dos dados",
            "data_governance": "Dados e governança",
            "data_governance_note": (
                "Situação das fontes, limites dos dados públicos e prontidão para contexto "
                "territorial de saúde."
            ),
            "summary_metrics": "Indicadores-resumo",
            "territories": "territórios",
            "indicator_values": "valores de indicadores",
            "triggered_scenarios": "sinais ativos",
            "territorial_map": "Mapa de prioridade territorial",
            "map_view": "Visualização do mapa",
            "municipality_priority": "Prioridade municipal",
            "reference_neighborhoods": "Bairros de referência",
            "health_territories": "Territórios de saúde",
            "health_territory_note": (
                "Prontidão das fontes públicas para contexto de territórios de saúde; "
                "a priorização de TB permanece no nível municipal."
            ),
            "municipality": "Município",
            "search_municipality": "Buscar município",
            "severity": "Gravidade",
            "data_status": "Situação dos dados",
            "layer": "Camada",
            "map_alt": "Mapa coroplético municipal",
            "map_legend": "Legenda do mapa",
            "lower_concern": "menor atenção",
            "moderate_concern": "atenção moderada",
            "higher_concern": "maior atenção",
            "priority_ranking": "Municípios prioritários",
            "loading_ranking": "Carregando ranking...",
            "territory": "Território",
            "score": "Pontuação",
            "scenarios": "Sinais",
            "top_scenario": "Sinal principal",
            "data": "Dados",
            "explanation": "Explicação",
            "no_scenarios_generated": (
                "Nenhum sinal territorial foi gerado ainda. Execute os comandos ingest, "
                "compute-indicators e build-scenarios."
            ),
            "source_freshness": "Atualização das fontes",
            "source": "Fonte",
            "status": "Situação",
            "rows": "Linhas",
            "message": "Mensagem",
            "caveats": "Ressalvas",
            "no_import_runs": "Nenhuma execução de importação registrada ainda.",
        },
        "mvp2": {
            "title": "Acompanhamento da atenção",
            "subtitle": "fila operacional de revisão",
            "badge_synthetic": "demonstração sintética/pseudonimizada",
            "caveat": (
                "Piloto operacional sintético/pseudonimizado. Os alertas são filas transparentes "
                "de revisão e não diagnosticam, prescrevem ou substituem o julgamento profissional."
            ),
            "local_cases": "casos locais",
            "total_alerts": "alertas totais",
            "open_alerts": "alertas abertos",
            "filters": "Filtros da fila",
            "type": "Tipo",
            "severity": "Gravidade",
            "facility": "Unidade",
            "team": "Equipe",
            "status": "Situação",
            "queues": "Filas por unidade/equipe",
            "alerts": "Alertas",
            "high": "Alta",
            "moderate": "Moderada",
            "open": "Abertos",
            "no_operational_alerts": "Nenhum alerta operacional foi gerado ainda.",
            "alert_queue": "Fila operacional de alertas",
            "case": "Caso",
            "due": "Prazo",
            "signal": "Sinal",
            "no_alert_matches": "Nenhum alerta corresponde aos filtros selecionados.",
        },
        "health_territory_readiness": {
            "public_subterritory_geometry": "Geometria pública de referência",
            "cnes_facility_context": "Contexto CNES de unidades",
            "official_health_territory_boundaries": "Limites oficiais de territórios de saúde",
            "tb_health_territory_indicators": "Indicadores de TB por território de saúde",
            "public_reference_polygons": "polígonos públicos de referência",
            "cnes_facilities": "unidades CNES",
            "municipalities": "municípios",
            "not_available_public_mvp": "indisponível nas fontes públicas atuais",
        },
        "readiness": {
            "public_sources": "Fontes públicas",
            "hospitalization_coverage": "Cobertura anual do SIH/SUS",
            "geometry": "Geometria",
            "diagnostic_scenario_rules": "Priorização da cobertura diagnóstica",
            "indicator_validation": "Validação dos indicadores",
            "generated_scenarios": "Sinais gerados",
            "core_sources_successful": "fontes públicas centrais com sucesso",
            "municipalities_with_geometry": "municípios com geometria",
            "with": "com",
            "warnings": "aviso(s)",
            "no_validation_run": "Nenhuma validação registrada",
            "scenarios_in": "cenários em",
            "territories": "territórios",
        },
        "status_labels": {
            "ready": "pronto",
            "partial": "parcial",
            "missing_indicator": "indicador ausente",
            "insufficient_comparison": "cobertura comparativa insuficiente",
            "pending_domain_review": "revisão de domínio pendente",
            "warning": "atenção",
            "missing": "ausente",
            "success": "sucesso",
            "failed": "falha",
            "skipped": "ignorado",
            "complete": "completo",
            "open": "aberto",
            "resolved": "resolvido",
            "dismissed": "descartado",
        },
        "severity_labels": {
            "high": "alta",
            "moderate": "moderada",
            "low": "baixa",
            "none": "nenhuma",
        },
        "alert_types": {
            "pending_lab_result": "resultado laboratorial pendente",
            "medication_pickup_delay": "atraso na retirada de medicamento",
            "contact_pending_evaluation": "avaliação de contato pendente",
            "resistance_vigilance": "vigilância de resistência",
        },
        "js": {
            "layer_labels": {
                "priority_score": "Pontuação de prioridade",
                "scenario_count": "Quantidade de cenários",
                "tb_incidence_per_100k": "Incidência de TB",
                "tb_mortality_per_100k": "Mortalidade por TB",
                "cure_proportion": "Proporção de cura",
                "treatment_interruption_proportion": "Proporção de interrupção do tratamento",
                "laboratory_confirmation_proportion": "Proporção de confirmação laboratorial",
            },
            "municipality_detail": "Detalhe do município",
            "select_municipality": "Selecione um município.",
            "map_renderer_unavailable": (
                "Renderizador do mapa indisponível. Verifique o acesso ao CDN do Leaflet."
            ),
            "map_data_unavailable": (
                "Dados do mapa indisponíveis. Execute a ingestão e verifique a geometria "
                "IBGE Malhas em cache."
            ),
            "no_geometry": (
                "Nenhuma geometria municipal disponível. Execute a ingestão para armazenar "
                "dados do IBGE Malhas."
            ),
            "subterritory_caveat": (
                "Bairros são referência geográfica pública; indicadores e priorização de TB "
                "permanecem no nível municipal."
            ),
            "subterritory_select_municipality": (
                "Selecione um município para ver bairros de referência."
            ),
            "subterritory_loading": "Carregando bairros de referência...",
            "subterritory_empty": (
                "Nenhum bairro de referência público disponível para este município."
            ),
            "subterritory_unavailable": "Bairros de referência indisponíveis.",
            "reference_neighborhoods": "Bairros de referência",
            "public_reference": "referência pública",
            "unavailable": "Indisponível",
            "loading": "Carregando...",
            "detail_unavailable": "Detalhe indisponível.",
            "municipalities": "municípios",
            "no_ranking_matches": "Nenhum município corresponde aos filtros selecionados.",
            "no_scenario": "Sem cenário",
            "why_flagged": "Por que foi sinalizado",
            "recommended_response": "Resposta recomendada",
            "indicators": "Indicadores",
            "caveats": "Ressalvas",
            "priority_score": "Pontuação de prioridade",
            "scenarios": "Sinais",
            "top_severity": "Maior gravidade",
            "data_status": "Situação dos dados",
            "no_scenarios_triggered": "Nenhum cenário acionado.",
            "no_recommendations": "Nenhuma recomendação gerada.",
            "no_indicators": "Nenhum valor de indicador.",
            "no_caveats": "Nenhuma ressalva registrada.",
            "indicator": "Indicador",
            "value": "Valor",
            "status": "Situação",
            "direction": "Direção",
            "public_aggregate": "dado público agregado",
            "suppressed_caveat": (
                "Valores públicos suprimidos ficam ocultos por regras de contagem mínima "
                "e não são tratados como zero."
            ),
            "missing_caveat": (
                "Valores ausentes indicam dados públicos indisponíveis, suprimidos ou "
                "não computáveis."
            ),
            "suppressed": "suprimido",
            "missing": "ausente",
            "reported": "informado",
            "higher_needs_attention": "maior valor requer atenção",
            "lower_needs_attention": "menor valor requer atenção",
            "context": "contexto",
            "per_100k": "por 100 mil",
            "status_labels": {
                "complete": "completo",
                "partial": "parcial",
                "missing": "ausente",
            },
            "severity_labels": {
                "high": "alta",
                "moderate": "moderada",
                "low": "baixa",
                "none": "nenhuma",
            },
        },
    },
}

INDICATOR_LABELS_PT = {
    "tb_incidence_per_100k": "Incidência de TB",
    "tb_mortality_per_100k": "Mortalidade por TB",
    "cure_proportion": "Proporção de cura",
    "treatment_interruption_proportion": "Proporção de interrupção do tratamento",
    "retreatment_proportion": "Proporção de retratamento",
    "laboratory_confirmation_proportion": "Proporção de confirmação laboratorial",
    "hiv_testing_proportion": "Proporção de testagem para HIV",
    "tb_hiv_burden_proportion": "Carga TB-HIV",
    "trm_tb_use_proportion": "Proporção de uso de TRM-TB",
    "culture_use_among_retreatment": "Uso de cultura entre retratamentos",
    "hospitalization_burden_per_100k": "Carga de internações por TB",
}

INDICATOR_CAVEATS_PT = {
    "tb_incidence_per_100k": (
        "Usa território de residência e mapeamento oficial do tipo de entrada de casos novos."
    ),
    "tb_mortality_per_100k": (
        "Usa território de residência, salvo configuração de análise diferente."
    ),
    "cure_proportion": (
        "Depende do mapeamento oficial da situação de encerramento e da definição "
        "do período de coorte."
    ),
    "treatment_interruption_proportion": (
        "Usa a terminologia brasileira atual para abandono/interrupção."
    ),
    "retreatment_proportion": "Requer mapeamento oficial das categorias de tipo de entrada.",
    "laboratory_confirmation_proportion": (
        "Transformações derivadas de DBC devem evitar dupla contagem dos campos "
        "de confirmação laboratorial."
    ),
    "hiv_testing_proportion": (
        "Requer mapeamento das categorias positivo, negativo, em andamento e não realizado."
    ),
    "tb_hiv_burden_proportion": (
        "Usa resultado HIV positivo no universo de casos novos; a comorbidade AIDS "
        "é auditada separadamente."
    ),
    "trm_tb_use_proportion": (
        "Requer mapeamento do campo de teste rápido molecular e exclusões não aplicáveis."
    ),
    "culture_use_among_retreatment": "Combina tipo de entrada, forma pulmonar e campos de cultura.",
    "hospitalization_burden_per_100k": (
        "Interpreta internações como proxy de gravidade ou fluxo assistencial, não como incidência."
    ),
}

SOURCE_LABELS_EN = {
    "cnes": "CNES",
    "ibge_localidades": "IBGE Localidades",
    "ibge_malhas": "IBGE territorial meshes",
    "ibge_intramunicipal": "Normalized public intramunicipal references",
    "ibge_population": "IBGE population denominator",
    "indicator_validation": "Indicator sanity validation",
    "local_contacts": "Pseudonymized contact investigations",
    "local_lab_events": "Pseudonymized local lab events",
    "local_pharmacy_dispensing": "Pseudonymized pharmacy dispensing",
    "local_resources": "Local resource inventory",
    "local_tb_cases": "Pseudonymized local TB cases",
    "local_teams": "Local team registry",
    "local_territories": "Local territory registry",
    "operational_alerts": "Generated operational alerts",
    "sih_sus": "SIH/SUS",
    "sim": "SIM",
    "sinan_tb": "SINAN-TB / DATASUS",
    "sinan_validation": "SINAN-TB mapping audit",
}

SOURCE_LABELS_PT = {
    "cnes": "CNES",
    "ibge_localidades": "IBGE Localidades",
    "ibge_malhas": "IBGE Malhas territoriais",
    "ibge_intramunicipal": "IBGE intramunicipal normalizado",
    "ibge_population": "Denominador populacional IBGE",
    "indicator_validation": "Validação de sanidade dos indicadores",
    "local_contacts": "Investigações de contatos pseudonimizadas",
    "local_lab_events": "Eventos laboratoriais locais pseudonimizados",
    "local_pharmacy_dispensing": "Dispensação farmacêutica pseudonimizada",
    "local_resources": "Inventário local de recursos",
    "local_tb_cases": "Casos locais de TB pseudonimizados",
    "local_teams": "Cadastro local de equipes",
    "local_territories": "Cadastro local de territórios",
    "operational_alerts": "Alertas operacionais gerados",
    "sih_sus": "SIH/SUS",
    "sim": "SIM",
    "sinan_tb": "SINAN-TB / DATASUS",
    "sinan_validation": "Auditoria de mapeamento SINAN-TB",
}

SOURCE_CAVEATS_PT = {
    "ibge_localidades": "Limites territoriais e cadastro municipal podem mudar ao longo do tempo.",
    "ibge_population": (
        "Estimativas populacionais e valores censitários não devem ser misturados sem metadados."
    ),
    "ibge_malhas": (
        "Malha web simplificada para visualização territorial; não é fonte de localização "
        "de pacientes ou endereços."
    ),
    "ibge_intramunicipal": (
        "Bairros ou polígonos intramunicipais públicos são contexto geográfico; não "
        "representam territórios oficiais de saúde nem indicadores de TB por bairro."
    ),
    "sinan_tb": (
        "Mapeamentos oficiais de tipo de entrada, encerramento, HIV, TRM-TB e "
        "cultura exigem revisão."
    ),
    "sinan_validation": (
        "Auditoria técnica dos efeitos da transformação atual; ainda requer revisão "
        "de domínio contra dicionários e cadernos oficiais."
    ),
    "indicator_validation": (
        "Valida invariantes mecânicos de saída pública; não substitui revisão de domínio."
    ),
}

RULE_BASE_EXPLANATIONS_PT = {
    "high_incidence": (
        "A incidência de TB está igual ou acima do limiar p75 para a UF/ano selecionados."
    ),
    "high_mortality": (
        "A mortalidade por TB está igual ou acima do limiar p75 para a UF/ano selecionados."
    ),
    "high_treatment_interruption": "A interrupção do tratamento está igual ou acima do limiar p75.",
    "low_cure": "A proporção de cura está igual ou abaixo do limiar p25.",
    "high_retreatment": "A proporção de retratamento está igual ou acima do limiar p75.",
    "low_lab_confirmation": "A confirmação laboratorial está igual ou abaixo do limiar p25.",
    "high_tb_hiv_burden": "A carga TB-HIV está igual ou acima do limiar p75.",
    "high_hospitalization_burden": (
        "A carga de internações por TB está igual ou acima do limiar p75."
    ),
    "low_hiv_testing": (
        "Regra comparativa provisória: a testagem para HIV está igual ou abaixo do limiar p25."
    ),
    "low_trm_tb_use": (
        "Regra comparativa provisória: o uso de TRM-TB está igual ou abaixo do limiar p25."
    ),
    "low_culture_use_among_retreatment": (
        "Regra comparativa provisória: o uso de cultura entre casos pulmonares de "
        "retratamento está igual ou abaixo do limiar p25."
    ),
}

RULE_LABELS_PT = {
    "high_incidence": "alta incidência",
    "high_mortality": "alta mortalidade",
    "high_treatment_interruption": "alta interrupção do tratamento",
    "low_cure": "baixa cura",
    "high_retreatment": "alto retratamento",
    "low_lab_confirmation": "baixa confirmação laboratorial",
    "high_tb_hiv_burden": "alta carga TB-HIV",
    "high_hospitalization_burden": "alta carga de internações",
    "low_hiv_testing": "baixa testagem para HIV",
    "low_trm_tb_use": "baixo uso de TRM-TB",
    "low_culture_use_among_retreatment": "baixo uso de cultura no retratamento",
}

ALERT_MESSAGE_TEMPLATES = {
    "en": {
        "pending_lab_result": "Laboratory result pending for case {case_id}.",
        "medication_pickup_delay": ("Medication pickup is delayed for open case {case_id}."),
        "contact_pending_evaluation": ("Contact evaluation is pending for index case {case_id}."),
        "resistance_vigilance": "Resistance vigilance for case {case_id}.",
    },
    "pt": {
        "pending_lab_result": "Resultado laboratorial pendente para o caso {case_id}.",
        "medication_pickup_delay": (
            "Retirada de medicamento atrasada para o caso aberto {case_id}."
        ),
        "contact_pending_evaluation": (
            "Avaliação de contato pendente para o caso índice {case_id}."
        ),
        "resistance_vigilance": "Vigilância de resistência para o caso {case_id}.",
    },
}

DASHBOARD_READINESS_KEYS = frozenset(
    {
        "public_sources",
        "hospitalization_coverage",
        "geometry",
        "indicator_validation",
        "diagnostic_scenario_rules",
        "generated_scenarios",
    }
)
HEALTH_TERRITORY_READINESS_KEYS = frozenset(
    {
        "public_subterritory_geometry",
        "cnes_facility_context",
        "official_health_territory_boundaries",
        "tb_health_territory_indicators",
    }
)


def normalize_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


def language_context(language: str | None) -> dict[str, Any]:
    lang = normalize_language(language)
    other_lang = "en" if lang == "pt" else "pt"
    return {
        "lang": lang,
        "html_lang": "pt-BR" if lang == "pt" else "en",
        "other_lang": other_lang,
        "tr": UI_TEXT[lang],
    }


def localize_dashboard_context(context: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(context)
    localized["caveat"] = UI_TEXT[language]["mvp1"]["caveat"]
    localized["sources"] = [localize_source_row(row, language) for row in context["sources"]]
    localized["scenario_rule_evaluations"] = [
        localize_scenario_rule_evaluation_row(row, language)
        for row in context.get("scenario_rule_evaluations", [])
    ]
    hospitalization_source = next(
        (
            row
            for row in context["sources"]
            if isinstance(row, Mapping) and row.get("source_id") == "sih_sus"
        ),
        None,
    )
    localized["readiness"] = localize_readiness_items(
        context["readiness"],
        language,
        hospitalization_source=hospitalization_source,
    )
    localized["health_territory_readiness"] = localize_readiness_items(
        context["health_territory_readiness"],
        language,
    )
    if language == "pt":
        localized["ranking"] = [localize_ranking_row(row, language) for row in context["ranking"]]
    return localized


def localize_readiness_items(
    items: Mapping[str, Any],
    language: str,
    *,
    hospitalization_source: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    localized_items: dict[str, Any] = {}
    for key, item in items.items():
        if not isinstance(item, Mapping):
            localized_items[key] = item
            continue

        localized_item = dict(item)
        if key in DASHBOARD_READINESS_KEYS:
            localized_item["label"] = UI_TEXT[language]["readiness"][key]
        elif key in HEALTH_TERRITORY_READINESS_KEYS:
            localized_item["label"] = UI_TEXT[language]["health_territory_readiness"][key]
        else:
            localized_items[key] = localized_item
            continue

        localized_item["detail"] = localized_readiness_detail(
            key,
            item,
            language,
            hospitalization_source=hospitalization_source,
        )
        localized_items[key] = localized_item
    return localized_items


def localized_readiness_detail(
    key: str,
    item: Mapping[str, Any],
    language: str,
    *,
    hospitalization_source: Mapping[str, Any] | None,
) -> str:
    if key == "hospitalization_coverage":
        return localized_hospitalization_coverage_detail(
            hospitalization_source,
            language,
        )
    formatter = READINESS_DETAIL_FORMATTERS.get(key)
    if formatter is None:
        return str(item.get("detail", ""))
    return formatter(item, language)


def localized_public_sources_detail(item: Mapping[str, Any], language: str) -> str:
    successful = readiness_count(item.get("success_count"))
    expected = readiness_count(item.get("expected_count"))
    return language_text(
        language,
        pt=(
            f"{successful}/{expected} execuções das fontes públicas centrais concluídas com sucesso"
        ),
        en=f"{successful}/{expected} core public source runs successful",
    )


def localized_geometry_detail(item: Mapping[str, Any], language: str) -> str:
    geometry_count = readiness_count(item.get("geometry_count"))
    territory_count = readiness_count(item.get("territory_count"))
    return language_text(
        language,
        pt=f"{geometry_count}/{territory_count} municípios com geometria",
        en=f"{geometry_count}/{territory_count} municipalities with geometry",
    )


def localized_indicator_validation_detail(
    item: Mapping[str, Any],
    language: str,
) -> str:
    source_status = str(item.get("source_status", "missing"))
    if source_status == "missing":
        return language_text(
            language,
            pt="Nenhuma execução de validação registrada",
            en="No validation run recorded",
        )
    warning_count = readiness_count(item.get("warning_count"))
    status = localized_status(source_status, language)
    if not warning_count:
        return status
    return language_text(
        language,
        pt=f"{status} com {warning_count} {'aviso' if warning_count == 1 else 'avisos'}",
        en=f"{status} with {warning_count} {'warning' if warning_count == 1 else 'warnings'}",
    )


def localized_diagnostic_scenario_rules_detail(
    item: Mapping[str, Any],
    language: str,
) -> str:
    ready_count = readiness_count(item.get("ready_count"))
    evaluation_count = readiness_count(item.get("evaluation_count"))
    insufficient_count = readiness_count(item.get("insufficient_count"))
    missing_count = readiness_count(item.get("missing_count"))
    return language_text(
        language,
        pt=(
            f"{ready_count}/{evaluation_count} avaliações de regras diagnósticas prontas; "
            f"{insufficient_count} com cobertura comparativa insuficiente; "
            f"{missing_count} com indicadores ausentes"
        ),
        en=(
            f"{ready_count}/{evaluation_count} diagnostic rule evaluations ready; "
            f"{insufficient_count} with insufficient comparison coverage; "
            f"{missing_count} missing indicators"
        ),
    )


def localized_generated_scenarios_detail(
    item: Mapping[str, Any],
    language: str,
) -> str:
    scenario_count = readiness_count(item.get("scenario_count"))
    territory_count = readiness_count(item.get("territory_count"))
    return language_text(
        language,
        pt=f"{scenario_count} sinais gerados em {territory_count} territórios",
        en=f"{scenario_count} generated signals in {territory_count} territories",
    )


def localized_public_subterritory_geometry_detail(
    item: Mapping[str, Any],
    language: str,
) -> str:
    drawable_count = readiness_count(item.get("drawable_geometry_count"))
    feature_count = readiness_count(item.get("feature_count"))
    return language_text(
        language,
        pt=(
            f"{drawable_count}/{feature_count} polígonos públicos de referência "
            "disponíveis para detalhamento contextual"
        ),
        en=(
            f"{drawable_count}/{feature_count} public reference polygons available "
            "for contextual drill-down"
        ),
    )


def localized_cnes_facility_context_detail(
    item: Mapping[str, Any],
    language: str,
) -> str:
    facility_count = readiness_count(item.get("facility_count"))
    municipality_count = readiness_count(item.get("municipality_count"))
    return language_text(
        language,
        pt=(
            f"{facility_count} registros públicos de unidades CNES em "
            f"{municipality_count} municípios"
        ),
        en=(
            f"{facility_count} public CNES facility records in {municipality_count} municipalities"
        ),
    )


def localized_health_boundaries_detail(
    _item: Mapping[str, Any],
    language: str,
) -> str:
    return language_text(
        language,
        pt=(
            "Limites oficiais de UBS, equipes e microáreas não estão disponíveis "
            "nas fontes exclusivamente públicas atuais."
        ),
        en=(
            "Official UBS, team, and microarea boundaries are not available from "
            "the current public-only sources."
        ),
    )


def localized_health_indicators_detail(
    _item: Mapping[str, Any],
    language: str,
) -> str:
    return language_text(
        language,
        pt=(
            "Desfechos de TB por UBS, equipe, microárea ou bairro não são calculados "
            "nesta versão; os indicadores públicos de TB permanecem no nível municipal."
        ),
        en=(
            "TB outcomes by UBS, team, microarea, or neighborhood are not computed in "
            "this version; public TB indicators remain municipality-level."
        ),
    )


def localized_hospitalization_coverage_detail(
    source: Mapping[str, Any] | None,
    language: str,
) -> str:
    if source is None:
        return language_text(
            language,
            pt="Nenhuma execução de importação do SIH/SUS registrada para o escopo",
            en="No scoped SIH/SUS import run recorded",
        )

    coverage = source.get("month_coverage")
    if not isinstance(coverage, Mapping):
        return language_text(
            language,
            pt="A cobertura mensal do SIH/SUS não foi registrada",
            en="SIH/SUS monthly coverage was not recorded",
        )

    scope_count = readiness_count(coverage.get("scope_count"), default=1)
    if scope_count > 1:
        return localized_hospitalization_scope_detail(coverage, language, scope_count)
    return localized_hospitalization_month_detail(coverage, language)


def localized_hospitalization_scope_detail(
    coverage: Mapping[str, Any],
    language: str,
    scope_count: int,
) -> str:
    complete_count = readiness_count(coverage.get("complete_scope_count"))
    return language_text(
        language,
        pt=(f"{complete_count}/{scope_count} UFs com cobertura completa de 12 meses do SIH/SUS"),
        en=(f"{complete_count}/{scope_count} states with complete 12-month SIH/SUS coverage"),
    )


def localized_hospitalization_month_detail(
    coverage: Mapping[str, Any],
    language: str,
) -> str:
    loaded_months = coverage.get("loaded_months")
    if not isinstance(loaded_months, list):
        return language_text(
            language,
            pt="Cobertura mensal do SIH/SUS desconhecida; indicadores anuais são excluídos",
            en="SIH/SUS monthly coverage is unknown; annual indicators are excluded",
        )

    expected_months = coverage.get("expected_months")
    expected_count = len(expected_months) if isinstance(expected_months, list) else 12
    detail = language_text(
        language,
        pt=f"{len(loaded_months)}/{expected_count} meses do SIH/SUS carregados",
        en=f"{len(loaded_months)}/{expected_count} SIH/SUS months loaded",
    )

    missing_months = coverage.get("missing_months")
    if not isinstance(missing_months, list) or not missing_months:
        return detail
    missing = ", ".join(f"{readiness_count(month):02d}" for month in missing_months)
    return language_text(
        language,
        pt=f"{detail}; faltam {missing}",
        en=f"{detail}; missing {missing}",
    )


def language_text(language: str, *, pt: str, en: str) -> str:
    return pt if language == "pt" else en


def readiness_count(value: object, *, default: int = 0) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


ReadinessDetailFormatter = Callable[[Mapping[str, Any], str], str]
READINESS_DETAIL_FORMATTERS: dict[str, ReadinessDetailFormatter] = {
    "public_sources": localized_public_sources_detail,
    "geometry": localized_geometry_detail,
    "indicator_validation": localized_indicator_validation_detail,
    "generated_scenarios": localized_generated_scenarios_detail,
    "diagnostic_scenario_rules": localized_diagnostic_scenario_rules_detail,
    "public_subterritory_geometry": localized_public_subterritory_geometry_detail,
    "cnes_facility_context": localized_cnes_facility_context_detail,
    "official_health_territory_boundaries": localized_health_boundaries_detail,
    "tb_health_territory_indicators": localized_health_indicators_detail,
}


def localize_mvp2_context(context: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(context)
    localized["caveat"] = UI_TEXT[language]["mvp2"]["caveat"]
    localized["alerts"] = [localize_alert_row(row, language) for row in context["alerts"]]
    return localized


def localize_map_payload(payload: dict[str, Any], language: str) -> dict[str, Any]:
    if language == FALLBACK_LANGUAGE:
        return payload
    localized = deepcopy(payload)
    layers = localized.get("metadata", {}).get("layers", {})
    for layer_id, layer in layers.items():
        if layer_id in INDICATOR_LABELS_PT:
            layer["label"] = INDICATOR_LABELS_PT[layer_id]
        elif layer_id in UI_TEXT[language]["js"]["layer_labels"]:
            layer["label"] = UI_TEXT[language]["js"]["layer_labels"][layer_id]

    for feature in localized.get("features", []):
        properties = feature.get("properties", {})
        for indicator_id, indicator in properties.get("indicators", {}).items():
            indicator["name"] = indicator_label(indicator_id, language, indicator.get("name"))
        top_scenarios = [
            localize_scenario_row(row, language) for row in properties.get("top_scenarios", [])
        ]
        properties["top_scenarios"] = top_scenarios
        properties["top_explanations"] = [row["explanation"] for row in top_scenarios]
    return localized


def localize_subterritory_payload(payload: dict[str, Any], language: str) -> dict[str, Any]:
    if language == FALLBACK_LANGUAGE:
        return payload
    localized = deepcopy(payload)
    metadata = localized.get("metadata", {})
    if isinstance(metadata, dict):
        metadata["caveat"] = UI_TEXT[language]["js"]["subterritory_caveat"]
    return localized


def localize_territory_report(report: dict[str, Any], language: str) -> dict[str, Any]:
    if language == FALLBACK_LANGUAGE:
        return report
    localized = deepcopy(report)
    localized["indicators"] = [
        localize_indicator_row(row, language) for row in report.get("indicators", [])
    ]
    localized["scenarios"] = [
        localize_scenario_row(row, language) for row in report.get("scenarios", [])
    ]
    localized["recommendations"] = [
        localize_recommendation_row(row, language) for row in report.get("recommendations", [])
    ]
    return localized


def localize_ranking_row(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    top_scenarios = [localize_scenario_row(item, language) for item in row.get("top_scenarios", [])]
    localized["top_scenarios"] = top_scenarios
    localized["top_explanations"] = [item["explanation"] for item in top_scenarios]
    return localized


def localize_source_row(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    source_id = str(row.get("source_id", ""))
    labels = SOURCE_LABELS_PT if language == "pt" else SOURCE_LABELS_EN
    localized["name"] = labels.get(source_id, product_source_text(str(row.get("name", source_id))))
    localized["message"] = product_source_text(str(row.get("message", "")))
    if language == "pt":
        localized["caveats"] = SOURCE_CAVEATS_PT.get(
            source_id, product_source_text(str(row.get("caveats", "")))
        )
    else:
        localized["caveats"] = product_source_text(str(row.get("caveats", "")))
    return localized


def product_source_text(value: str) -> str:
    replacements = {
        "loaded MVP2 local CSV": "loaded local demonstration CSV",
        "generated MVP2 operational alerts": "generated operational alerts",
        "MVP1 ": "",
        "MVP2 ": "",
        "MVP1": "",
        "MVP2": "",
    }
    text = value
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def localize_indicator_row(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    indicator_id = str(row.get("indicator_id", ""))
    localized["indicator_name"] = indicator_label(
        indicator_id, language, localized.get("indicator_name")
    )
    if language == "pt":
        localized["caveats"] = indicator_caveat_pt(indicator_id, str(row.get("caveats", "")))
    return localized


def localize_scenario_row(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    if language == "pt":
        rule_id = str(row.get("rule_id", ""))
        localized["explanation"] = scenario_explanation_pt(rule_id, row)
    return localized


def localize_scenario_rule_evaluation_row(
    row: Mapping[str, Any],
    language: str,
) -> dict[str, Any]:
    localized = dict(row)
    rule_id = str(row.get("rule_id", ""))
    if language == "pt":
        localized["rule_name"] = RULE_LABELS_PT.get(rule_id, rule_id.replace("_", " "))
    localized["status_label"] = localized_status(str(row.get("status", "")), language)
    review_status = row.get("review_status")
    if isinstance(review_status, str):
        localized["review_status_label"] = localized_status(review_status, language)
    return localized


def localize_recommendation_row(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    if language == "pt":
        rule_id = str(row.get("rule_id", ""))
        raw_rule_ids = row.get("trigger_rule_ids")
        rule_ids = (
            [str(item) for item in raw_rule_ids]
            if isinstance(raw_rule_ids, list) and raw_rule_ids
            else [rule_id]
        )
        rule_labels = [RULE_LABELS_PT.get(item, item.replace("_", " ")) for item in rule_ids]
        if len(rule_labels) == 1:
            reason = f"a regra de {rule_labels[0]} foi acionada"
        else:
            reason = f"as regras de {', '.join(rule_labels)} foram acionadas"
        localized["explanation"] = (
            f"Recomendado porque {reason}. Isto é apoio à decisão e requer revisão profissional."
        )
    return localized


def localize_alert_row(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    alert_type = str(row.get("alert_type", ""))
    severity = str(row.get("severity", ""))
    status = str(row.get("status", ""))
    labels = UI_TEXT[language]
    localized["alert_type_label"] = labels["alert_types"].get(
        alert_type, alert_type.replace("_", " ")
    )
    localized["severity_label"] = labels["severity_labels"].get(severity, severity)
    localized["status_label"] = labels["status_labels"].get(status, status)
    if language == "pt":
        template = ALERT_MESSAGE_TEMPLATES["pt"].get(alert_type)
        if template:
            localized["message_label"] = template.format(case_id=row.get("local_case_id", ""))
        else:
            localized["message_label"] = row.get("message", "")
    else:
        localized["message_label"] = row.get("message", "")
    return localized


def localize_product_alert(row: Mapping[str, Any], language: str) -> dict[str, Any]:
    localized = dict(row)
    templates = ALERT_MESSAGE_TEMPLATES[normalize_language(language)]
    template = templates.get(str(row.get("alert_type", "")))
    if template is not None:
        localized["message"] = template.format(case_id=row.get("local_case_id", ""))
    return localized


def indicator_caveat_pt(indicator_id: str, original: str) -> str:
    caveat = INDICATOR_CAVEATS_PT.get(indicator_id, original)
    suffixes: list[str] = []
    if "Denominator unavailable or zero" in original:
        suffixes.append("Denominador indisponível ou igual a zero.")
    if "Suppressed for public output because numerator exceeds" in original:
        suffixes.append("Suprimido na saída pública porque o numerador excede o denominador.")
    if "Suppressed for public output because count is below" in original:
        suffixes.append(
            "Suprimido na saída pública porque a contagem está abaixo do mínimo definido."
        )
    if suffixes:
        return " ".join([caveat, *suffixes])
    return caveat


def indicator_label(indicator_id: str, language: str, fallback: object = None) -> str:
    if language == "pt":
        return INDICATOR_LABELS_PT.get(indicator_id, str(fallback or indicator_id))
    return str(fallback or indicator_id)


def scenario_explanation_pt(rule_id: str, row: Mapping[str, Any]) -> str:
    base = RULE_BASE_EXPLANATIONS_PT.get(rule_id, rule_id.replace("_", " "))
    indicator_value = number_label(row.get("indicator_value"))
    threshold_value = number_label(row.get("threshold_value"))
    if indicator_value is None or threshold_value is None:
        return base
    return f"{base} Valor={indicator_value}; limiar={threshold_value}."


def number_label(value: object) -> str | None:
    if isinstance(value, int | float):
        return f"{float(value):.2f}"
    return None


def localized_status(value: str, language: str) -> str:
    return str(UI_TEXT[language]["status_labels"].get(value, value))


def localized_severity(value: str | None, language: str) -> str:
    key = value or "none"
    return str(UI_TEXT[language]["severity_labels"].get(key, key))


def localized_alert_type(value: str, language: str) -> str:
    return str(UI_TEXT[language]["alert_types"].get(value, value.replace("_", " ")))
