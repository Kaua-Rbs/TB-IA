import { copy, type AppCopy, type Language } from './i18n';

export function formatNumber(value: number | null | undefined, lang: Language, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '-';
  }
  return new Intl.NumberFormat(lang === 'pt' ? 'pt-BR' : 'en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(value);
}

export function formatIndicatorValue(
  value: number | null | undefined,
  unit: string | null | undefined,
  lang: Language
) {
  if (value === null || value === undefined) {
    return '-';
  }
  if (unit === 'proportion') {
    return `${formatNumber(value * 100, lang, 1)}%`;
  }
  if (unit === 'per_100k') {
    return `${formatNumber(value, lang, 1)}/100 mil`;
  }
  return formatNumber(value, lang, 1);
}

export function labelStatus(status: string | null | undefined, lang: Language) {
  if (!status) return '-';
  const labels = copy[lang].statuses as Record<string, string>;
  return labels[status] ?? status;
}

export function labelSeverity(severity: string | null | undefined, lang: Language) {
  if (!severity) return copy[lang].severities.none;
  const labels = copy[lang].severities as Record<string, string>;
  return labels[severity] ?? severity;
}

export function labelAlertType(alertType: string | null | undefined, labels: AppCopy) {
  if (!alertType) return '-';
  const alertLabels = labels.alertTypes as Record<string, string>;
  return alertLabels[alertType] ?? alertType;
}

export function formatDate(value: string | null | undefined, lang: Language) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(lang === 'pt' ? 'pt-BR' : 'en-US').format(date);
}
