import { AlertTriangle } from "lucide-react";
import { useId } from "react";

import type {
  IndicatorHistory,
  IndicatorHistoryPoint,
  IndicatorHistorySource,
} from "../lib/api";
import { formatIndicatorValue, formatNumber } from "../lib/format";
import { copy, type Language } from "../lib/i18n";

interface IncidenceHistoryProps {
  history: IndicatorHistory | null | undefined;
  isLoading: boolean;
  isError: boolean;
  lang: Language;
}

const chartWidth = 300;
const chartHeight = 132;
const chartLeft = 16;
const chartRight = 284;
const chartTop = 14;
const chartBottom = 91;

export function IncidenceHistory({
  history,
  isLoading,
  isError,
  lang,
}: IncidenceHistoryProps) {
  const labels = copy[lang].territorial.history;
  const titleId = useId();

  return (
    <section
      className="detail-section incidence-history"
      aria-labelledby={titleId}
      aria-busy={isLoading}
    >
      <div className="history-title-row">
        <h4 id={titleId}>{labels.title}</h4>
        {history ? (
          <span
            className={`history-coverage history-coverage-${history.coverage.status}`}
          >
            {history.coverage.available_year_count}/
            {history.coverage.requested_year_count} {labels.availableYears}
          </span>
        ) : null}
      </div>
      <p className="history-boundary">{labels.boundary}</p>
      {isLoading ? (
        <p className="history-state">{labels.loading}</p>
      ) : isError ? (
        <p className="history-state history-state-error">{labels.error}</p>
      ) : history ? (
        <HistoryContent history={history} lang={lang} />
      ) : (
        <p className="history-state">{labels.unavailable}</p>
      )}
    </section>
  );
}

function HistoryContent({
  history,
  lang,
}: {
  history: IndicatorHistory;
  lang: Language;
}) {
  const labels = copy[lang].territorial.history;

  return (
    <div className="history-content">
      <HistoryChart history={history} lang={lang} />
      <div className="history-year-strip" role="list" aria-label={labels.annualValues}>
        {history.points.map((point) => (
          <div
            className={`history-year history-year-${point.status}`}
            key={point.year}
            role="listitem"
          >
            <span>{point.year}</span>
            <strong>
              {point.status === "available"
                ? formatIndicatorValue(point.value, history.unit, lang)
                : point.status_label ?? labels.statuses[point.status]}
            </strong>
          </div>
        ))}
      </div>
      <ul className="history-key" aria-label={labels.availability}>
        {(["available", "suppressed", "missing"] as const).map((status) => (
          <li key={status}>
            <span className={`history-status-mark history-status-${status}`} />
            {labels.statuses[status]}
          </li>
        ))}
      </ul>
      {history.comparability_flags.length ? (
        <ul className="history-flags">
          {history.comparability_flags.map((flag) => (
            <li key={flag.code}>
              <AlertTriangle size={14} aria-hidden="true" />
              <span>{flag.detail ?? flag.code}</span>
              <strong>{flag.years.join(", ")}</strong>
            </li>
          ))}
        </ul>
      ) : (
        <p className="history-no-flags">{labels.noFlags}</p>
      )}
      <details className="history-audit">
        <summary>{labels.auditDetails}</summary>
        <div className="history-audit-list">
          {history.points.map((point) => (
            <AnnualEvidence
              key={point.year}
              point={point}
              unit={history.unit}
              lang={lang}
            />
          ))}
        </div>
      </details>
    </div>
  );
}

