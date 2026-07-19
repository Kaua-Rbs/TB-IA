import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ClipboardList,
  ListFilter,
  RotateCcw
} from 'lucide-react';
import { useEffect, useMemo, useState, type KeyboardEvent } from 'react';
import { useSearchParams } from 'react-router-dom';

import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import {
  fetchOperationAlert,
  fetchOperationAlerts,
  fetchOperationsSummary,
  type OperationalAlert
} from '../lib/api';
import { formatDate, formatNumber, labelAlertType } from '../lib/format';
import { copy, normalizeLanguage, type Language } from '../lib/i18n';

const operationFilterKeys = [
  'alert_type',
  'severity',
  'status',
  'facility_id',
  'team_id'
] as const;

export function OperationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const lang = normalizeLanguage(searchParams.get('lang'));
  const labels = copy[lang];
  const year = Number(searchParams.get('year') || '2023');
  const filters = {
    alertType: searchParams.get('alert_type') || '',
    severity: searchParams.get('severity') || '',
    facilityId: searchParams.get('facility_id') || '',
    teamId: searchParams.get('team_id') || '',
    status: searchParams.get('status') || ''
  };
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);
  const [filtersExpanded, setFiltersExpanded] = useState(
    () =>
      typeof window === 'undefined' ||
      !window.matchMedia?.('(max-width: 760px)').matches
  );

  const summaryQuery = useQuery({
    queryKey: ['operations-summary', year],
    queryFn: () => fetchOperationsSummary(year)
  });
  const alertsQuery = useQuery({
    queryKey: ['operations-alerts', year, filters, lang],
    queryFn: () =>
      fetchOperationAlerts({
        year,
        alertType: filters.alertType,
        severity: filters.severity,
        facilityId: filters.facilityId,
        teamId: filters.teamId,
        status: filters.status,
        lang
      })
  });
  const detailQuery = useQuery({
    queryKey: ['operations-alert', selectedAlertId, lang],
    queryFn: () => fetchOperationAlert(selectedAlertId ?? '', lang),
    enabled: Boolean(selectedAlertId)
  });

  const highAlertCount =
    summaryQuery.data?.by_severity.find((row) => row.severity === 'high')
      ?.count ?? 0;
  const facilityOptions = useMemo(
    () => [
      ...new Set(
        summaryQuery.data?.by_facility_team.map((row) => row.facility_id) ?? []
      )
    ],
    [summaryQuery.data]
  );
  const teamOptions = useMemo(
    () => summaryQuery.data?.by_facility_team ?? [],
    [summaryQuery.data]
  );
  const visibleTeamOptions = useMemo(
    () =>
      teamOptions.filter(
        (row) => !filters.facilityId || row.facility_id === filters.facilityId
      ),
    [filters.facilityId, teamOptions]
  );
  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  useEffect(() => {
    if (!alertsQuery.data?.length) {
      setSelectedAlertId(null);
      setExpandedAlertId(null);
      return;
    }
    if (
      !selectedAlertId ||
      !alertsQuery.data.some((alert) => alert.alert_id === selectedAlertId)
    ) {
      setSelectedAlertId(alertsQuery.data[0].alert_id);
    }
    if (
      expandedAlertId &&
      !alertsQuery.data.some((alert) => alert.alert_id === expandedAlertId)
    ) {
      setExpandedAlertId(null);
    }
  }, [alertsQuery.data, expandedAlertId, selectedAlertId]);

  useEffect(() => {
    const mobileQuery = window.matchMedia?.('(max-width: 760px)');
    if (!mobileQuery) return;
    const synchronizeFilterPanel = (event: MediaQueryListEvent) => {
      setFiltersExpanded(!event.matches);
    };
    setFiltersExpanded(!mobileQuery.matches);
    mobileQuery.addEventListener('change', synchronizeFilterPanel);
    return () => {
      mobileQuery.removeEventListener('change', synchronizeFilterPanel);
    };
  }, []);

  function updateFilter(key: string, value: string | number) {
    const params = new URLSearchParams(searchParams);
    if (value === '') {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
    if (key === 'facility_id') {
      params.delete('team_id');
    }
    params.set('lang', lang);
    setExpandedAlertId(null);
    setSearchParams(params);
  }

  function resetFilters() {
    const params = new URLSearchParams(searchParams);
    for (const key of operationFilterKeys) {
      params.delete(key);
    }
    params.set('lang', lang);
    setExpandedAlertId(null);
    setSearchParams(params);
  }

  function selectAlert(alertId: string) {
    setSelectedAlertId(alertId);
    setExpandedAlertId((current) => (current === alertId ? null : alertId));
  }

  return (
    <div className="page-stack operations-page">
      <header className="page-hero compact-hero operations-hero">
        <div>
          <span className="situation-kicker">{labels.productContext}</span>
          <h1>{labels.operations.title}</h1>
          <p>{labels.operations.subtitle}</p>
          <div className="badge-row operations-boundary">
            <span className="product-badge synthetic">
              {labels.operations.syntheticBadge}
            </span>
          </div>
        </div>
        <form className="command-bar" aria-label={labels.operations.filters}>
          <label>
            {labels.common.year}
            <input
              type="number"
              min="2000"
              max="2100"
              value={year}
              onChange={(event) =>
                updateFilter('year', Number(event.target.value))
              }
            />
          </label>
        </form>
      </header>

      <section className="caveat-band synthetic-band">
        <AlertCircle size={18} aria-hidden="true" />
        <span>{labels.operations.caveat}</span>
      </section>

      <section className="metric-strip" aria-label={labels.operations.summary}>
        <MetricCard
          label={labels.operations.localCases}
          value={formatNumber(summaryQuery.data?.case_count, lang)}
        />
        <MetricCard
          label={labels.operations.totalAlerts}
          value={formatNumber(summaryQuery.data?.alert_count, lang)}
        />
        <MetricCard
          label={labels.operations.openAlerts}
          value={formatNumber(summaryQuery.data?.open_alert_count, lang)}
        />
        <MetricCard
          label={labels.operations.highAlerts}
          value={formatNumber(highAlertCount, lang)}
          tone="danger"
        />
      </section>

      <section className="operations-layout">
        <div className="queue-panel">
          <div className="panel-heading split-heading">
            <div>
              <h2>{labels.operations.queue}</h2>
              <p>{labels.operations.subtitle}</p>
            </div>
            <div className="queue-toolbar">
              <button
                type="button"
                className="operations-filter-toggle"
                aria-expanded={filtersExpanded}
                aria-controls="operations-filter-panel"
                aria-label={filterToggleLabel(
                  filtersExpanded,
                  activeFilterCount,
                  lang
                )}
                onClick={() => setFiltersExpanded((current) => !current)}
              >
                <ListFilter size={15} aria-hidden="true" />
                <span>{labels.operations.filters}</span>
                {activeFilterCount ? (
                  <span className="active-filter-count">
                    {activeFilterCount}
                  </span>
                ) : null}
                <ChevronDown
                  className={filtersExpanded ? 'expanded' : ''}
                  size={15}
                  aria-hidden="true"
                />
              </button>
              {activeFilterCount ? (
                <button
                  type="button"
                  className="filters-reset"
                  onClick={resetFilters}
                >
                  <RotateCcw size={14} aria-hidden="true" />
                  <span>{labels.operations.resetFilters}</span>
                </button>
              ) : null}
            </div>
          </div>

          <div
            id="operations-filter-panel"
            className={
              'table-tools operations-filters' +
              (filtersExpanded ? ' expanded' : '')
            }
            role="group"
            aria-label={labels.operations.filters}
          >
            <label className="filter-field">
              <span>{labels.operations.type}</span>
              <select
                value={filters.alertType}
                onChange={(event) =>
                  updateFilter('alert_type', event.target.value)
                }
              >
                <option value="">{labels.common.all}</option>
                <option value="pending_lab_result">
                  {labelAlertType('pending_lab_result', labels)}
                </option>
                <option value="medication_pickup_delay">
                  {labelAlertType('medication_pickup_delay', labels)}
                </option>
                <option value="contact_pending_evaluation">
                  {labelAlertType('contact_pending_evaluation', labels)}
                </option>
                <option value="resistance_vigilance">
                  {labelAlertType('resistance_vigilance', labels)}
                </option>
              </select>
            </label>
            <label className="filter-field">
              <span>{labels.common.severity}</span>
              <select
                value={filters.severity}
                onChange={(event) =>
                  updateFilter('severity', event.target.value)
                }
              >
                <option value="">{labels.common.all}</option>
                <option value="high">{labels.severities.high}</option>
                <option value="moderate">{labels.severities.moderate}</option>
              </select>
            </label>
            <label className="filter-field">
              <span>{labels.common.status}</span>
              <select
                value={filters.status}
                onChange={(event) =>
                  updateFilter('status', event.target.value)
                }
              >
                <option value="">{labels.common.all}</option>
                <option value="open">{labels.statuses.open}</option>
                <option value="closed">{labels.statuses.closed}</option>
              </select>
            </label>
            <label className="filter-field">
              <span>{labels.operations.facility}</span>
              <select
                value={filters.facilityId}
                onChange={(event) =>
                  updateFilter('facility_id', event.target.value)
                }
              >
                <option value="">{labels.common.all}</option>
                {facilityOptions.map((facilityId) => (
                  <option key={facilityId} value={facilityId}>
                    {facilityId}
                  </option>
                ))}
              </select>
            </label>
            <label className="filter-field">
              <span>{labels.operations.team}</span>
              <select
                value={filters.teamId}
                onChange={(event) =>
                  updateFilter('team_id', event.target.value)
                }
              >
                <option value="">{labels.common.all}</option>
                {visibleTeamOptions.map((row) => (
                  <option
                    key={row.facility_id + '-' + row.team_id}
                    value={row.team_id}
                  >
                    {row.team_name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="table-shell queue-table">
            <table>
              <thead>
                <tr>
                  <th>{labels.operations.type}</th>
                  <th>{labels.common.severity}</th>
                  <th>{labels.common.status}</th>
                  <th>{labels.operations.facility}</th>
                  <th>{labels.operations.team}</th>
                  <th>{labels.operations.due}</th>
                </tr>
              </thead>
              <tbody>
                {alertsQuery.data?.map((alert) => (
                  <AlertRow
                    key={alert.alert_id}
                    alert={alert}
                    selected={alert.alert_id === selectedAlertId}
                    expanded={alert.alert_id === expandedAlertId}
                    detailAlert={
                      alert.alert_id === selectedAlertId
                        ? detailQuery.data
                        : undefined
                    }
                    detailLoading={
                      alert.alert_id === selectedAlertId &&
                      detailQuery.isLoading
                    }
                    lang={lang}
                    onSelect={selectAlert}
                  />
                ))}
              </tbody>
            </table>
            {alertsQuery.isLoading ? (
              <p className="empty-state">{labels.common.loading}</p>
            ) : null}
            {!alertsQuery.isLoading && !alertsQuery.data?.length ? (
              <p className="empty-state">{labels.common.empty}</p>
            ) : null}
          </div>
        </div>

        <aside className="detail-panel operations-detail" aria-live="polite">
          <span className="dossier-kicker">
            {labels.operations.dossierTitle}
          </span>
          <h2>{labels.operations.alertDetail}</h2>
          {!selectedAlertId ? (
            <p className="muted-copy">{labels.operations.selectAlert}</p>
          ) : null}
          {detailQuery.data ? (
            <AlertDetail alert={detailQuery.data} lang={lang} />
          ) : null}
        </aside>
      </section>

      <section className="facility-panel">
        <div className="panel-heading">
          <h2>{labels.operations.facilityTeams}</h2>
        </div>
        <div className="facility-grid">
          {teamOptions.map((row) => (
            <div
              key={row.facility_id + '-' + row.team_id}
              className="facility-card"
            >
              <ClipboardList size={18} aria-hidden="true" />
              <div>
                <strong>{row.team_name}</strong>
                <span>{row.facility_id}</span>
              </div>
              <dl>
                <div>
                  <dt>{labels.operations.totalAlerts}</dt>
                  <dd>{row.alert_count}</dd>
                </div>
                <div>
                  <dt>{labels.operations.highAlerts}</dt>
                  <dd>{row.high}</dd>
                </div>
                <div>
                  <dt>{labels.operations.openAlerts}</dt>
                  <dd>{row.open}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function AlertRow({
  alert,
  selected,
  expanded,
  detailAlert,
  detailLoading,
  lang,
  onSelect
}: {
  alert: OperationalAlert;
  selected: boolean;
  expanded: boolean;
  detailAlert: OperationalAlert | undefined;
  detailLoading: boolean;
  lang: Language;
  onSelect: (alertId: string) => void;
}) {
  const labels = copy[lang];
  const overdue = isAlertOverdue(alert);
  const detailId = 'mobile-alert-detail-' + alert.alert_id;
  function selectWithKeyboard(event: KeyboardEvent<HTMLTableRowElement>) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    onSelect(alert.alert_id);
  }

  return (
    <>
      <tr
        className={[
          'alert-row',
          selected ? 'selected-row' : '',
          alert.severity === 'high' ? 'severity-high-row' : '',
          overdue ? 'overdue-row' : ''
        ]
          .filter(Boolean)
          .join(' ')}
        onClick={() => onSelect(alert.alert_id)}
        onKeyDown={selectWithKeyboard}
        tabIndex={0}
        aria-selected={selected}
        aria-expanded={expanded}
        aria-controls={detailId}
      >
        <td data-label={labels.operations.type}>
          <div className="alert-type-cell">
            <span>{labelAlertType(alert.alert_type, labels)}</span>
            <ChevronDown
              className={
                'mobile-expand-icon' + (expanded ? ' expanded' : '')
              }
              size={17}
              aria-hidden="true"
            />
          </div>
        </td>
        <td data-label={labels.common.severity}>
          <div className="severity-cell">
            {alert.severity === 'high' ? (
              <AlertTriangle
                className="severity-marker"
                size={14}
                aria-hidden="true"
              />
            ) : null}
            <StatusBadge
              value={alert.severity}
              kind="severity"
              lang={lang}
            />
          </div>
        </td>
        <td data-label={labels.common.status}>
          <StatusBadge value={alert.status} lang={lang} />
        </td>
        <td data-label={labels.operations.facility}>{alert.facility_id}</td>
        <td data-label={labels.operations.team}>{alert.team_name}</td>
        <td
          className={overdue ? 'due-cell overdue' : 'due-cell'}
          data-label={labels.operations.due}
        >
          <span className="due-date">
            {overdue ? (
              <AlertTriangle size={13} aria-hidden="true" />
            ) : null}
            <span>{formatDate(alert.due_date, lang)}</span>
          </span>
          {overdue ? <small>{labels.operations.overdue}</small> : null}
        </td>
      </tr>
      {expanded ? (
        <tr id={detailId} className="mobile-alert-detail-row">
          <td colSpan={6}>
            {detailLoading ? (
              <p className="empty-state">{labels.common.loading}</p>
            ) : null}
            {detailAlert ? (
              <AlertDetail alert={detailAlert} lang={lang} />
            ) : null}
          </td>
        </tr>
      ) : null}
    </>
  );
}

function AlertDetail({
  alert,
  lang
}: {
  alert: OperationalAlert;
  lang: Language;
}) {
  const labels = copy[lang];
  return (
    <div className="detail-stack">
      <section className="detail-section">
        <h4>{labels.operations.whereReview}</h4>
        <span className="eyebrow">{alert.facility_id}</span>
        <h3>{alert.team_name}</h3>
        <div className="indicator-list">
          <div>
            <span>{labels.operations.case}</span>
            <strong>{alert.local_case_id}</strong>
          </div>
          <div>
            <span>{labels.operations.facility}</span>
            <strong>{alert.facility_id}</strong>
          </div>
        </div>
      </section>
      <section className="detail-section">
        <h4>{labels.operations.whyReview}</h4>
        <p>
          <strong>{labelAlertType(alert.alert_type, labels)}</strong>
        </p>
        <p>{alert.message}</p>
        <div className="badge-row">
          <StatusBadge
            value={alert.severity}
            kind="severity"
            lang={lang}
          />
          <StatusBadge value={alert.status} lang={lang} />
        </div>
      </section>
      <section className="detail-section">
        <h4>{labels.operations.reviewWindow}</h4>
        <div className="indicator-list">
          <div>
            <span>{labels.operations.reference}</span>
            <strong>{formatDate(alert.reference_date, lang)}</strong>
          </div>
          <div>
            <span>{labels.operations.due}</span>
            <strong>{formatDate(alert.due_date, lang)}</strong>
          </div>
        </div>
      </section>
    </div>
  );
}

function isAlertOverdue(alert: OperationalAlert) {
  if (alert.status !== 'open' || !alert.due_date) return false;
  const dueAt = new Date(alert.due_date.slice(0, 10) + 'T23:59:59Z');
  return !Number.isNaN(dueAt.getTime()) && dueAt.getTime() < Date.now();
}

function filterToggleLabel(
  expanded: boolean,
  activeFilterCount: number,
  lang: Language
) {
  const labels = copy[lang].operations;
  const action = expanded ? labels.hideFilters : labels.showFilters;
  if (!activeFilterCount) return action;
  const countLabel =
    activeFilterCount === 1
      ? labels.activeFilterSingular
      : labels.activeFilterPlural;
  return action + '. ' + activeFilterCount + ' ' + countLabel;
}
