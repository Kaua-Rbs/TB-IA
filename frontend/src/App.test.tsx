import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { maplibreMockState } from "./test/setup";

const rankingFixtures = [
  {
    territoryId: "2304400",
    name: "Fortaleza",
    score: 8,
    scenarioCount: 2,
    severity: "high",
    dataStatus: "complete",
  },
  {
    territoryId: "2303709",
    name: "Caucaia",
    score: 7.2,
    scenarioCount: 2,
    severity: "high",
    dataStatus: "partial",
  },
  {
    territoryId: "2307650",
    name: "Maracanaú",
    score: 6.4,
    scenarioCount: 1,
    severity: "moderate",
    dataStatus: "complete",
  },
  {
    territoryId: "2312908",
    name: "Sobral",
    score: 5.8,
    scenarioCount: 1,
    severity: "moderate",
    dataStatus: "partial",
  },
  {
    territoryId: "2307304",
    name: "Juazeiro do Norte",
    score: 4.9,
    scenarioCount: 1,
    severity: "low",
    dataStatus: "complete",
  },
  {
    territoryId: "2304202",
    name: "Crato",
    score: 4.2,
    scenarioCount: 1,
    severity: "low",
    dataStatus: "missing",
  },
  {
    territoryId: "2306405",
    name: "Itapipoca",
    score: 3.6,
    scenarioCount: 1,
    severity: "low",
    dataStatus: "complete",
  },
] as const;

const mapPayload = {
  type: "FeatureCollection",
  metadata: {
    geographic_scope: "BR",
    comparison_scope: "national",
    year: 2023,
    feature_count: rankingFixtures.length,
    drawable_geometry_count: rankingFixtures.length,
    layers: {
      priority_score: {
        label: "Pontuação de prioridade",
        kind: "property",
        unit: "score",
        direction: "high_bad",
      },
      scenario_count: {
        label: "Quantidade de sinais",
        kind: "property",
        unit: "count",
        direction: "high_bad",
      },
      tb_incidence_per_100k: {
        label: "Incidência de TB",
        kind: "indicator",
        unit: "per_100k",
        direction: "high_bad",
      },
    },
  },
  features: rankingFixtures.map((municipality, index) => {
    const isFortaleza = municipality.territoryId === "2304400";
    const explanation = isFortaleza
      ? "Testagem para HIV abaixo do comparativo"
      : municipality.name + " requer revisão territorial";
    return {
      type: "Feature",
      properties: {
        territory_id: municipality.territoryId,
        name: municipality.name,
        uf: "CE",
        priority_score: municipality.score,
        scenario_count: municipality.scenarioCount,
        top_severity: municipality.severity,
        top_explanations: [explanation],
        top_scenarios: [
          {
            rule_id: isFortaleza ? "low_hiv_testing" : "priority_signal",
            review_status: isFortaleza ? "pending_domain_review" : null,
            indicator_id: isFortaleza ? "hiv_testing_proportion" : "tb_incidence_per_100k",
            severity: municipality.severity,
            score: municipality.score,
            explanation,
          },
        ],
        data_status: municipality.dataStatus,
        indicators: isFortaleza
          ? {
              tb_incidence_per_100k: {
                name: "Incidência de TB",
                value: 80,
                is_suppressed: false,
                unit: "per_100k",
                direction: "high_bad",
              },
            }
          : {},
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [index, 0],
            [index + 0.75, 0],
            [index + 0.75, 0.75],
            [index, 0],
          ],
        ],
      },
    };
  }),
};

