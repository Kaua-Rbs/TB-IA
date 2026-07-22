import { Database, ShieldAlert } from "lucide-react";

import type {
  ResistanceSurveillanceProfile as ResistanceProfile,
  ResistanceSurveillanceSignal,
} from "../lib/api";
import { formatIndicatorValue, formatNumber } from "../lib/format";
import { copy, type Language } from "../lib/i18n";

interface ResistanceSurveillanceProfileProps {
  profile: ResistanceProfile | null | undefined;
  lang: Language;
}

export function ResistanceSurveillanceProfile({
  profile,
  lang,
}: ResistanceSurveillanceProfileProps) {
  if (!profile) return null;
  const labels = copy[lang].territorial.resistance;

  return (
    <section
      className="detail-section resistance-profile"
      aria-labelledby="resistance-profile-title"
    >
      <div className="resistance-profile-heading">
        <h4 id="resistance-profile-title">{labels.title}</h4>
        <ShieldAlert size={15} aria-hidden="true" />
      </div>
      <p className="resistance-boundary">
        {profile.interpretation_label ?? labels.title}
      </p>
      <dl className="resistance-guardrails">
        <div>
          <dt>{labels.confirmedStatus}</dt>
          <dd>{profile.confirmed_resistance_status_label ?? "-"}</dd>
        </div>
        <div>
          <dt>{labels.rankingEffect}</dt>
          <dd>{profile.ranking_effect_label ?? "-"}</dd>
        </div>
        <div>
          <dt>{labels.reviewStatus}</dt>
          <dd>{profile.review_status_label ?? "-"}</dd>
        </div>
      </dl>

      <div className="resistance-signal-heading">
        <Database size={14} aria-hidden="true" />
        <span>{labels.publicSignals}</span>
      </div>
      <ul className="resistance-signal-list">
        {profile.signals.map((signal) => (
          <ResistanceSignalRow
            key={signal.signal_id}
            signal={signal}
            lang={lang}
          />
        ))}
      </ul>
    </section>
  );
}

function ResistanceSignalRow({
  signal,
  lang,
}: {
  signal: ResistanceSurveillanceSignal;
  lang: Language;
}) {
  const labels = copy[lang].territorial.resistance;
  const basis =
    signal.numerator_value !== null && signal.denominator_value !== null
      ? `${formatNumber(signal.numerator_value, lang)} / ${formatNumber(
          signal.denominator_value,
          lang,
        )}`
      : "-";

  return (
    <li
      className={
        `resistance-signal resistance-data-${signal.data_status} resistance-trigger-${signal.trigger_status}`
      }
    >
      <div className="resistance-signal-title">
        <span className="resistance-status-marker" aria-hidden="true" />
        <strong>{signal.label}</strong>
        <span>{signal.data_status_label ?? "-"}</span>
      </div>
      <small className="resistance-trigger-status">
        {signal.trigger_status_label ?? signal.evaluation_status_label ?? "-"}
      </small>
      <dl className="resistance-signal-metrics">
        <div>
          <dt>{labels.signalValue}</dt>
          <dd>{formatIndicatorValue(signal.value, signal.unit, lang)}</dd>
        </div>
        <div>
          <dt>{labels.signalBasis}</dt>
          <dd>{basis}</dd>
        </div>
        <div>
          <dt>{labels.signalThreshold}</dt>
          <dd>
            {formatIndicatorValue(signal.threshold_value, signal.unit, lang)}
          </dd>
        </div>
      </dl>
      <small className="resistance-source">
        <span>{labels.source}</span>
        {sourceSummary(signal, labels.noSource)}
      </small>
      {signal.caveats ? (
        <small className="resistance-signal-caveat">{signal.caveats}</small>
      ) : null}
    </li>
  );
}

function sourceSummary(
  signal: ResistanceSurveillanceSignal,
  fallback: string,
) {
  if (!signal.source_provenance.length) return fallback;
  return signal.source_provenance
    .map((source) => {
      const name = source.source_label ?? source.source_id;
      return source.reference_year ? `${name} · ${source.reference_year}` : name;
    })
    .join("; ");
}
