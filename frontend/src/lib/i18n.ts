export type Language = "pt" | "en";

export const supportedLanguages: Language[] = ["pt", "en"];

export function normalizeLanguage(value: string | null): Language {
  return value === "en" ? "en" : "pt";
}

export const copy = {
  pt: {
    appName: "TB-IA",
    appSubtitle: "Inteligência territorial para tuberculose",
    nav: {
      territorial: "Análise territorial",
      operations: "Acompanhamento da atenção",
      governance: "Dados e governança",
    },
    languageToggle: "English",
    navigationLabel: "Navegação principal",
    openMenu: "Abrir menu",
    closeMenu: "Fechar menu",
    common: {
      all: "Todos",
      apply: "Aplicar",
      loading: "Carregando dados",
      unavailable: "Dados indisponíveis",
      empty: "Nenhum registro encontrado",
      year: "Ano",
      uf: "Território",
      comparison: "Comparação",
      national: "Percentis nacionais",
      ufRanking: "Ranking na UF",
      status: "Situação",
      severity: "Gravidade",
      source: "Fonte",
      detail: "Detalhe",
    },
    concept: {
      visualConcept: "Painel municipal",
      managerConsole: "Painel gestor de saúde",
      currentVersion: "Interface atual",
      susName: "Sistema Único de Saúde",
      ministryOfHealth: "Ministério da Saúde",
      publicData: "Dados públicos",
      alerts: "Alertas",
      reports: "Relatórios",
      userManagement: "Gestão de usuários",
      settings: "Configurações",
      help: "Ajuda",
      territorialBrief:
        "Mapa, priorização e prontidão em uma superfície de decisão para vigilância e atenção primária.",
      operationsBrief:
        "Fila de revisão para equipes municipais acompanharem pendências, prazos e sinais operacionais.",
      rankingBrief:
        "Lista compacta para triagem rápida; expanda quando precisar comparar todo o escopo.",
      readinessBrief:
        "Estado das fontes públicas, geometria, validação e geração dos sinais territoriais.",
      queueBrief:
        "Pendências priorizadas para revisão humana, sem diagnóstico ou prescrição automatizada.",
      alertDetailBrief:
        "Resumo do sinal, contexto da equipe e próximos pontos de revisão.",
      teamBrief:
        "Distribuição de alertas por unidade e equipe para organizar a rotina local.",
      searchQueue: "Buscar caso, unidade ou equipe",
    },
    territorial: {
      title: "Análise territorial",
      subtitle:
        "Priorização municipal com dados públicos agregados e contexto submunicipal de referência.",
      publicBadge: "dado público agregado",
      commandScope: "Escopo de análise",
      metrics: {
        municipalities: "Municípios no escopo",
        indicators: "Valores de indicadores",
        signals: "Sinais territoriais",
        readiness: "Prontidão geral",
      },
      mapTitle: "Mapa territorial",
      mapMode: "Visualização",
      priorityMode: "Prioridade municipal",
      referenceMode: "Bairros de referência",
      layer: "Camada",
      municipalitySearch: "Buscar município",
      rankingTitle: "Municípios prioritários",
      rankingSubtitle: "Seleção sincronizada com o mapa e o painel de detalhe.",
      selectedTitle: "Detalhe do município",
      selectedEmpty: "Selecione um município no mapa ou ranking.",
      whyFlagged: "Por que foi sinalizado",
      recommendedResponse: "Resposta recomendada",
      indicators: "Indicadores",
      caveats: "Ressalvas",
      referenceCaveat:
        "Bairros são referência geográfica pública; indicadores e priorização de TB permanecem no nível municipal.",
      dataReadiness: "Prontidão dos dados",
      healthTerritories: "Territórios de saúde",
      sourceFreshness: "Atualização das fontes",
      noSignals: "Sem sinais territoriais para o escopo selecionado.",
      expandRanking: "Expandir ranking",
      collapseRanking: "Ocultar ranking",
      rankingCollapsed:
        "Ranking oculto para facilitar a leitura inicial. Expanda para ver e filtrar a lista completa.",
      loadYearTitle: "Dados do ano selecionado não estão processados",
      loadYearText:
        "A aplicação pode tentar baixar arquivos públicos do DATASUS/IBGE para o escopo e ano selecionados e recalcular indicadores e cenários.",
      loadYearButton: "Carregar ano selecionado",
      loadYearRunning: "Carregando dados públicos",
      loadYearDone: "Carga concluída. Atualizando painel.",
      loadYearFailed:
        "Não foi possível concluir a carga automática. Verifique as fontes públicas e tente novamente.",
      loadYearProgress: "Progresso da carga",
      loadYearStep: "Etapa",
      loadYearTechnicalError: "Detalhe técnico",
      loadYearHint:
        "Para Brasil inteiro a carga pode demorar; a ação só inicia quando você confirma no botão.",
      mapHelp:
        "O mapa usa polígonos públicos e não exibe dados de paciente, endereço ou alertas operacionais.",
    },
    operations: {
      title: "Acompanhamento da atenção",
      subtitle:
        "Fila operacional transparente para revisão das equipes municipais.",
      syntheticBadge: "demonstração sintética/pseudonimizada",
      caveat:
        "Alertas são filas de revisão operacional; não diagnosticam, não prescrevem e não substituem julgamento profissional.",
      localCases: "Casos locais",
      totalAlerts: "Alertas gerados",
      openAlerts: "Alertas abertos",
      highAlerts: "Alta gravidade",
      filters: "Filtros da fila",
      queue: "Fila operacional",
      facilityTeams: "Unidades e equipes",
      alertDetail: "Detalhe do alerta",
      selectAlert: "Selecione um alerta para ver o detalhe.",
      case: "Caso local",
      due: "Prazo",
      reference: "Referência",
      signal: "Sinal",
      team: "Equipe",
      facility: "Unidade",
      type: "Tipo",
    },
    statuses: {
      ready: "pronto",
      partial: "parcial",
      warning: "atenção",
      missing: "ausente",
      complete: "completo",
      open: "aberto",
      closed: "fechado",
    },
    severities: {
      high: "maior atenção",
      moderate: "atenção moderada",
      low: "menor atenção",
      none: "sem sinal",
    },
    alertTypes: {
      pending_lab_result: "Resultado laboratorial pendente",
      medication_pickup_delay: "Atraso na retirada de medicamento",
      contact_pending_evaluation: "Contato sem avaliação",
      resistance_vigilance: "Vigilância de resistência",
    },
  },
  en: {
    appName: "TB-IA",
    appSubtitle: "Territorial intelligence for tuberculosis",
    nav: {
      territorial: "Territorial analysis",
      operations: "Care follow-up",
      governance: "Data and governance",
    },
    languageToggle: "Português",
    navigationLabel: "Primary navigation",
    openMenu: "Open menu",
    closeMenu: "Close menu",
    common: {
      all: "All",
      apply: "Apply",
      loading: "Loading data",
      unavailable: "Data unavailable",
      empty: "No records found",
      year: "Year",
      uf: "Territory",
      comparison: "Comparison",
      national: "National percentiles",
      ufRanking: "Within-state ranking",
      status: "Status",
      severity: "Severity",
      source: "Source",
      detail: "Detail",
    },
    concept: {
      visualConcept: "Municipal console",
      managerConsole: "Health manager console",
      currentVersion: "Current interface",
      susName: "Brazilian Unified Health System",
      ministryOfHealth: "Ministry of Health",
      publicData: "Public data",
      alerts: "Alerts",
      reports: "Reports",
      userManagement: "User management",
      settings: "Settings",
      help: "Help",
      territorialBrief:
        "Map, prioritization, and readiness in one decision surface for surveillance and primary care.",
      operationsBrief:
        "Review queue for municipal teams to follow pending tasks, due dates, and operational signals.",
      rankingBrief:
        "Compact list for quick triage; expand when the full scope needs comparison.",
      readinessBrief:
        "Status of public sources, geometry, validation, and generated territorial signals.",
      queueBrief:
        "Prioritized pending items for human review, without automated diagnosis or prescription.",
      alertDetailBrief:
        "Signal summary, team context, and next review points.",
      teamBrief:
        "Alert distribution by facility and team to organize local routines.",
      searchQueue: "Search case, facility, or team",
    },
    territorial: {
      title: "Territorial analysis",
      subtitle:
        "Municipality prioritization with public aggregate data and contextual submunicipal references.",
      publicBadge: "public aggregate data",
      commandScope: "Analysis scope",
      metrics: {
        municipalities: "Municipalities in scope",
        indicators: "Indicator values",
        signals: "Territorial signals",
        readiness: "Overall readiness",
      },
      mapTitle: "Territorial map",
      mapMode: "View",
      priorityMode: "Municipality priority",
      referenceMode: "Reference neighborhoods",
      layer: "Layer",
      municipalitySearch: "Search municipality",
      rankingTitle: "Priority municipalities",
      rankingSubtitle:
        "Selection is synchronized with the map and detail panel.",
      selectedTitle: "Municipality detail",
      selectedEmpty: "Select a municipality on the map or ranking.",
      whyFlagged: "Why flagged",
      recommendedResponse: "Recommended response",
      indicators: "Indicators",
      caveats: "Caveats",
      referenceCaveat:
        "Neighborhoods are public geographic references; TB indicators and prioritization remain municipality-level.",
      dataReadiness: "Data readiness",
      healthTerritories: "Health territories",
      sourceFreshness: "Source freshness",
      noSignals: "No territorial signals for the selected scope.",
      expandRanking: "Expand ranking",
      collapseRanking: "Hide ranking",
      rankingCollapsed:
        "Ranking is hidden to keep the first view compact. Expand it to view and filter the full list.",
      loadYearTitle: "Selected year data is not processed",
      loadYearText:
        "The app can try to download public DATASUS/IBGE files for the selected scope and year, then recompute indicators and scenarios.",
      loadYearButton: "Load selected year",
      loadYearRunning: "Loading public data",
      loadYearDone: "Load completed. Refreshing dashboard.",
      loadYearFailed:
        "Automatic load could not be completed. Check public sources and try again.",
      loadYearProgress: "Load progress",
      loadYearStep: "Step",
      loadYearTechnicalError: "Technical detail",
      loadYearHint:
        "For the full Brazil scope this can take a while; the action only starts after you confirm with the button.",
      mapHelp:
        "The map uses public polygons and does not display patient, address, or operational alert locations.",
    },
    operations: {
      title: "Care follow-up",
      subtitle: "Transparent operational queue for municipal team review.",
      syntheticBadge: "synthetic/pseudonymized demo",
      caveat:
        "Alerts are operational review queues; they do not diagnose, prescribe, or replace professional judgment.",
      localCases: "Local cases",
      totalAlerts: "Generated alerts",
      openAlerts: "Open alerts",
      highAlerts: "High severity",
      filters: "Queue filters",
      queue: "Operational queue",
      facilityTeams: "Facilities and teams",
      alertDetail: "Alert detail",
      selectAlert: "Select an alert to view detail.",
      case: "Local case",
      due: "Due",
      reference: "Reference",
      signal: "Signal",
      team: "Team",
      facility: "Facility",
      type: "Type",
    },
    statuses: {
      ready: "ready",
      partial: "partial",
      warning: "warning",
      missing: "missing",
      complete: "complete",
      open: "open",
      closed: "closed",
    },
    severities: {
      high: "higher attention",
      moderate: "moderate attention",
      low: "lower attention",
      none: "no signal",
    },
    alertTypes: {
      pending_lab_result: "Pending laboratory result",
      medication_pickup_delay: "Medication pickup delay",
      contact_pending_evaluation: "Contact pending evaluation",
      resistance_vigilance: "Resistance vigilance",
    },
  },
} as const;

export type AppCopy = (typeof copy)[Language];