const territorialContext = {
  uf: "BR",
  geographic_scope: "BR",
  comparison_scope: "national",
  year: 2023,
  territory_count: rankingFixtures.length,
  indicator_count: 1,
  scenario_count: 9,
  caveat: "Painel público agregado.",
  ranking: rankingFixtures.map((municipality, index) => ({
    territory_id: municipality.territoryId,
    territory_name: municipality.name,
    score: municipality.score,
    scenario_count: municipality.scenarioCount,
    top_severity: municipality.severity,
    top_explanations: mapPayload.features[index].properties.top_explanations,
    top_scenarios: mapPayload.features[index].properties.top_scenarios,
  })),
  scenario_rule_evaluations: [],
  readiness: {
    geometry: {
      label: "Geometria",
      status: "ready",
      detail: "7/7 municípios com geometria",
    },
  },
  health_territory_readiness: {
    official_health_territory_boundaries: {
      label: "Limites oficiais de territórios de saúde",
      status: "missing",
      detail: "Indisponível em fontes públicas atuais.",
    },
  },
  sources: [
    {
      source_id: "fixture",
      name: "Fonte pública",
      status: "success",
      row_count: 1,
      finished_at: null,
      message: "ok",
      caveats: "",
      month_coverage: {
        expected_months: Array.from({ length: 12 }, (_, index) => index + 1),
        loaded_months: [1],
        missing_months: Array.from({ length: 11 }, (_, index) => index + 2),
        complete: false,
        scope_count: 1,
        complete_scope_count: 0,
      },
    },
  ],
};
function buildIncidenceHistory(english = false) {
  const years = [2018, 2019, 2020, 2021, 2022, 2023];
  const values = [60.3, 59.6, null, null, 59.6, 60.4];
  const numerators = [1593, 1591, null, null, 1447, 1467];
  const populations = [2643247, 2669342, 2686612, null, 2428708, 2428708];

  return {
    territory_id: "2304400",
    territory_name: "Fortaleza",
    uf: "CE",
    indicator_id: "tb_incidence_per_100k",
    indicator_name: english ? "TB incidence" : "Incidência de TB",
    unit: "per_100k",
    direction: "high_bad",
    start_year: 2018,
    end_year: 2023,
    coverage: {
      requested_year_count: 6,
      available_year_count: 4,
      suppressed_year_count: 1,
      missing_year_count: 1,
      provenance_incomplete_year_count: 0,
      status: "partial",
      status_label: english ? "partial" : "parcial",
    },
    comparability_flags: [
      {
        code: "suppressed_year",
        years: [2020],
        detail: english
          ? "At least one annual value is hidden by the minimum-count rule."
          : "Ao menos um valor anual está oculto pela regra de contagem mínima.",
      },
      {
        code: "source_release_changed",
        years: [2020],
        detail: english
          ? "The series crosses source releases with different finality status."
          : "A série atravessa versões da fonte com situações de fechamento diferentes.",
      },
      {
        code: "denominator_method_changed",
        years: [2022],
        detail: english
          ? "The population denominator changes between estimate and Census methods."
          : "O denominador populacional alterna entre estimativa e Censo.",
      },
      {
        code: "denominator_year_mismatch",
        years: [2023],
        detail: english
          ? "At least one rate uses a population reference year different from the event year."
          : "Ao menos uma taxa usa população de referência de ano diferente do evento.",
      },
    ],
    points: years.map((pointYear, index) => {
      const status =
        pointYear === 2020
          ? "suppressed"
          : pointYear === 2021
            ? "missing"
            : "available";
      const populationYear = pointYear === 2023 ? 2022 : pointYear;
      const preliminary = pointYear >= 2020;
      const census = pointYear >= 2022;
      return {
        year: pointYear,
        status,
        status_label:
          status === "available"
            ? english
              ? "available"
              : "disponível"
            : status === "suppressed"
              ? english
                ? "suppressed"
                : "suprimido"
              : english
                ? "missing"
                : "ausente",
        value: values[index],
        numerator_value: numerators[index],
        denominator_value: populations[index],
        denominator_year: status === "missing" ? null : populationYear,
        source_provenance:
          status === "missing"
            ? []
            : [
                {
                  source_id: "sinan_tb",
                  source_label: "SINAN-TB / DATASUS",
                  reference_year: pointYear,
                  release_status: preliminary ? "preliminary" : "final",
                  release_status_label: preliminary
                    ? english
                      ? "preliminary"
                      : "preliminar"
                    : "final",
                  dataset_kind: "notification",
                  dataset_kind_label: english
                    ? "notification records"
                    : "registros de notificação",
                  artifact_sha256: "a".repeat(64),
                },
                {
                  source_id: "ibge_population",
                  source_label: english ? "IBGE population" : "População IBGE",
                  reference_year: populationYear,
                  release_status: "final",
                  release_status_label: "final",
                  dataset_kind: census ? "census" : "estimate",
                  dataset_kind_label: census
                    ? english
                      ? "Census"
                      : "Censo"
                    : english
                      ? "population estimate"
                      : "estimativa populacional",
                  artifact_sha256: "b".repeat(64),
                },
              ],
        caveats:
          status === "missing"
            ? ""
            : english
              ? "Uses municipality of residence and the official new-case mapping."
              : "Usa município de residência e o mapeamento oficial de casos novos.",
      };
    }),
  };
}


