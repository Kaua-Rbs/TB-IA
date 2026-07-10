import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const mapPayload = {
  type: "FeatureCollection",
  metadata: {
    geographic_scope: "BR",
    comparison_scope: "national",
    year: 2023,
    feature_count: 1,
    drawable_geometry_count: 1,
    layers: {
      priority_score: {
        label: "Pontuação de prioridade",
        kind: "property",
        unit: "score",
        direction: "high_bad",
      },
    },
  },
  features: [
    {
      type: "Feature",
      properties: {
        territory_id: "2304400",
        name: "Fortaleza",
        uf: "CE",
        priority_score: 8,
        scenario_count: 2,
        top_severity: "high",
        top_explanations: ["Incidência elevada"],
        top_scenarios: [
          {
            rule_id: "high_incidence",
            indicator_id: "tb_incidence_per_100k",
            severity: "high",
            score: 4,
            explanation: "Incidência elevada",
          },
        ],
        data_status: "complete",
        indicators: {
          tb_incidence_per_100k: {
            name: "Incidência de TB",
            value: 80,
            is_suppressed: false,
            unit: "per_100k",
            direction: "high_bad",
          },
        },
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 0],
          ],
        ],
      },
    },
  ],
};

const territorialContext = {
  uf: "BR",
  geographic_scope: "BR",
  comparison_scope: "national",
  year: 2023,
  territory_count: 1,
  indicator_count: 1,
  scenario_count: 2,
  caveat: "Painel público agregado.",
  ranking: [
    {
      territory_id: "2304400",
      territory_name: "Fortaleza",
      score: 8,
      scenario_count: 2,
      top_severity: "high",
      top_explanations: ["Incidência elevada"],
      top_scenarios: mapPayload.features[0].properties.top_scenarios,
    },
  ],
  readiness: {
    geometry: {
      label: "Geometria",
      status: "ready",
      detail: "1/1 municípios com geometria",
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
    },
  ],
};

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

beforeEach(() => {
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
        sih_all_months: false,
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
        sih_all_months: false,
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
            high_count: 1,
            moderate_count: 0,
            open_count: 1,
          },
        ],
      });
    }
    if (url.includes("/api/operations/alerts/alert-1"))
      return jsonResponse(operationAlert);
    if (url.includes("/api/operations/alerts"))
      return jsonResponse([operationAlert]);
    if (url.includes("/api/territories/2304400/report")) {
      return jsonResponse({
        territory_id: "2304400",
        territory_name: "Fortaleza",
        year: 2023,
        indicators: [],
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
      screen.getByRole("button", { name: "Expandir ranking" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("MVP1")).not.toBeInTheDocument();
    expect(screen.queryByText("MVP2")).not.toBeInTheDocument();
  });

  it("expands and hides the priority ranking", async () => {
    const user = userEvent.setup();
    window.history.pushState({}, "", "/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    await screen.findByRole("heading", { name: "Análise territorial" });
    await user.click(screen.getByRole("button", { name: "Expandir ranking" }));

    expect(
      screen.getByRole("button", { name: "Ocultar ranking" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Score" }),
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
    expect(screen.queryByText("MVP1")).not.toBeInTheDocument();
    expect(screen.queryByText("MVP2")).not.toBeInTheDocument();
  });

  it("renders the territorial concept route as a product console", async () => {
    window.history.pushState({}, "", "/conceito/territorios?uf=BR&year=2023&lang=pt");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Análise territorial" }),
    ).toBeInTheDocument();
    expect(
      screen.getByAltText("TB-IA - Painel gestor de saúde"),
    ).toBeInTheDocument();
    expect(screen.getByAltText("Sistema Único de Saúde")).toBeInTheDocument();
    expect(screen.getByText("Dados públicos")).toBeInTheDocument();
    expect(screen.getByText("Ajuda")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Mapa territorial" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Municípios prioritários" }),
    ).toBeInTheDocument();
    expect((await screen.findAllByText("Fortaleza")).length).toBeGreaterThan(0);
    expect(screen.queryByText("MVP1")).not.toBeInTheDocument();
    expect(screen.queryByText("MVP2")).not.toBeInTheDocument();
  });

  it("renders the operations concept route as a review queue", async () => {
    window.history.pushState({}, "", "/conceito/acompanhamento?year=2023&lang=pt");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Acompanhamento da atenção" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Fila operacional" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Detalhe do alerta" }),
    ).toBeInTheDocument();
    expect(
      (await screen.findAllByText("Resultado laboratorial pendente")).length,
    ).toBeGreaterThan(0);
    expect((await screen.findAllByText("Equipe Centro")).length).toBeGreaterThan(0);
    expect(screen.queryByText("MVP1")).not.toBeInTheDocument();
    expect(screen.queryByText("MVP2")).not.toBeInTheDocument();
  });
});

function jsonResponse(payload: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), { status: 200 }),
  );
}
