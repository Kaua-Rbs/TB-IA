import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  DownloadCloud,
  Layers,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { MapLegend } from "../components/MapLegend";
import { MetricCard } from "../components/MetricCard";
import { PriorityRankingList } from "../components/PriorityRankingList";
import { StatusBadge } from "../components/StatusBadge";
import {
  TerritorialMap,
  type MapFocusRequest,
} from "../components/TerritorialMap";
import {
  fetchSubterritories,
  fetchTerritorialContext,
  fetchTerritorialMap,
  fetchTerritorialYearLoadJob,
  fetchTerritoryReport,
  startTerritorialYearLoad,
  type FeatureCollection,
  type LoadYearJob,
  type RankingRow,
} from "../lib/api";
import {
  formatIndicatorValue,
  formatMonthCoverage,
  formatNumber,
  labelStatus,
} from "../lib/format";
import {
  buildMapLayerPresentation,
  layerLabel,
  layerOptions,
} from "../lib/geojson";
import { copy, normalizeLanguage } from "../lib/i18n";

const ufOptions = [
  "BR",
  "AC",
  "AL",
  "AP",
  "AM",
  "BA",
  "CE",
  "DF",
  "ES",
  "GO",
  "MA",
  "MT",
  "MS",
  "MG",
  "PA",
  "PB",
  "PR",
  "PE",
  "PI",
  "RJ",
  "RN",
  "RS",
  "RO",
  "RR",
  "SC",
  "SP",
  "SE",
  "TO",
];