const operationAlert = {
  alert_id: "alert-1",
  year: 2023,
  alert_type: "pending_lab_result",
  severity: "high",
  status: "open",
  local_case_id: "CASE-1",
  territory_id: "2304400",
  facility_id: "UBS-1",
  team_id: "TEAM-1",
  team_name: "Equipe Centro",
  related_entity_id: null,
  reference_date: "2026-06-29",
  generated_at: "2026-06-29T00:00:00",
  due_date: "2026-07-02",
  message: "Resultado laboratorial pendente.",
};

const secondOperationAlert = {
  ...operationAlert,
  alert_id: "alert-2",
  alert_type: "medication_pickup_delay",
  severity: "moderate",
  local_case_id: "CASE-2",
  due_date: "2026-07-04",
  message: "Retirada de medicamento atrasada.",
};

const englishOperationAlert = {
  ...operationAlert,
  message: "Laboratory result pending for case CASE-1.",
};

const secondEnglishOperationAlert = {
  ...secondOperationAlert,
  message: "Medication pickup is delayed for open case CASE-2.",
};

beforeEach(() => {
  maplibreMockState.fitBounds.mockClear();
  maplibreMockState.setFilter.mockClear();
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.includes("/api/territorial/context") && url.includes("year=2024")) {
      return jsonResponse({
        ...territorialContext,
        year: 2024,
        indicator_count: 0,
        scenario_count: 0,
        ranking: [],
      });
    }
    if (url.includes("/api/territorial/context"))
      return jsonResponse(territorialContext);
    if (url.includes("/api/territorial/map")) return jsonResponse(mapPayload);
    if (url.includes("/api/territorial/load-year/job-1")) {
      return jsonResponse({
        job_id: "job-1",
        uf: "BR",
        year: 2024,
        sih_all_months: true,
        status: "running",
        result_status: null,
        stage: "download",
        step_index: 1,
        step_count: 5,
        message: "1/4 baixando: SINAN-TB Brazil 2024 preliminary",
        download: null,
        indicator_count: 0,
        scenario_count: 0,
        recommendation_count: 0,
        error: null,
        created_at: "2026-07-07T00:00:00Z",
        started_at: "2026-07-07T00:00:01Z",
        updated_at: "2026-07-07T00:00:02Z",
        finished_at: null,
      });
    }
    if (url.includes("/api/territorial/load-year")) {
      return jsonResponse({
        job_id: "job-1",
        uf: "BR",
        year: 2024,
        sih_all_months: true,
        status: "queued",
        result_status: null,
        stage: "queued",
        step_index: 0,
        step_count: 5,
        message: "Carga aguardando início.",
        download: null,
        indicator_count: 0,
        scenario_count: 0,
        recommendation_count: 0,
        error: null,
        created_at: "2026-07-07T00:00:00Z",
        started_at: null,
        updated_at: "2026-07-07T00:00:00Z",
        finished_at: null,
      });
    }
    if (url.includes("/api/territorial/subterritories")) {
      return jsonResponse({
        type: "FeatureCollection",
        metadata: { feature_count: 0, drawable_geometry_count: 0 },
        features: [],
      });
    }
    if (url.includes("/api/operations/summary")) {
      return jsonResponse({
        year: 2023,
        case_count: 1,
        alert_count: 1,
        open_alert_count: 1,
        by_type: [{ alert_type: "pending_lab_result", count: 1 }],
        by_severity: [{ severity: "high", count: 1 }],
        by_status: [{ status: "open", count: 1 }],
        by_facility_team: [
          {
            facility_id: "UBS-1",
            team_id: "TEAM-1",
            team_name: "Equipe Centro",
            alert_count: 1,
            high: 1,
            moderate: 0,
            open: 1,
          },
        ],
      });
    }
    if (url.includes("/api/operations/alerts/alert-1"))
      return jsonResponse(
        url.includes("lang=en") ? englishOperationAlert : operationAlert,
      );
    if (url.includes("/api/operations/alerts/alert-2"))
      return jsonResponse(
        url.includes("lang=en")
          ? secondEnglishOperationAlert
          : secondOperationAlert,
      );
    if (url.includes("/api/operations/alerts"))
      return jsonResponse(
        url.includes("lang=en")
          ? [englishOperationAlert, secondEnglishOperationAlert]
          : [operationAlert, secondOperationAlert],
      );
    if (url.includes("/api/territories/2304400/report")) {
      return jsonResponse({
        territory_id: "2304400",
        territory_name: "Fortaleza",
        year: 2023,
        indicators: [],
        incidence_history: buildIncidenceHistory(url.includes("lang=en")),
        recommendations: [],
        scenarios: mapPayload.features[0].properties.top_scenarios,
      });
    }
    return jsonResponse({});
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.pushState({}, "", "/");
});

