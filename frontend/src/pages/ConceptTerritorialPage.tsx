import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { ConceptIcon } from '../components/ConceptIcon';
import { StatusBadge } from '../components/StatusBadge';
import { TerritorialMap } from '../components/TerritorialMap';
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
  type ReadinessItem,
  type SourceRow,
  type TerritoryReport,
} from '../lib/api';
import {
  formatIndicatorValue,
  formatNumber,
  labelSeverity,
  labelStatus,
} from '../lib/format';
import { layerLabel, layerOptions } from '../lib/geojson';
import { copy, normalizeLanguage, type Language } from '../lib/i18n';

const ufOptions = [
  'BR',
  'AC',
  'AL',
  'AP',
  'AM',
  'BA',
  'CE',
  'DF',
  'ES',
  'GO',
  'MA',
  'MT',
  'MS',
  'MG',
  'PA',
  'PB',
  'PR',
  'PE',
  'PI',
  'RJ',
  'RN',
  'RS',
  'RO',
  'RR',
  'SC',
  'SP',
  'SE',
  'TO',
];

export function ConceptTerritorialPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const lang = normalizeLanguage(searchParams.get('lang'));
  const labels = copy[lang];
  const uf = (searchParams.get('uf') || 'BR').toUpperCase();
  const year = Number(searchParams.get('year') || '2023');
  const comparisonScope =
    uf === 'BR' ? 'national' : searchParams.get('comparison_scope') || 'uf';
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mapMode, setMapMode] = useState<'priority' | 'reference'>('priority');
  const [layerId, setLayerId] = useState('priority_score');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isRankingExpanded, setIsRankingExpanded] = useState(false);
  const [loadJobId, setLoadJobId] = useState<string | null>(null);
  const [handledLoadJobId, setHandledLoadJobId] = useState<string | null>(null);

  const queryParams = { uf, year, comparisonScope, lang };
  const contextQuery = useQuery({
    queryKey: ['territorial-context', queryParams],
    queryFn: () => fetchTerritorialContext(queryParams),
  });
  const mapQuery = useQuery({
    queryKey: ['territorial-map', queryParams],
    queryFn: () => fetchTerritorialMap(queryParams),
  });
  const reportQuery = useQuery({
    queryKey: ['territory-report', selectedId, year, comparisonScope, lang],
    queryFn: () =>
      fetchTerritoryReport(selectedId ?? '', year, comparisonScope, lang),
    enabled: Boolean(selectedId),
  });
  const subterritoryQuery = useQuery({
    queryKey: ['subterritories', selectedId, lang],
    queryFn: () => fetchSubterritories(selectedId ?? '', lang),
    enabled: mapMode === 'reference' && Boolean(selectedId),
  });
  const loadYearMutation = useMutation<LoadYearJob>({
    mutationFn: () =>
      startTerritorialYearLoad({ ...queryParams, sihAllMonths: false }),
    onSuccess: (job) => setLoadJobId(job.job_id),
  });
  const loadJobQuery = useQuery<LoadYearJob>({
    queryKey: ['territorial-load-job', loadJobId],
    queryFn: () => fetchTerritorialYearLoadJob(loadJobId ?? ''),
    enabled: Boolean(loadJobId),
    refetchInterval: (query) => {
      const job = query.state.data as LoadYearJob | undefined;
      return job?.status === 'queued' || job?.status === 'running'
        ? 2000
        : false;
    },
  });

  const layers = layerOptions(mapQuery.data);
  const rankingRows = useMemo(
    () => buildRankingRows(contextQuery.data?.ranking ?? [], mapQuery.data),
    [contextQuery.data, mapQuery.data]
  );
  const filteredRanking = useMemo(
    () =>
      rankingRows.filter((row) => {
        const feature = mapQuery.data?.features.find(
          (candidate) => candidate.properties.territory_id === row.territory_id
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
    [mapQuery.data, rankingRows, searchTerm, severityFilter, statusFilter]
  );
  const selectedFeature = useMemo(
    () =>
      mapQuery.data?.features.find(
        (feature) => feature.properties.territory_id === selectedId
      ),
    [mapQuery.data, selectedId]
  );

  useEffect(() => {
    setLoadJobId(null);
    setHandledLoadJobId(null);
    setSelectedId(null);
  }, [uf, year, comparisonScope]);

  useEffect(() => {
    if (!selectedId && filteredRanking.length) {
      setSelectedId(filteredRanking[0].territory_id);
    }
  }, [filteredRanking, selectedId]);

  useEffect(() => {
    const job = loadJobQuery.data;
    if (job?.status !== 'complete' || handledLoadJobId === job.job_id) return;
    setHandledLoadJobId(job.job_id);
    void queryClient.invalidateQueries({ queryKey: ['territorial-context'] });
    void queryClient.invalidateQueries({ queryKey: ['territorial-map'] });
  }, [handledLoadJobId, loadJobQuery.data, queryClient]);

  function updateScope(next: Record<string, string | number>) {
    const params = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(next)) {
      params.set(key, String(value));
    }
    const nextUf = String(next.uf ?? uf).toUpperCase();
    if (nextUf === 'BR') {
      params.set('comparison_scope', 'national');
    }
    params.set('lang', lang);
    setSearchParams(params);
  }

  function selectFromSearch(value: string) {
    setSearchTerm(value);
    const match = mapQuery.data?.features.find((feature) =>
      feature.properties.name.toLowerCase().startsWith(value.toLowerCase())
    );
    if (match) setSelectedId(match.properties.territory_id);
  }

  const isLoading = contextQuery.isLoading || mapQuery.isLoading;
  const hasError = contextQuery.isError || mapQuery.isError;
  const loadJob = loadJobQuery.data ?? loadYearMutation.data;
  const isLoadRunning = Boolean(
    loadYearMutation.isPending ||
      loadJob?.status === 'queued' ||
      loadJob?.status === 'running'
  );
  const shouldOfferYearLoad = Boolean(
    contextQuery.data &&
      !contextQuery.isFetching &&
      contextQuery.data.territory_count > 0 &&
      contextQuery.data.indicator_count === 0
  );
  const shouldShowLoadPanel =
    shouldOfferYearLoad || Boolean(loadJob) || loadYearMutation.isPending;

  return (
    <div className="concept-page concept-territorial-page">
      <header className="concept-topbar">
        <div>
          <span className="concept-kicker">{labels.concept.visualConcept}</span>
          <h1>{labels.territorial.title}</h1>
          <p>{labels.concept.territorialBrief}</p>
        </div>
        <form className="concept-command-bar" aria-label={labels.territorial.commandScope}>
          <label>
            {labels.common.uf}
            <select value={uf} onChange={(event) => updateScope({ uf: event.target.value })}>
              {ufOptions.map((option) => (
                <option key={option} value={option}>
                  {option === 'BR' ? 'Brasil' : option}
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
              onChange={(event) => updateScope({ year: Number(event.target.value) })}
            />
          </label>
          <label>
            {labels.common.comparison}
            <select
              value={comparisonScope}
              disabled={uf === 'BR'}
              onChange={(event) => updateScope({ comparison_scope: event.target.value })}
            >
              <option value="national">{labels.common.national}</option>
              <option value="uf">{labels.common.ufRanking}</option>
            </select>
          </label>
        </form>
      </header>

      {shouldShowLoadPanel ? (
        <section className="concept-load-panel" aria-live="polite">
          <div>
            <strong>{labels.territorial.loadYearTitle}</strong>
            <p>{labels.territorial.loadYearText}</p>
          </div>
          <button
            type="button"
            onClick={() => loadYearMutation.mutate()}
            disabled={isLoadRunning}
          >
            <ConceptIcon name="refresh" size={17} />
            <span>
              {isLoadRunning
                ? labels.territorial.loadYearRunning
                : labels.territorial.loadYearButton}
            </span>
          </button>
          <ConceptLoadYearProgress job={loadJob} lang={lang} />
        </section>
      ) : null}

      <section className="concept-metric-strip" aria-label="Resumo territorial">
        <ConceptMetric label={labels.territorial.metrics.municipalities} value={formatNumber(contextQuery.data?.territory_count, lang)} />
        <ConceptMetric label={labels.territorial.metrics.indicators} value={formatNumber(contextQuery.data?.indicator_count, lang)} />
        <ConceptMetric label={labels.territorial.metrics.signals} value={formatNumber(contextQuery.data?.scenario_count, lang)} tone="attention" />
        <ConceptMetric label={labels.territorial.metrics.readiness} value={readinessSummary(contextQuery.data?.readiness, lang)} tone="good" />
      </section>

      <section className="concept-territorial-grid">
        <div className="concept-map-panel">
          <div className="concept-panel-header concept-split">
            <div>
              <h2>{labels.territorial.mapTitle}</h2>
              <p>{contextQuery.data?.caveat ?? labels.territorial.mapHelp}</p>
            </div>
            <div className="concept-map-tools">
              <label>
                {labels.territorial.mapMode}
                <span className="concept-segmented">
                  <button
                    type="button"
                    className={mapMode === 'priority' ? 'active' : ''}
                    onClick={() => setMapMode('priority')}
                  >
                    {labels.territorial.priorityMode}
                  </button>
                  <button
                    type="button"
                    className={mapMode === 'reference' ? 'active' : ''}
                    onClick={() => setMapMode('reference')}
                  >
                    {labels.territorial.referenceMode}
                  </button>
                </span>
              </label>
              <label>
                {labels.territorial.layer}
                <select value={layerId} onChange={(event) => setLayerId(event.target.value)}>
                  {layers.map((layer) => (
                    <option key={layer.id} value={layer.id}>
                      {layerLabel(layer, layer.id)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>
          <div className="concept-map-frame">
            {isLoading ? <div className="concept-map-status">{labels.common.loading}</div> : null}
            {hasError ? <div className="concept-map-status error">{labels.common.unavailable}</div> : null}
            <TerritorialMap
              payload={mapQuery.data}
              referencePayload={subterritoryQuery.data}
              layerId={layerId}
              selectedId={selectedId}
              referenceMode={mapMode === 'reference'}
              visualTone="concept"
              onSelect={setSelectedId}
            />
          </div>
          <div className="concept-map-caveat">
            <ConceptIcon name="territory" size={15} />
            <span>
              {mapMode === 'reference'
                ? subterritoryQuery.data?.metadata.caveat ?? labels.territorial.referenceCaveat
                : labels.territorial.mapHelp}
            </span>
          </div>
        </div>

        <aside className="concept-decision-panel">
          <DecisionPanel
            feature={selectedFeature}
            report={reportQuery.data}
            lang={lang}
            emptyText={labels.territorial.selectedEmpty}
          />
        </aside>
      </section>

      <section className="concept-lower-grid">
        <section className="concept-priority-panel">
          <div className="concept-panel-header concept-split">
            <div>
              <h2>{labels.territorial.rankingTitle}</h2>
              <p>{labels.concept.rankingBrief}</p>
            </div>
            <button
              type="button"
              className="concept-secondary-button"
              onClick={() => setIsRankingExpanded((value) => !value)}
              aria-expanded={isRankingExpanded}
            >
              {isRankingExpanded ? (
                <ConceptIcon name="close" size={16} />
              ) : (
                <ConceptIcon name="expand" size={16} />
              )}
              <span>
                {isRankingExpanded
                  ? labels.territorial.collapseRanking
                  : labels.territorial.expandRanking}
              </span>
            </button>
          </div>
          <div className="concept-table-tools">
            <label className="concept-search">
              <ConceptIcon name="search" size={15} />
              <input
                list="concept-municipality-options"
                value={searchTerm}
                placeholder={labels.territorial.municipalitySearch}
                onChange={(event) => selectFromSearch(event.target.value)}
              />
            </label>
            <datalist id="concept-municipality-options">
              {mapQuery.data?.features.map((feature) => (
                <option key={feature.properties.territory_id} value={feature.properties.name} />
              ))}
            </datalist>
            <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
              <option value="">{labels.common.severity}: {labels.common.all}</option>
              <option value="high">{labelSeverity('high', lang)}</option>
              <option value="moderate">{labelSeverity('moderate', lang)}</option>
              <option value="low">{labelSeverity('low', lang)}</option>
            </select>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">{labels.common.status}: {labels.common.all}</option>
              <option value="complete">{labelStatus('complete', lang)}</option>
              <option value="partial">{labelStatus('partial', lang)}</option>
              <option value="missing">{labelStatus('missing', lang)}</option>
            </select>
          </div>
          <PriorityRows
            rows={filteredRanking}
            selectedId={selectedId}
            expanded={isRankingExpanded}
            lang={lang}
            onSelect={setSelectedId}
          />
        </section>

        <section id="dados" className="concept-governance-panel">
          <div className="concept-panel-header">
            <h2>{labels.territorial.dataReadiness}</h2>
            <p>{labels.concept.readinessBrief}</p>
          </div>
          <ReadinessGrid items={contextQuery.data?.readiness} lang={lang} />
        </section>

        <section id="territorios-saude" className="concept-health-panel">
          <div className="concept-panel-header">
            <h2>{labels.territorial.healthTerritories}</h2>
            <p>{labels.territorial.referenceCaveat}</p>
          </div>
          <ReadinessGrid items={contextQuery.data?.health_territory_readiness} lang={lang} />
        </section>

        <section className="concept-source-panel">
          <div className="concept-panel-header">
            <h2>{labels.territorial.sourceFreshness}</h2>
          </div>
          <SourceRows sources={contextQuery.data?.sources ?? []} lang={lang} />
        </section>
      </section>
    </div>
  );
}

function ConceptMetric({
  label,
  value,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  tone?: 'neutral' | 'good' | 'attention';
}) {
  return (
    <div className={`concept-metric concept-metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DecisionPanel({
  feature,
  report,
  lang,
  emptyText,
}: {
  feature: FeatureCollection['features'][number] | undefined;
  report: TerritoryReport | undefined;
  lang: Language;
  emptyText: string;
}) {
  const labels = copy[lang];
  if (!feature) {
    return (
      <div className="concept-empty-panel">
        <ConceptIcon name="alert" size={18} />
        <p>{emptyText}</p>
      </div>
    );
  }
  const indicators =
    report?.indicators ??
    Object.entries(feature.properties.indicators).map(([indicatorId, indicator]) => ({
      indicator_id: indicatorId,
      indicator_name: indicator.name ?? indicatorId,
      ...indicator,
    }));
  const scenarios = report?.scenarios ?? feature.properties.top_scenarios;

  return (
    <div className="concept-decision-stack">
      <div>
        <span className="concept-overline">{feature.properties.uf}</span>
        <h2>{feature.properties.name}</h2>
        <div className="concept-badge-row">
          <StatusBadge value={feature.properties.top_severity} kind="severity" lang={lang} />
          <StatusBadge value={feature.properties.data_status} lang={lang} />
        </div>
      </div>
      <div className="concept-score-card">
        <span>{labels.territorial.metrics.signals}</span>
        <strong>{formatNumber(feature.properties.priority_score, lang, 1)}</strong>
      </div>
      <section>
        <h3>{labels.territorial.whyFlagged}</h3>
        {scenarios.length ? (
          <ul className="concept-signal-list">
            {scenarios.slice(0, 3).map((scenario) => (
              <li key={`${scenario.rule_id}-${scenario.indicator_id}`}>
                <ConceptIcon name="check" size={15} />
                <span>{scenario.explanation}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="concept-muted">{labels.territorial.noSignals}</p>
        )}
      </section>
      <section>
        <h3>{labels.territorial.recommendedResponse}</h3>
        {report?.recommendations?.length ? (
          <ul className="concept-signal-list">
            {report.recommendations.slice(0, 3).map((recommendation, index) => (
              <li key={`${recommendation.recommendation_id ?? recommendation.title ?? index}`}>
                <ConceptIcon name="check" size={15} />
                <span>{recommendation.action ?? recommendation.title ?? recommendation.explanation}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="concept-muted">-</p>
        )}
      </section>
      <section>
        <h3>{labels.territorial.indicators}</h3>
        <div className="concept-indicator-grid">
          {indicators.slice(0, 6).map((indicator) => (
            <div key={indicator.indicator_id}>
              <span>{indicator.indicator_name}</span>
              <strong>{formatIndicatorValue(indicator.value, indicator.unit, lang)}</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function PriorityRows({
  rows,
  selectedId,
  expanded,
  lang,
  onSelect,
}: {
  rows: RankingRow[];
  selectedId: string | null;
  expanded: boolean;
  lang: Language;
  onSelect: (territoryId: string) => void;
}) {
  const labels = copy[lang];
  const visibleRows = expanded ? rows : rows.slice(0, 6);
  if (!visibleRows.length) {
    return <p className="concept-empty-state">{labels.territorial.noSignals}</p>;
  }
  return (
    <div className="concept-ranking-list">
      {visibleRows.map((row, index) => (
        <button
          key={row.territory_id}
          type="button"
          className={row.territory_id === selectedId ? 'selected' : ''}
          onClick={() => onSelect(row.territory_id)}
        >
          <span className="concept-rank-index">{index + 1}</span>
          <span className="concept-rank-main">
            <strong>{row.territory_name}</strong>
            <small>{`${row.scenario_count} ${labels.territorial.metrics.signals}`}</small>
          </span>
          <StatusBadge value={row.top_severity} kind="severity" lang={lang} />
          <span className="concept-rank-score">{formatNumber(row.score, lang, 1)}</span>
        </button>
      ))}
    </div>
  );
}

function ReadinessGrid({
  items,
  lang,
}: {
  items: Record<string, ReadinessItem> | undefined;
  lang: Language;
}) {
  return (
    <div className="concept-readiness-grid">
      {Object.entries(items ?? {}).map(([key, item]) => (
        <div key={key} className={`concept-readiness-item concept-readiness-${item.status}`}>
          <div>
            <strong>{item.label}</strong>
            <small>{item.detail}</small>
          </div>
          <StatusBadge value={item.status} lang={lang} />
        </div>
      ))}
    </div>
  );
}

function SourceRows({ sources, lang }: { sources: SourceRow[]; lang: Language }) {
  return (
    <div className="concept-source-list">
      {sources.slice(0, 6).map((source) => (
        <div key={source.source_id} className="concept-source-row">
          <div>
            <strong>{source.name}</strong>
            <small>{source.message}</small>
          </div>
          <StatusBadge value={source.status} lang={lang} />
        </div>
      ))}
    </div>
  );
}

function ConceptLoadYearProgress({ job, lang }: { job: LoadYearJob | undefined; lang: Language }) {
  const labels = copy[lang];
  if (!job) return null;
  const progress = Math.max(0, Math.min(100, Math.round((job.step_index / job.step_count) * 100)));
  return (
    <div className="concept-load-progress">
      <div>
        <strong>{labels.territorial.loadYearProgress}</strong>
        <span>{`${labels.territorial.loadYearStep} ${job.step_index}/${job.step_count}`}</span>
      </div>
      <div className="concept-progress-track" aria-hidden="true">
        <span style={{ width: `${progress}%` }} />
      </div>
      <p>{job.message}</p>
      {job.error ? <small>{`${labels.territorial.loadYearTechnicalError}: ${job.error}`}</small> : null}
    </div>
  );
}

function readinessSummary(items: Record<string, { status: string }> | undefined, lang: Language) {
  if (!items) return '-';
  const statuses = Object.values(items).map((item) => item.status);
  if (statuses.every((status) => status === 'ready')) return labelStatus('ready', lang);
  if (statuses.some((status) => status === 'warning')) return labelStatus('warning', lang);
  if (statuses.some((status) => status === 'partial')) return labelStatus('partial', lang);
  return labelStatus('missing', lang);
}

function buildRankingRows(rows: RankingRow[], payload: FeatureCollection | undefined): RankingRow[] {
  if (rows.length) return rows;
  return [...(payload?.features ?? [])]
    .filter((feature) => feature.properties.scenario_count > 0)
    .sort((left, right) => right.properties.priority_score - left.properties.priority_score)
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
