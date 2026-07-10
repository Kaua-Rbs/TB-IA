import { labelSeverity, labelStatus } from '../lib/format';
import type { Language } from '../lib/i18n';

interface StatusBadgeProps {
  value: string | null | undefined;
  kind?: 'status' | 'severity' | 'plain';
  lang: Language;
}

export function StatusBadge({ value, kind = 'status', lang }: StatusBadgeProps) {
  const normalized = value ?? 'none';
  const label = kind === 'severity' ? labelSeverity(value, lang) : labelStatus(value, lang);
  return <span className={`status-badge ${kind}-${normalized}`}>{label}</span>;
}