describe("App", () => {
  it("renders the territorial product shell without MVP labels", async () => {
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Análise territorial" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Acompanhamento da atenção")).toBeInTheDocument();
    expect((await screen.findAllByText("Fortaleza")).length).toBeGreaterThan(0);
    expect(
      await screen.findByText(/1\/12 meses do SIH\/SUS/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Ver ranking completo" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("MVP1")).not.toBeInTheDocument();
    expect(screen.queryByText("MVP2")).not.toBeInTheDocument();
  });

  it("opens the highest-priority municipality in the territorial dossier", async () => {
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    const dossierTitle = await screen.findByText("Dossiê territorial");
    const detailPanel = dossierTitle.closest("aside");
    expect(detailPanel).not.toBeNull();
    const detail = within(detailPanel as HTMLElement);

    expect(
      await detail.findByRole("heading", { name: "Fortaleza" }),
    ).toBeInTheDocument();
    expect(detail.getByText("Índice de prioridade")).toBeInTheDocument();
    expect(detail.getByText("8,0")).toBeInTheDocument();
    expect(detail.getByText("Testagem para HIV abaixo do comparativo")).toBeInTheDocument();
    expect(
      detail.getByText("regra comparativa provisória"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Fortaleza/ }),
    ).toHaveAttribute("aria-pressed", "true");
  });
  it("shows auditable annual incidence without inferring a trend", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    const heading = await screen.findByText("Incidência histórica");
    const section = heading.closest("section");
    expect(section).not.toBeNull();
    const history = within(section as HTMLElement);

    expect(history.getByText("4/6 anos disponíveis")).toBeInTheDocument();
    expect(
      history.getByRole("img", {
        name: /Incidência de TB: 2018-2023/,
      }),
    ).toBeInTheDocument();
    expect(history.getAllByText("suprimido").length).toBeGreaterThan(0);
    expect(history.getAllByText("ausente").length).toBeGreaterThan(0);
    expect(
      history.getByText(
        "A série atravessa versões da fonte com situações de fechamento diferentes.",
      ),
    ).toBeInTheDocument();
    expect(
      history.getByText(
        "Série observada e auditável; não é previsão e ainda não gera pontuação.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tendência crescente/i)).not.toBeInTheDocument();

    await user.click(history.getByText("Ver base anual e fontes"));

    expect(
      history.getByText("Casos: 1.593 · População: 2.643.247"),
    ).toBeVisible();
    expect(
      history.getAllByText(/SINAN-TB \/ DATASUS:/).length,
    ).toBeGreaterThan(0);
    expect(
      history.getAllByText(/População IBGE: final · Censo · 2022/).length,
    ).toBeGreaterThan(0);
  });

  it("localizes incidence-history boundaries and audit labels", async () => {
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=en");
    render(<App />);

    const heading = await screen.findByText("Historical incidence");
    const section = heading.closest("section");
    expect(section).not.toBeNull();
    const history = within(section as HTMLElement);

    expect(await history.findByText("4/6 available years")).toBeInTheDocument();
    expect(
      history.getByText(
        "Observed, auditable series; it is not a forecast and does not affect the score.",
      ),
    ).toBeInTheDocument();
    expect(
      history.getByText(
        "The population denominator changes between estimate and Census methods.",
      ),
    ).toBeInTheDocument();
    expect(history.getByText("View annual basis and sources")).toBeInTheDocument();
  });


  it("explains layer values, availability, and units in the map legend", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    const legendRegion = await screen.findByRole("region", {
      name: "Legenda do mapa",
    });
    const legend = within(legendRegion);

    expect(legend.getByText("Pontuação de prioridade")).toBeInTheDocument();
    expect(legend.getByText("7,2 - 8,0")).toBeInTheDocument();
    expect(legend.getAllByText("2 municípios no mapa")).toHaveLength(3);
    expect(legend.getByText("1 município no mapa")).toBeInTheDocument();
    expect(legend.getByText("0 municípios no mapa")).toBeInTheDocument();
    expect(legend.getByText("Dado suprimido")).toBeInTheDocument();
    expect(legend.getByText("Dado ausente")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Mapa territorial interativo"),
    ).toBeInTheDocument();

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Camada" }),
      "tb_incidence_per_100k",
    );

    expect(legend.getByText("Incidência de TB")).toBeInTheDocument();
    expect(legend.getByText("80,0/100 mil")).toBeInTheDocument();
    expect(legend.getByText("6 municípios no mapa")).toBeInTheDocument();
    expect(
      legend.getByText(
        "Faixas relativas aos valores disponíveis no escopo e ano selecionados.",
      ),
    ).toBeInTheDocument();
  });

  it("focuses the selected polygon only after an explicit ranking action", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    await screen.findByRole("button", { name: /Fortaleza/ });
    await waitFor(() => {
      expect(maplibreMockState.fitBounds).toHaveBeenCalledTimes(1);
    });
    expect(maplibreMockState.fitBounds).toHaveBeenLastCalledWith(
      [
        [0, 0],
        [6.75, 0.75],
      ],
      { padding: 36, duration: 0 },
    );

    maplibreMockState.fitBounds.mockClear();
    await user.click(screen.getByRole("button", { name: /Caucaia/ }));

    await waitFor(() => {
      expect(maplibreMockState.fitBounds).toHaveBeenCalledTimes(1);
    });
    expect(maplibreMockState.fitBounds).toHaveBeenCalledWith(
      [
        [1, 0],
        [1.75, 0.75],
      ],
      { padding: 56, maxZoom: 8, duration: 240 },
    );
  });

  it("opens and closes the localized mobile navigation menu", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    const menuButton = screen.getByRole("button", { name: "Abrir menu" });
    expect(menuButton).toHaveAttribute("aria-expanded", "false");
    expect(menuButton).toHaveAttribute(
      "aria-controls",
      "product-navigation-panel",
    );

    await user.click(menuButton);
    expect(screen.getByRole("button", { name: "Fechar menu" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );

    await user.click(screen.getByRole("button", { name: "Fechar menu" }));
    expect(screen.getByRole("button", { name: "Abrir menu" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("closes the mobile menu after navigation", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Abrir menu" }));
    await user.click(
      screen.getByRole("link", { name: "Acompanhamento da atenção" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Acompanhamento da atenção" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abrir menu" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("keeps ranking filters visible and shows six rows before expansion", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    const heading = await screen.findByRole("heading", {
      name: "Municípios prioritários",
    });
    const section = heading.closest("section");
    expect(section).not.toBeNull();
    const ranking = within(section as HTMLElement);
    const rankingButtons = () =>
      ranking
        .getAllByRole("button")
        .filter((button) => button.hasAttribute("aria-pressed"));

    expect(
      ranking.getByRole("combobox", { name: "Buscar município" }),
    ).toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Gravidade" }),
    ).toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Situação" }),
    ).toBeInTheDocument();
    expect(rankingButtons()).toHaveLength(6);
    expect(
      ranking.queryByRole("button", { name: /Itapipoca/ }),
    ).not.toBeInTheDocument();

    const fortaleza = ranking.getByRole("button", { name: /Fortaleza/ });
    expect(fortaleza).toHaveAttribute("aria-pressed", "true");
    expect(fortaleza).toHaveAccessibleName(
      "1 Fortaleza 2 sinais maior atenção Índice de prioridade: 8,0",
    );

    await user.click(
      ranking.getByRole("button", { name: "Ver ranking completo" }),
    );

    expect(
      ranking.getByRole("button", { name: "Mostrar 6 primeiros" }),
    ).toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Buscar município" }),
    ).toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Gravidade" }),
    ).toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Situação" }),
    ).toBeInTheDocument();
    expect(rankingButtons()).toHaveLength(7);
    expect(
      ranking.getByRole("button", { name: /Itapipoca/ }),
    ).toBeInTheDocument();

    const caucaia = ranking.getByRole("button", { name: /Caucaia/ });
    caucaia.focus();
    await user.keyboard("{Enter}");
    expect(caucaia).toHaveAttribute("aria-pressed", "true");
    expect(fortaleza).toHaveAttribute("aria-pressed", "false");

    await user.selectOptions(
      ranking.getByRole("combobox", { name: "Gravidade" }),
      "moderate",
    );
    expect(rankingButtons()).toHaveLength(2);
    expect(
      ranking.queryByRole("button", { name: "Mostrar 6 primeiros" }),
    ).not.toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Buscar município" }),
    ).toBeInTheDocument();
    expect(
      ranking.getByRole("combobox", { name: "Situação" }),
    ).toBeInTheDocument();
  });

  it("shows load-year progress after starting a missing year load", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2024&lang=pt");
    render(<App />);

    expect(
      await screen.findByText("Dados do ano selecionado não estão processados"),
    ).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Carregar ano selecionado" }),
    );

    expect(await screen.findByText("Progresso da carga")).toBeInTheDocument();
    expect(
      await screen.findByText("1/4 baixando: SINAN-TB Brazil 2024 preliminary"),
    ).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("sih_all_months=true"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("renders the operational queue through the product route", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    await user.click(
      screen.getByRole("link", { name: "Acompanhamento da atenção" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Acompanhamento da atenção" }),
    ).toBeInTheDocument();
    expect(
      (await screen.findAllByText("Resultado laboratorial pendente")).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("demonstração sintética/pseudonimizada"),
    ).toBeInTheDocument();
    const teamPanel = screen
      .getByRole("heading", { name: "Unidades e equipes" })
      .closest("section");
    expect(teamPanel).not.toBeNull();
    expect(teamPanel).toHaveTextContent(/Alta gravidade\s*1/);
    expect(teamPanel).toHaveTextContent(/Alertas abertos\s*1/);
    expect(screen.queryByText("MVP1")).not.toBeInTheDocument();
    expect(screen.queryByText("MVP2")).not.toBeInTheDocument();
  });

  it("counts and resets active operational filters", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/acompanhamento?year=2023&lang=pt");
    render(<App />);

    const filterToggle = await screen.findByRole("button", {
      name: "Ocultar filtros",
    });
    expect(filterToggle).toHaveAttribute("aria-expanded", "true");

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Gravidade" }),
      "high",
    );

    await waitFor(() => {
      expect(new URLSearchParams(window.location.search).get("severity")).toBe(
        "high",
      );
    });
    const activeToggle = screen.getByRole("button", {
      name: "Ocultar filtros. 1 filtro ativo",
    });
    expect(within(activeToggle).getByText("1")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Limpar filtros" }),
    );

    await waitFor(() => {
      expect(
        new URLSearchParams(window.location.search).has("severity"),
      ).toBe(false);
    });
    expect(
      screen.getByRole("combobox", { name: "Gravidade" }),
    ).toHaveValue("");
    expect(
      screen.queryByRole("button", { name: "Limpar filtros" }),
    ).not.toBeInTheDocument();
  });

  it("expands alert detail in place and marks overdue deadlines explicitly", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/acompanhamento?year=2023&lang=pt");
    render(<App />);

    const firstRow = await screen.findByRole("row", {
      name: /Resultado laboratorial pendente/,
    });
    const secondRow = screen.getByRole("row", {
      name: /Atraso na retirada de medicamento/,
    });

    expect(within(firstRow).getByText("Prazo vencido")).toBeInTheDocument();
    expect(secondRow).toHaveAttribute("aria-expanded", "false");

    await user.click(secondRow);
    expect(secondRow).toHaveAttribute("aria-expanded", "true");

    const detailRow = await screen.findByRole("row", { name: /CASE-2/ });
    const detail = within(detailRow);
    expect(
      detail.getByRole("heading", { name: "Onde revisar" }),
    ).toBeInTheDocument();
    expect(
      detail.getByRole("heading", { name: "Por que revisar" }),
    ).toBeInTheDocument();
    expect(
      detail.getByRole("heading", { name: "Janela de revisão" }),
    ).toBeInTheDocument();
    expect(
      detail.getByText("Retirada de medicamento atrasada."),
    ).toBeInTheDocument();

    await user.click(secondRow);
    await waitFor(() => {
      expect(
        screen.queryByRole("row", { name: /CASE-2/ }),
      ).not.toBeInTheDocument();
    });
  });

  it("selects operational alert rows with Enter and Space", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/acompanhamento?year=2023&lang=pt");
    render(<App />);

    const firstRow = await screen.findByRole("row", {
      name: /Resultado laboratorial pendente/,
    });
    const secondRow = screen.getByRole("row", {
      name: /Atraso na retirada de medicamento/,
    });
    await waitFor(() =>
      expect(firstRow).toHaveAttribute("aria-selected", "true"),
    );
    expect(secondRow).toHaveAttribute("tabindex", "0");

    secondRow.focus();
    await user.keyboard(" ");
    expect(secondRow).toHaveAttribute("aria-selected", "true");

    firstRow.focus();
    await user.keyboard("{Enter}");
    expect(firstRow).toHaveAttribute("aria-selected", "true");
  });

  it("provides localized labels for every mobile alert-card field", async () => {
    window.history.pushState({}, "", "/acompanhamento?year=2023&lang=pt");
    render(<App />);

    const row = await screen.findByRole("row", {
      name: /Resultado laboratorial pendente/,
    });
    expect(
      within(row)
        .getAllByRole("cell")
        .map((cell) => cell.getAttribute("data-label")),
    ).toEqual([
      "Tipo",
      "Gravidade",
      "Situação",
      "Unidade",
      "Equipe",
      "Prazo",
    ]);
  });

  it("renders localized alert detail fields and requests the selected language", async () => {
    window.history.pushState({}, "", "/acompanhamento?year=2023&lang=en");
    render(<App />);

    const heading = await screen.findByRole("heading", {
      name: "Alert detail",
    });
    const detailPanel = heading.closest("aside");
    expect(detailPanel).not.toBeNull();
    const detail = within(detailPanel as HTMLElement);

    expect(
      await detail.findByText("Laboratory result pending for case CASE-1."),
    ).toBeInTheDocument();
    expect(detail.getByText("Pending laboratory result")).toBeInTheDocument();
    expect(detail.getAllByText("open").length).toBeGreaterThan(0);
    expect(detail.getByText("6/29/2026")).toBeInTheDocument();
    expect(detail.getByText("7/2/2026")).toBeInTheDocument();
    expect(detail.queryByText("pending_lab_result")).not.toBeInTheDocument();
    expect(detail.queryByText("2026-06-29")).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/operations/alerts/alert-1?lang=en"),
      expect.any(Object),
    );
  });

  it("redirects the legacy territorial route with its query and hash", async () => {
    window.history.pushState(
      {},
      "",
      "/conceito/territorios?uf=BR&year=2023&lang=pt#dados",
    );
    render(<App />);

    await waitFor(() => expect(window.location.pathname).toBe("/territorios"));
    expect(window.location.search).toBe("?uf=BR&year=2023&lang=pt");
    expect(window.location.hash).toBe("#dados");
    expect(
      await screen.findByRole("heading", { name: "Análise territorial" }),
    ).toBeInTheDocument();
    expect(screen.getByAltText("Sistema Único de Saúde")).toBeInTheDocument();
  });

  it("redirects the legacy operations route with its query and hash", async () => {
    window.history.pushState(
      {},
      "",
      "/conceito/acompanhamento?year=2023&lang=pt#fila",
    );
    render(<App />);

    await waitFor(() =>
      expect(window.location.pathname).toBe("/acompanhamento"),
    );
    expect(window.location.search).toBe("?year=2023&lang=pt");
    expect(window.location.hash).toBe("#fila");
    expect(
      await screen.findByRole("heading", { name: "Acompanhamento da atenção" }),
    ).toBeInTheDocument();
  });
});

function jsonResponse(payload: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), { status: 200 }),
  );
}
