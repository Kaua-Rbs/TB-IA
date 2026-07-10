import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { ConceptIcon } from '../components/ConceptIcon';
import { StatusBadge } from '../components/StatusBadge';
import {
  fetchOperationAlert,
  fetchOperationAlerts,
  fetchOperationsSummary,
  type OperationalAlert,
} from '../lib/api';
import { formatDate, formatNumber, labelAlertType, labelStatus } from '../lib/format';
import { copy, normalizeLanguage, type Language } from '../lib/i18n';

export function ConceptOperationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const lang = normalizeLanguage(searchParams.get('lang'));
  const labels = copy[lang];
  const year = Number(searchParams.get('year') || '2023');
  const filters = {
    alertType: searchParams.get('alert_type') || '',
    severity: searchParams.get('severity') || '',
    facilityId: searchParams.get('facility_id') || '',
    teamId: searchParams.get('team_id') || '',
    status: searchParams.get('status') || '',
  };
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const summaryQuery = useQuery({
    queryKey: ['operations-summary', year],
    queryFn: () => fetchOperationsSummary(year),
  });
  const alertsQuery = useQuery({
    queryKey: ['operations-alerts', year, filters],
    queryFn: () =>
      fetchOperationAlerts({
        year,
        alertType: filters.alertType,
        severity: filters.severity,
        facilityId: filters.facilityId,
        teamId: filters.teamId,
        status: filters.status,
      }),
  });
  const detailQuery = useQuery({
    queryKey: ['operations-alert', selectedAlertId],
    queryFn: () => fetchOperationAlert(selectedAlertId ?? ''),
    enabled: Boolean(selectedAlertId),
  });

  const highAlertCount =
    summaryQuery.data?.by_severity.find((row) => row.severity === 'high')?.count ?? 0;
  const facilityOptions = useMemo(
    () => [...new Set(summaryQuery.data?.by_facility_team.map((row) => row.facility_id) ?? [])],
    [summaryQuery.data]
  );
  const teamOptions = useMemo(
    () => summaryQuery.data?.by_facility_team ?? [],
    [summaryQuery.data]
  );
  const filteredAlerts = useMemo(
    () =>
      (alertsQuery.data ?? []).filter((alert) => {
        const needle = searchTerm.toLowerCase();
        if (!needle) return true;
        return [alert.local_case_id, alert.facility_id, alert.team_name, alert.message]
          .join(' ')
          .toLowerCase()
          .includes(needle);
      }),
    [alertsQuery.data, searchTerm]
  );

  useEffect(() => {
    if (!filteredAlerts.length) {
      setSelectedAlertId(null);
      return;
    }
    if (!selectedAlertId || !filteredAlerts.some((alert) => alert.alert_id === selectedAlertId)) {
      setSelectedAlertId(filteredAlerts[0].alert_id);
    }
  }, [filteredAlerts, selectedAlertId]);

  function updateFilter(key: string, value: string | number) {
    const params = new URLSearchParams(searchParams);
    if (value === '') {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
    params.set('lang', lang);
    setSearchParams(params);
  }

  return (
    <div className="concept-page concept-operations-page">
      <header className="concept-topbar concept-operations-topbar">
        <div>
          <span className="concept-kicker">{labels.concept.visualConcept}</span>
          <h1>{labels.operations.title}</h1>
          <p>{labels.concept.operationsBrief}</p>
        </div>
        <form className="concept-command-bar concept-command-bar-single" aria-label={labels.operations.filters}>
          <label>
            {labels.common.year}
            <input
              type="number"
              min="2000"
              max="2100"
              value={year}
              onChange={(event) => updateFilter('year', Number(event.target.value))}
            />
          </label>
        </form>
      </header>

      <section className="concept-caveat-band">
        <ConceptIcon name="alerts" size={18} />
        <span>{labels.operations.caveat}</span>
      </section>

      <section className="concept-metric-strip" aria-label="Resumo operacional">
        <ConceptMetric label={labels.operations.localCases} value={formatNumber(summaryQuery.data?.case_count, lang)} />
        <ConceptMetric label={labels.operations.totalAlerts} value={formatNumber(summaryQuery.data?.alert_count, lang)} />
        <ConceptMetric label={labels.operations.openAlerts} value={formatNumber(summaryQuery.data?.open_alert_count, lang)} tone="attention" />
        <ConceptMetric label={labels.operations.highAlerts} value={formatNumber(highAlertCount, lang)} tone="danger" />
      </section>

      <section className="concept-operations-grid">
        <div className="concept-queue-panel">
          <div className="concept-panel-header concept-split">
            <div>
              <h2>{labels.operations.queue}</h2>
              <p>{labels.concept.queueBrief}</p>
            </div>
            <div className="concept-filter-chip">
              <ConceptIcon name="filter" size={15} />
              <span>{labels.operations.filters}</span>
            </div>
          </div>
          <div className="concept-table-tools concept-operation-tools">
            <label className="concept-search">
              <ConceptIcon name="search" size={15} />
              <input
                value={searchTerm}
                placeholder={labels.concept.searchQueue}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>
            <select value={filters.alertType} onChange={(event) => updateFilter('alert_type', event.target.value)}>
              <option value="">{labels.operations.type}: {labels.common.all}</option>
              <option value="pending_lab_result">{labelAlertType('pending_lab_result', labels)}</option>
              <option value="medication_pickup_delay">{labelAlertType('medication_pickup_delay', labels)}</option>
              <option value="contact_pending_evaluation">{labelAlertType('contact_pending_evaluation', labels)}</option>
              <option value="resistance_vigilance">{labelAlertType('resistance_vigilance', labels)}</option>
            </select>
            <select value={filters.severity} onChange={(event) => updateFilter('severity', event.target.value)}>
              <option value="">{labels.common.severity}: {labels.common.all}</option>
              <option value="high">{labels.severities.high}</option>
              <option value="moderate">{labels.severities.moderate}</option>
            </select>
            <select value={filters.status} onChange={(event) => updateFilter('status', event.target.value)}>
              <option value="">{labels.common.status}: {labels.common.all}</option>
              <option value="open">{labels.statuses.open}</option>
              <option value="closed">{labels.statuses.closed}</option>
            </select>
            <select value={filters.facilityId} onChange={(event) => updateFilter('facility_id', event.target.value)}>
              <option value="">{labels.operations.facility}: {labels.common.all}</option>
              {facilityOptions.map((facilityId) => (
                <option key={facilityId} value={facilityId}>{facilityId}</option>
              ))}
            </select>
          </div>
          <div className="concept-queue-list" role="table" aria-label={labels.operations.queue}>
            <div className="concept-queue-head" role="row">
              <span>{labels.operations.type}</span>
              <span>{labels.common.severity}</span>
              <span>{labels.operations.facility}</span>
              <span>{labels.operations.team}</span>
              <span>{labels.operations.due}</span>
            </div>
            {filteredAlerts.map((alert) => (
              <AlertRow
                key={alert.alert_id}
                alert={alert}
                selected={alert.alert_id === selectedAlertId}
                lang={lang}
                onSelect={setSelectedAlertId}
              />
            ))}
            {alertsQuery.isLoading ? <p className="concept-empty-state">{labels.common.loading}</p> : null}
            {!alertsQuery.isLoading && !filteredAlerts.length ? (
              <p className="concept-empty-state">{labels.common.empty}</p>
            ) : null}
          </div>
        </div>

        <aside className="concept-alert-detail-panel">
          <div className="concept-panel-header">
            <h2>{labels.operations.alertDetail}</h2>
            <p>{labels.concept.alertDetailBrief}</p>
          </div>
          {detailQuery.data ? (
            <AlertDetail alert={detailQuery.data} lang={lang} />
          ) : (
            <p className="concept-muted">{labels.operations.selectAlert}</p>
          )}
        </aside>
      </section>

      <section className="concept-team-panel">
        <div className="concept-panel-header">
          <h2>{labels.operations.facilityTeams}</h2>
          <p>{labels.concept.teamBrief}</p>
        </div>
        <div className="concept-team-grid">
          {teamOptions.map((row) => (
            <div key={`${row.facility_id}-${row.team_id}`} className="concept-team-card">
              <ConceptIcon name="userManagement" size={18} />
              <div>
                <strong>{row.team_name}</strong>
                <span>{row.facility_id}</span>
              </div>
              <dl>
                <div><dt>{labels.operations.totalAlerts}</dt><dd>{row.alert_count}</dd></div>
                <div><dt>{labels.operations.highAlerts}</dt><dd>{row.high_count}</dd></div>
                <div><dt>{labels.operations.openAlerts}</dt><dd>{row.open_count}</dd></div>
              </dl>
            </div>
          ))}
        </div>
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
  tone?: 'neutral' | 'attention' | 'danger';
}) {
  return (
    <div className={`concept-metric concept-metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function AlertRow({
  alert,
  selected,
  lang,
  onSelect,
}: {
  alert: OperationalAlert;
  selected: boolean;
  lang: Language;
  onSelect: (alertId: string) => void;
}) {
  const labels = copy[lang];
  return (
    <button
      type="button"
      className={`concept-queue-row ${selected ? 'selected' : ''}`}
      onClick={() => onSelect(alert.alert_id)}
      role="row"
    >
      <span>{labelAlertType(alert.alert_type, labels)}</span>
      <StatusBadge value={alert.severity} kind="severity" lang={lang} />
      <span>{alert.facility_id}</span>
      <span>{alert.team_name}</span>
      <span>{formatDate(alert.due_date, lang)}</span>
    </button>
  );
}

function AlertDetail({ alert, lang }: { alert: OperationalAlert; lang: Language }) {
  const labels = copy[lang];
  return (
    <div className="concept-alert-detail">
      <div>
        <span className="concept-overline">{alert.facility_id}</span>
        <h3>{alert.team_name}</h3>
        <div className="concept-badge-row">
          <StatusBadge value={alert.severity} kind="severity" lang={lang} />
          <StatusBadge value={alert.status} lang={lang} />
        </div>
      </div>
      <section>
        <h4>{alert.local_case_id}</h4>
        <p>{alert.message}</p>
      </section>
      <div className="concept-indicator-grid concept-alert-grid">
        <div><span>{labels.operations.type}</span><strong>{labelAlertType(alert.alert_type, labels)}</strong></div>
        <div><span>{labels.common.status}</span><strong>{labelStatus(alert.status, lang)}</strong></div>
        <div><span>{labels.operations.signal}</span><strong>{alert.reference_date}</strong></div>
        <div><span>{labels.operations.due}</span><strong>{formatDate(alert.due_date, lang)}</strong></div>
      </div>
    </div>
  );
}