export function TerritorialPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const lang = normalizeLanguage(searchParams.get("lang"));
  const labels = copy[lang];
  const uf = (searchParams.get("uf") || "BR").toUpperCase();
  const year = Number(searchParams.get("year") || "2023");
  const comparisonScope =
    uf === "BR" ? "national" : searchParams.get("comparison_scope") || "uf";
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const focusSequenceRef = useRef(0);
  const [mapFocusRequest, setMapFocusRequest] =
    useState<MapFocusRequest | null>(null);
  const [mapMode, setMapMode] = useState<"priority" | "reference">("priority");
  const [layerId, setLayerId] = useState("priority_score");
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [loadJobId, setLoadJobId] = useState<string | null>(null);
  const [handledLoadJobId, setHandledLoadJobId] = useState<string | null>(null);

  const queryParams = { uf, year, comparisonScope, lang };
  const contextQuery = useQuery({
    queryKey: ["territorial-context", queryParams],
    queryFn: () => fetchTerritorialContext(queryParams),
  });
  const mapQuery = useQuery({
    queryKey: ["territorial-map", queryParams],
    queryFn: () => fetchTerritorialMap(queryParams),
  });
  const reportQuery = useQuery({
    queryKey: ["territory-report", selectedId, year, comparisonScope, lang],
    queryFn: () =>
      fetchTerritoryReport(selectedId ?? "", year, comparisonScope, lang),
    enabled: Boolean(selectedId),
  });
  const subterritoryQuery = useQuery({
    queryKey: ["subterritories", selectedId, lang],
    queryFn: () => fetchSubterritories(selectedId ?? "", lang),
    enabled: mapMode === "reference" && Boolean(selectedId),
  });
  const loadYearMutation = useMutation<LoadYearJob>({
    mutationFn: () =>
      startTerritorialYearLoad({ ...queryParams, sihAllMonths: true }),
    onSuccess: (job) => {
      setLoadJobId(job.job_id);
    },
  });
  const loadJobQuery = useQuery<LoadYearJob>({
    queryKey: ["territorial-load-job", loadJobId],
    queryFn: () => fetchTerritorialYearLoadJob(loadJobId ?? ""),
    enabled: Boolean(loadJobId),
    refetchInterval: (query) => {
      const job = query.state.data as LoadYearJob | undefined;
      return job?.status === "queued" || job?.status === "running"
        ? 2000
        : false;
    },
  });

  const selectedFeature = useMemo(
    () =>
      mapQuery.data?.features.find(
        (feature) => feature.properties.territory_id === selectedId,
      ),
    [mapQuery.data, selectedId],
  );
  const layers = layerOptions(mapQuery.data);
  const mapPresentation = useMemo(
    () => buildMapLayerPresentation(mapQuery.data, layerId),
    [layerId, mapQuery.data],
  );
  const rankingRows = useMemo(
    () => buildRankingRows(contextQuery.data?.ranking ?? [], mapQuery.data),
    [contextQuery.data, mapQuery.data],
  );
  const filteredRanking = useMemo(
    () =>
      rankingRows.filter((row) => {
        const feature = mapQuery.data?.features.find(
          (candidate) => candidate.properties.territory_id === row.territory_id,
        );
        const nameMatches = row.territory_name
          .toLowerCase()
          .includes(searchTerm.toLowerCase());
        const severityMatches =
          !severityFilter || row.top_severity === severityFilter;
        const statusMatches =
          !statusFilter || feature?.properties.data_status === statusFilter;
        return nameMatches && severityMatches && statusMatches;
      }),
    [mapQuery.data, rankingRows, searchTerm, severityFilter, statusFilter],
  );

  useEffect(() => {
    setLoadJobId(null);
    setHandledLoadJobId(null);
  }, [uf, year]);

  useEffect(() => {
    const job = loadJobQuery.data;
    if (job?.status !== "complete" || handledLoadJobId === job.job_id) return;
    setHandledLoadJobId(job.job_id);
    void queryClient.invalidateQueries({ queryKey: ["territorial-context"] });
    void queryClient.invalidateQueries({ queryKey: ["territorial-map"] });
  }, [handledLoadJobId, loadJobQuery.data, queryClient]);

  useEffect(() => {
    if (!selectedId) return;
    const stillExists = mapQuery.data?.features.some(
      (feature) => feature.properties.territory_id === selectedId,
    );
    if (mapQuery.data && !stillExists) {
      setSelectedId(null);
    }
  }, [mapQuery.data, selectedId]);

  useEffect(() => {
    if (!selectedId && filteredRanking.length) {
      setSelectedId(filteredRanking[0].territory_id);
    }
  }, [filteredRanking, selectedId]);

  function updateScope(next: Record<string, string | number>) {
    const params = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(next)) {
      params.set(key, String(value));
    }
    const nextUf = String(next.uf ?? uf).toUpperCase();
    if (nextUf === "BR") {
      params.set("comparison_scope", "national");
    }
    params.set("lang", lang);
    setSearchParams(params);
    setMapFocusRequest(null);
    setSelectedId(null);
  }

  function selectFromSearch(value: string) {
    setSearchTerm(value);
    const match = mapQuery.data?.features.find((feature) =>
      feature.properties.name.toLowerCase().startsWith(value.toLowerCase()),
    );
    if (match) {
      setSelectedId(match.properties.territory_id);
    }
  }

  function selectFromRanking(territoryId: string) {
    setSelectedId(territoryId);
    focusSequenceRef.current += 1;
    setMapFocusRequest({
      territoryId,
      requestId: focusSequenceRef.current,
    });
  }

  const isLoading = contextQuery.isLoading || mapQuery.isLoading;
  const hasError = contextQuery.isError || mapQuery.isError;
  const loadJob = loadJobQuery.data ?? loadYearMutation.data;
  const isLoadRunning = Boolean(
    loadYearMutation.isPending ||
      loadJob?.status === "queued" ||
      loadJob?.status === "running",
  );
  const shouldOfferYearLoad = Boolean(
    contextQuery.data &&
      !contextQuery.isFetching &&
      contextQuery.data.territory_count > 0 &&
      contextQuery.data.indicator_count === 0,
  );
  const shouldShowLoadPanel =
    shouldOfferYearLoad || Boolean(loadJob) || loadYearMutation.isPending;

  return (
    <div className="page-stack territory-page">
      <header className="page-hero compact-hero">
        <div>
          <span className="situation-kicker">{labels.productContext}</span>
          <h1>{labels.territorial.title}</h1>
          <p>{labels.territorial.subtitle}</p>
        </div>
        <form
          className="command-bar"
          aria-label={labels.territorial.commandScope}
        >
          <label>
            {labels.common.uf}
            <select
              value={uf}
              onChange={(event) => updateScope({ uf: event.target.value })}
            >
              {ufOptions.map((option) => (
                <option key={option} value={option}>
                  {option === "BR" ? "Brasil" : option}
                </option>
              ))}
            </select>
          </label>
          <label>
            {labels.common.year}
            <input
              type="number"
              min="2000"
              max="2100"
              value={year}
              onChange={(event) =>
                updateScope({ year: Number(event.target.value) })
              }
            />
          </label>
          <label>
            {labels.common.comparison}
            <select
              value={comparisonScope}
              disabled={uf === "BR"}
              onChange={(event) =>
                updateScope({ comparison_scope: event.target.value })
              }
            >
              <option value="national">{labels.common.national}</option>
              <option value="uf">{labels.common.ufRanking}</option>
            </select>
          </label>
        </form>
      </header>

      <section className="caveat-band">
        <AlertTriangle size={18} aria-hidden="true" />
        <span>{contextQuery.data?.caveat ?? labels.territorial.mapHelp}</span>
      </section>

      {shouldShowLoadPanel ? (
        <section className="data-load-panel" aria-live="polite">
          <div>
            <h2>{labels.territorial.loadYearTitle}</h2>
            <p>{labels.territorial.loadYearText}</p>
            <small>{labels.territorial.loadYearHint}</small>
          </div>
          <button
            type="button"
            onClick={() => loadYearMutation.mutate()}
            disabled={isLoadRunning}
          >
            <DownloadCloud size={17} aria-hidden="true" />
            <span>
              {isLoadRunning
                ? labels.territorial.loadYearRunning
                : labels.territorial.loadYearButton}
            </span>
          </button>
          <LoadYearProgress job={loadJob} />
          {loadJob?.status === "complete" ? (
            <p className="load-feedback">
              {loadJob.message || labels.territorial.loadYearDone}
            </p>
          ) : null}
          {loadYearMutation.isError || loadJob?.status === "failed" ? (
            <p className="load-feedback error">
              {loadJob?.message || labels.territorial.loadYearFailed}
              {loadJob?.error ? (
                <span>{`${labels.territorial.loadYearTechnicalError}: ${loadJob.error}`}</span>
              ) : null}
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="metric-strip" aria-label="Resumo">
        <MetricCard
          label={labels.territorial.metrics.municipalities}
          value={formatNumber(contextQuery.data?.territory_count, lang)}
        />
        <MetricCard
          label={labels.territorial.metrics.indicators}
          value={formatNumber(contextQuery.data?.indicator_count, lang)}
        />
        <MetricCard
          label={labels.territorial.metrics.signals}
          value={formatNumber(contextQuery.data?.scenario_count, lang)}
        />
        <MetricCard
          label={labels.territorial.metrics.readiness}
          value={readinessSummary(contextQuery.data?.readiness, lang)}
          tone={readinessTone(contextQuery.data?.readiness)}
        />
      </section>

      <section className="territorial-workbench">
        <div className="map-card">
          <div className="panel-heading split-heading">
            <div>
              <h2>{labels.territorial.mapTitle}</h2>
              <p>{labels.territorial.mapHelp}</p>
            </div>
            <div className="map-tools">
              <label className="segmented-label">
                {labels.territorial.mapMode}
                <span className="segmented-control-app">
                  <button
                    type="button"
                    className={mapMode === "priority" ? "active" : ""}
                    onClick={() => setMapMode("priority")}
                  >
                    {labels.territorial.priorityMode}
                  </button>
                  <button
                    type="button"
                    className={mapMode === "reference" ? "active" : ""}
                    onClick={() => setMapMode("reference")}
                  >
                    {labels.territorial.referenceMode}
                  </button>
                </span>
              </label>
              <label>
                {labels.territorial.layer}
                <select
                  value={layerId}
                  onChange={(event) => setLayerId(event.target.value)}
                >
                  {layers.map((layer) => (
                    <option key={layer.id} value={layer.id}>
                      {layerLabel(layer, layer.id)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>
          <div className="map-frame-product">
            {isLoading ? (
              <div className="loading-overlay">{labels.common.loading}</div>
            ) : null}
            {hasError ? (
              <div className="loading-overlay error">
                {labels.common.unavailable}
              </div>
            ) : null}
            <TerritorialMap
              payload={mapPresentation.payload}
              referencePayload={subterritoryQuery.data}
              selectedId={selectedId}
              referenceMode={mapMode === "reference"}
              focusRequest={mapFocusRequest}
              ariaLabel={labels.territorial.mapAriaLabel}
              onSelect={setSelectedId}
            />
            <MapLegend
              presentation={mapPresentation}
              lang={lang}
              selectedId={selectedId}
              referenceMode={mapMode === "reference"}
              referenceCount={
                subterritoryQuery.data?.metadata.drawable_geometry_count ?? 0
              }
            />
          </div>
          {mapMode === "reference" ? (
            <div className="inline-caveat">
              <Layers size={16} aria-hidden="true" />
              <span>
                {subterritoryQuery.data?.metadata.caveat ??
                  labels.territorial.referenceCaveat}
              </span>
            </div>
          ) : null}
        </div>

        <aside className="detail-panel territorial-dossier">
          <span className="dossier-kicker">
            {labels.territorial.dossierTitle}
          </span>
          <h2>{labels.territorial.selectedTitle}</h2>
          {!selectedId ? (
            <p className="muted-copy">{labels.territorial.selectedEmpty}</p>
          ) : null}
          {selectedId && selectedFeature ? (
            <div className="detail-stack">
              <div>
                <span className="eyebrow">{selectedFeature.properties.uf}</span>
                <h3>{selectedFeature.properties.name}</h3>
                <div className="badge-row">
                  <StatusBadge
                    value={selectedFeature.properties.top_severity}
                    kind="severity"
                    lang={lang}
                  />
                  <StatusBadge
                    value={selectedFeature.properties.data_status}
                    lang={lang}
                  />
                </div>
              </div>
              <div className="score-row">
                <span>{labels.territorial.priorityScore}</span>
                <strong>
                  {formatNumber(
                    selectedFeature.properties.priority_score,
                    lang,
                    1,
                  )}
                </strong>
              </div>
              <DetailReport
                report={reportQuery.data}
                selectedFeature={selectedFeature}
                lang={lang}
              />
            </div>
          ) : null}
        </aside>
      </section>

      <PriorityRankingList
        rows={filteredRanking}
        mapPayload={mapQuery.data}
        selectedId={selectedId}
        searchTerm={searchTerm}
        severityFilter={severityFilter}
        statusFilter={statusFilter}
        lang={lang}
        onSearchChange={selectFromSearch}
        onSeverityFilterChange={setSeverityFilter}
        onStatusFilterChange={setStatusFilter}
        onSelect={selectFromRanking}
      />

      <section id="dados" className="governance-grid">
        <ReadinessPanel
          title={labels.territorial.dataReadiness}
          items={contextQuery.data?.readiness}
          lang={lang}
        />
        <ReadinessPanel
          title={labels.territorial.healthTerritories}
          items={contextQuery.data?.health_territory_readiness}
          lang={lang}
        />
        <section className="source-panel">
          <div className="panel-heading">
            <h2>{labels.territorial.sourceFreshness}</h2>
          </div>
          <div className="source-list">
            {contextQuery.data?.sources.map((source) => (
              <div key={source.source_id} className="source-row">
                <div>
                  <strong>{source.name}</strong>
                  <small>{source.message}</small>
                  {source.month_coverage ? (
                    <small>
                      {formatMonthCoverage(source.month_coverage, lang)}
                    </small>
                  ) : null}
                </div>
                <StatusBadge value={source.status} lang={lang} />
              </div>
            ))}
            {!contextQuery.data?.sources.length ? (
              <p className="empty-state">{labels.common.empty}</p>
            ) : null}

          </div>
        </section>
      </section>
    </div>
  );
}

function LoadYearProgress({ job }: { job: LoadYearJob | undefined }) {
  const [searchParams] = useSearchParams();
  const lang = normalizeLanguage(searchParams.get("lang"));
  const labels = copy[lang];
  if (!job) return null;

  const progress = Math.max(
    0,
    Math.min(100, Math.round((job.step_index / job.step_count) * 100)),
  );

  return (
    <div className="load-progress">
      <div className="load-progress-meta">
        <strong>{labels.territorial.loadYearProgress}</strong>
        <span>{`${labels.territorial.loadYearStep} ${job.step_index}/${job.step_count}`}</span>
      </div>
      <div className="load-progress-track" aria-hidden="true">
        <span style={{ width: `${progress}%` }} />
      </div>
      <p>{job.message}</p>
      {job.download ? (
        <small>
          {`${job.download.downloaded_file_count} baixados, ${job.download.existing_file_count} já disponíveis, ${job.download.failed_file_count} falhas`}
        </small>
      ) : null}
    </div>
  );
}

function DetailReport({
  report,
  selectedFeature,
  lang,
}: {
  report: ReturnType<typeof fetchTerritoryReport> extends Promise<infer T>
    ? T | undefined
    : never;
  selectedFeature: NonNullable<FeatureCollection["features"][number]>;
  lang: ReturnType<typeof normalizeLanguage>;
}) {
  const labels = copy[lang];
  const indicators =
    report?.indicators ??
    Object.entries(selectedFeature.properties.indicators).map(
      ([indicatorId, indicator]) => ({
        indicator_id: indicatorId,
        indicator_name: indicator.name ?? indicatorId,
        ...indicator,
      }),
    );
  const scenarios =
    report?.scenarios ?? selectedFeature.properties.top_scenarios;

  return (
    <>
      <section className="detail-section">
        <h4>{labels.territorial.whyFlagged}</h4>
        {scenarios.length ? (
          <ul className="plain-list">
            {scenarios.slice(0, 3).map((scenario) => (
              <li key={`${scenario.rule_id}-${scenario.indicator_id}`}>
                <CheckCircle2 size={15} aria-hidden="true" />
                <span>{scenario.explanation}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted-copy">{labels.territorial.noSignals}</p>
        )}
      </section>
      <section className="detail-section">
        <h4>{labels.territorial.recommendedResponse}</h4>
        {report?.recommendations?.length ? (
          <ul className="plain-list">
            {report.recommendations.slice(0, 3).map((recommendation, index) => (
              <li
                key={`${recommendation.recommendation_id ?? recommendation.title ?? index}`}
              >
                <CheckCircle2 size={15} aria-hidden="true" />
                <span>
                  {recommendation.action ??
                    recommendation.title ??
                    recommendation.explanation}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted-copy">-</p>
        )}
      </section>
      <section className="detail-section">
        <h4>{labels.territorial.indicators}</h4>
        <div className="indicator-list">
          {indicators.slice(0, 7).map((indicator) => (
            <div key={indicator.indicator_id}>
              <span>{indicator.indicator_name}</span>
              <strong>
                {formatIndicatorValue(indicator.value, indicator.unit, lang)}
              </strong>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

function ReadinessPanel({
  title,
  items,
  lang,
}: {
  title: string;
  items:
    | Record<string, { label: string; status: string; detail: string }>
    | undefined;
  lang: ReturnType<typeof normalizeLanguage>;
}) {
  return (
    <section className="readiness-panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div className="readiness-list">
        {Object.entries(items ?? {}).map(([key, item]) => (
          <div key={key} className={`readiness-item readiness-${item.status}`}>
            <div>
              <strong>{item.label}</strong>
              <small>{item.detail}</small>
            </div>
            <StatusBadge value={item.status} lang={lang} />
          </div>
        ))}
      </div>
    </section>
  );
}

function readinessTone(
  items: Record<string, { status: string }> | undefined,
): "default" | "good" | "warn" | "danger" {
  if (!items) return "default";
  const statuses = Object.values(items).map((item) => item.status);
  if (statuses.length && statuses.every((status) => status === "ready")) return "good";
  if (statuses.some((status) => status === "warning" || status === "partial")) return "warn";
  return "default";
}

function readinessSummary(
  items: Record<string, { status: string }> | undefined,
  lang: ReturnType<typeof normalizeLanguage>,
) {
  if (!items) return "-";
  const statuses = Object.values(items).map((item) => item.status);
  if (statuses.every((status) => status === "ready"))
    return labelStatus("ready", lang);
  if (statuses.some((status) => status === "warning"))
    return labelStatus("warning", lang);
  if (statuses.some((status) => status === "partial"))
    return labelStatus("partial", lang);
  return labelStatus("missing", lang);
}

function buildRankingRows(
  rows: RankingRow[],
  payload: FeatureCollection | undefined,
): RankingRow[] {
  if (rows.length) return rows;
  return [...(payload?.features ?? [])]
    .filter((feature) => feature.properties.scenario_count > 0)
    .sort(
      (left, right) =>
        right.properties.priority_score - left.properties.priority_score,
    )
    .map((feature) => ({
      territory_id: feature.properties.territory_id,
      territory_name: feature.properties.name,
      score: feature.properties.priority_score,
      scenario_count: feature.properties.scenario_count,
      top_severity: feature.properties.top_severity,
      top_explanations: feature.properties.top_explanations,
      top_scenarios: feature.properties.top_scenarios,
    }));
}
