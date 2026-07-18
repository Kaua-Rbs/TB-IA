import { ChevronDown, ChevronUp, Search } from "lucide-react";
import { useState } from "react";

import type { FeatureCollection, RankingRow } from "../lib/api";
import { formatNumber, labelSeverity, labelStatus } from "../lib/format";
import { copy, type Language } from "../lib/i18n";
import { StatusBadge } from "./StatusBadge";

const COLLAPSED_RANKING_SIZE = 6;

interface PriorityRankingListProps {
  rows: RankingRow[];
  mapPayload: FeatureCollection | undefined;
  selectedId: string | null;
  searchTerm: string;
  severityFilter: string;
  statusFilter: string;
  lang: Language;
  onSearchChange: (value: string) => void;
  onSeverityFilterChange: (value: string) => void;
  onStatusFilterChange: (value: string) => void;
  onSelect: (territoryId: string) => void;
}

export function PriorityRankingList({
  rows,
  mapPayload,
  selectedId,
  searchTerm,
  severityFilter,
  statusFilter,
  lang,
  onSearchChange,
  onSeverityFilterChange,
  onStatusFilterChange,
  onSelect,
}: PriorityRankingListProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const labels = copy[lang];
  const canExpand = rows.length > COLLAPSED_RANKING_SIZE;
  const visibleRows = isExpanded
    ? rows
    : rows.slice(0, COLLAPSED_RANKING_SIZE);

  return (
    <section className="ranking-section">
      <div className="panel-heading split-heading">
        <div>
          <h2>{labels.territorial.rankingTitle}</h2>
          <p>{labels.territorial.rankingSubtitle}</p>
        </div>
        {canExpand ? (
          <button
            type="button"
            className="secondary-action"
            onClick={() => setIsExpanded((value) => !value)}
            aria-expanded={isExpanded}
            aria-controls="priority-ranking-list"
          >
            {isExpanded ? (
              <ChevronUp size={17} aria-hidden="true" />
            ) : (
              <ChevronDown size={17} aria-hidden="true" />
            )}
            <span>
              {isExpanded
                ? labels.territorial.collapseRanking
                : labels.territorial.expandRanking}
            </span>
          </button>
        ) : null}
      </div>

      <div className="table-tools ranking-tools">
        <label className="search-control">
          <Search size={16} aria-hidden="true" />
          <input
            aria-label={labels.territorial.municipalitySearch}
            list="municipality-options"
            value={searchTerm}
            placeholder={labels.territorial.municipalitySearch}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </label>
        <datalist id="municipality-options">
          {mapPayload?.features.map((feature) => (
            <option
              key={feature.properties.territory_id}
              value={feature.properties.name}
            />
          ))}
        </datalist>
        <select
          aria-label={labels.common.severity}
          value={severityFilter}
          onChange={(event) => onSeverityFilterChange(event.target.value)}
        >
          <option value="">
            {labels.common.severity}: {labels.common.all}
          </option>
          <option value="high">{labelSeverity("high", lang)}</option>
          <option value="moderate">
            {labelSeverity("moderate", lang)}
          </option>
          <option value="low">{labelSeverity("low", lang)}</option>
        </select>
        <select
          aria-label={labels.common.status}
          value={statusFilter}
          onChange={(event) => onStatusFilterChange(event.target.value)}
        >
          <option value="">
            {labels.common.status}: {labels.common.all}
          </option>
          <option value="complete">{labelStatus("complete", lang)}</option>
          <option value="partial">{labelStatus("partial", lang)}</option>
          <option value="missing">{labelStatus("missing", lang)}</option>
        </select>
      </div>

      <ol id="priority-ranking-list" className="priority-ranking-list">
        {visibleRows.map((row, index) => {
          const score = formatNumber(row.score, lang, 1);
          return (
            <li key={row.territory_id}>
              <button
                type="button"
                className={
                  "priority-ranking-row" +
                  (row.territory_id === selectedId ? " selected" : "")
                }
                aria-pressed={row.territory_id === selectedId}
                onClick={() => onSelect(row.territory_id)}
              >
                <span className="priority-ranking-index">{index + 1}</span>
                <strong className="priority-ranking-name">
                  {row.territory_name}
                </strong>
                <span className="priority-ranking-signals">
                  <strong>{formatNumber(row.scenario_count, lang)}</strong>{" "}
                  {row.scenario_count === 1
                    ? labels.territorial.signalSingular
                    : labels.territorial.signalCount}
                </span>
                <StatusBadge
                  value={row.top_severity}
                  kind="severity"
                  lang={lang}
                />
                <span
                  className="priority-ranking-score"
                  aria-label={labels.territorial.priorityScore + ": " + score}
                >
                  {score}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
      {!rows.length ? (
        <p className="empty-state">{labels.territorial.noSignals}</p>
      ) : null}
    </section>
  );
}