function HistoryChart({
  history,
  lang,
}: {
  history: IndicatorHistory;
  lang: Language;
}) {
  const labels = copy[lang].territorial.history;
  const titleId = useId();
  const available = history.points.filter(
    (point): point is IndicatorHistoryPoint & { value: number } =>
      point.status === "available" && point.value !== null,
  );
  const values = available.map((point) => point.value);
  const minimum = values.length ? Math.min(...values) : 0;
  const maximum = values.length ? Math.max(...values) : 1;
  const spread = maximum - minimum || Math.max(Math.abs(maximum) * 0.1, 1);
  const domainMinimum = minimum - spread * 0.12;
  const domainMaximum = maximum + spread * 0.12;
  const segments = availableSegments(history.points);

  function xPosition(index: number) {
    if (history.points.length <= 1) return chartWidth / 2;
    return (
      chartLeft +
      (index / (history.points.length - 1)) * (chartRight - chartLeft)
    );
  }

  function yPosition(value: number) {
    return (
      chartBottom -
      ((value - domainMinimum) / (domainMaximum - domainMinimum)) *
        (chartBottom - chartTop)
    );
  }

  return (
    <svg
      className="history-chart"
      viewBox={`0 0 ${chartWidth} ${chartHeight}`}
      role="img"
      aria-labelledby={titleId}
    >
      <title id={titleId}>
        {history.indicator_name}: {history.start_year}-{history.end_year}.{" "}
        {labels.boundary}
      </title>
      {[chartTop, (chartTop + chartBottom) / 2, chartBottom].map((y) => (
        <line
          className="history-chart-grid"
          key={y}
          x1={chartLeft}
          x2={chartRight}
          y1={y}
          y2={y}
        />
      ))}
      {segments.map((segment) => (
        <polyline
          className="history-chart-line"
          key={segment.map((point) => point.year).join("-")}
          points={segment
            .map((point) => {
              const index = history.points.findIndex(
                (candidate) => candidate.year === point.year,
              );
              return `${xPosition(index)},${yPosition(point.value ?? 0)}`;
            })
            .join(" ")}
        />
      ))}
      {history.points.map((point, index) => {
        const x = xPosition(index);
        const statusLabel =
          point.status_label ?? labels.statuses[point.status];
        const valueLabel =
          point.status === "available"
            ? formatIndicatorValue(point.value, history.unit, lang)
            : statusLabel;
        return (
          <g key={point.year}>
            <title>{`${point.year}: ${valueLabel}`}</title>
            {point.status === "available" && point.value !== null ? (
              <circle
                className="history-chart-point"
                cx={x}
                cy={yPosition(point.value)}
                r="4"
              />
            ) : point.status === "suppressed" ? (
              <rect
                className="history-chart-suppressed"
                x={x - 4}
                y={chartBottom - 4}
                width="8"
                height="8"
                rx="1"
              />
            ) : (
              <circle
                className="history-chart-missing"
                cx={x}
                cy={chartBottom}
                r="4"
              />
            )}
            <text className="history-chart-year" x={x} y="119">
              {point.year}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function availableSegments(
  points: IndicatorHistoryPoint[],
): IndicatorHistoryPoint[][] {
  const segments: IndicatorHistoryPoint[][] = [];
  let current: IndicatorHistoryPoint[] = [];
  for (const point of points) {
    if (point.status === "available" && point.value !== null) {
      current.push(point);
    } else if (current.length) {
      segments.push(current);
      current = [];
    }
  }
  if (current.length) segments.push(current);
  return segments;
}

function AnnualEvidence({
  point,
  unit,
  lang,
}: {
  point: IndicatorHistoryPoint;
  unit: string | null;
  lang: Language;
}) {
  const labels = copy[lang].territorial.history;
  const statusLabel = point.status_label ?? labels.statuses[point.status];
  const countSummary =
    point.status === "available" &&
    point.numerator_value !== null &&
    point.denominator_value !== null
      ? `${labels.cases}: ${formatNumber(point.numerator_value, lang)} · ${labels.population}: ${formatNumber(point.denominator_value, lang)}`
      : null;

  return (
    <div className="history-audit-row">
      <div className="history-audit-heading">
        <strong>{point.year}</strong>
        <span className={`history-audit-status history-audit-${point.status}`}>
          {statusLabel}
        </span>
      </div>
      <div className="history-audit-measure">
        {point.status === "available" ? (
          <strong>{formatIndicatorValue(point.value, unit, lang)}</strong>
        ) : null}
        {countSummary ? <small>{countSummary}</small> : null}
        {point.denominator_year ? (
          <small>
            {labels.populationReference}: {point.denominator_year}
          </small>
        ) : null}
      </div>
      <div className="history-audit-sources">
        {point.source_provenance.map((source) => (
          <small key={source.source_id}>{sourceSummary(source)}</small>
        ))}
        {point.caveats ? <small>{point.caveats}</small> : null}
      </div>
    </div>
  );
}

function sourceSummary(source: IndicatorHistorySource) {
  const sourceName = source.source_label ?? source.source_id;
  const details = [
    source.release_status_label ?? source.release_status,
    source.dataset_kind_label ?? source.dataset_kind,
    source.reference_year,
  ].filter((value) => value !== null && value !== undefined && value !== "");
  return `${sourceName}: ${details.join(" · ")}`;
}
