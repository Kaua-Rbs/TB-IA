import { useQuery } from '@tanstack/react-query';
import { AlertCircle, ClipboardList, Filter } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import {
  fetchOperationAlert,
  fetchOperationAlerts,
  fetchOperationsSummary,
  type OperationalAlert
} from '../lib/api';
import { formatDate, formatNumber, labelAlertType, labelStatus } from '../lib/format';
import { copy, normalizeLanguage } from '../lib/i18n';

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
  const highAlertCount = summaryQuery.data?.by_severity.find((row) => row.severity === 'high')?.count ?? 0;
  const facilityOptions = useMemo(
    () => [...new Set(summaryQuery.data?.by_facility_team.map((row) => row.facility_id) ?? [])],
    [summaryQuery.data]
  );
  const teamOptions = useMemo(
    () => summaryQuery.data?.by_facility_team ?? [],
    [summaryQuery.data]
  );

  useEffect(() => {
    if (!alertsQuery.data?.length) {
      setSelectedAlertId(null);
      return;
    }
    if (!selectedAlertId || !alertsQuery.data.some((alert) => alert.alert_id === selectedAlertId)) {
      setSelectedAlertId(alertsQuery.data[0].alert_id);
    }
  }, [alertsQuery.data, selectedAlertId]);

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
    <div className="page-stack">
      <header className="page-hero compact-hero operations-hero">
        <div>
          <div className="badge-row">
            <span className="product-badge synthetic">{labels.operations.syntheticBadge}</span>
            <span className="scope-badge">{year}</span>
          </div>
          <h1>{labels.operations.title}</h1>
          <p>{labels.operations.subtitle}</p>
        </div>
        <form className="command-bar" aria-label={labels.operations.filters}>
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

      <section className="caveat-band synthetic-band">
        <AlertCircle size={18} aria-hidden="true" />
        <span>{labels.operations.caveat}</span>
      </section>

      <section className="metric-strip" aria-label="Resumo operacional">
        <MetricCard label={labels.operations.localCases} value={formatNumber(summaryQuery.data?.case_count, lang)} />
        <MetricCard label={labels.operations.totalAlerts} value={formatNumber(summaryQuery.data?.alert_count, lang)} />
        <MetricCard label={labels.operations.openAlerts} value={formatNumber(summaryQuery.data?.open_alert_count, lang)} />
        <MetricCard label={labels.operations.highAlerts} value={formatNumber(highAlertCount, lang)} tone="danger" />
      </section>

      <section className="operations-layout">
        <div className="queue-panel">
          <div className="panel-heading split-heading">
            <div>
              <h2>{labels.operations.queue}</h2>
              <p>{labels.operations.subtitle}</p>
            </div>
            <div className="table-tools operations-filters">
              <Filter size={16} aria-hidden="true" />
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
                    lang={lang}
                    onSelect={setSelectedAlertId}
                  />
                ))}
              </tbody>
            </table>
            {alertsQuery.isLoading ? <p className="empty-state">{labels.common.loading}</p> : null}
            {!alertsQuery.isLoading && !alertsQuery.data?.length ? (
              <p className="empty-state">{labels.common.empty}</p>
            ) : null}
          </div>
        </div>

        <aside className="detail-panel operations-detail">
          <h2>{labels.operations.alertDetail}</h2>
          {!selectedAlertId ? <p className="muted-copy">{labels.operations.selectAlert}</p> : null}
          {detailQuery.data ? <AlertDetail alert={detailQuery.data} lang={lang} /> : null}
        </aside>
      </section>

      <section className="facility-panel">
        <div className="panel-heading">
          <h2>{labels.operations.facilityTeams}</h2>
        </div>
        <div className="facility-grid">
          {teamOptions.map((row) => (
            <div key={`${row.facility_id}-${row.team_id}`} className="facility-card">
              <ClipboardList size={18} aria-hidden="true" />
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

function AlertRow({
  alert,
  selected,
  lang,
  onSelect
}: {
  alert: OperationalAlert;
  selected: boolean;
  lang: ReturnType<typeof normalizeLanguage>;
  onSelect: (alertId: string) => void;
}) {
  const labels = copy[lang];
  function selectWithKeyboard(event: React.KeyboardEvent<HTMLTableRowElement>) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    onSelect(alert.alert_id);
  }

  return (
    <tr
      className={selected ? 'selected-row' : ''}
      onClick={() => onSelect(alert.alert_id)}
      onKeyDown={selectWithKeyboard}
      tabIndex={0}
      aria-selected={selected}
    >
      <td data-label={labels.operations.type}>{labelAlertType(alert.alert_type, labels)}</td>
      <td data-label={labels.common.severity}><StatusBadge value={alert.severity} kind="severity" lang={lang} /></td>
      <td data-label={labels.common.status}><StatusBadge value={alert.status} lang={lang} /></td>
      <td data-label={labels.operations.facility}>{alert.facility_id}</td>
      <td data-label={labels.operations.team}>{alert.team_name}</td>
      <td data-label={labels.operations.due}>{formatDate(alert.due_date, lang)}</td>
    </tr>
  );
}

function AlertDetail({
  alert,
  lang
}: {
  alert: OperationalAlert;
  lang: ReturnType<typeof normalizeLanguage>;
}) {
  const labels = copy[lang];
  return (
    <div className="detail-stack">
      <div>
        <span className="eyebrow">{alert.facility_id}</span>
        <h3>{alert.team_name}</h3>
      </div>
      <div className="detail-section">
        <h4>{alert.local_case_id}</h4>
        <p>{alert.message}</p>
      </div>
      <div className="indicator-list">
        <div><span>{labels.operations.type}</span><strong>{labelAlertType(alert.alert_type, labels)}</strong></div>
        <div><span>{labels.common.status}</span><strong>{labelStatus(alert.status, lang)}</strong></div>
        <div><span>{labels.operations.reference}</span><strong>{formatDate(alert.reference_date, lang)}</strong></div>
        <div><span>{labels.operations.due}</span><strong>{formatDate(alert.due_date, lang)}</strong></div>
      </div>
    </div>
  );
}
