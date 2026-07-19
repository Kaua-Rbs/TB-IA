import {
  formatMapLayerRange,
  labelMapUnit
} from '../lib/format';
import {
  mapBucketColors,
  type MapLayerBucket,
  type MapLayerPresentation
} from '../lib/geojson';
import { copy, type Language } from '../lib/i18n';

interface MapLegendProps {
  presentation: MapLayerPresentation;
  lang: Language;
  selectedId: string | null;
  referenceMode: boolean;
  referenceCount: number;
}

const availabilityBuckets: MapLayerBucket[] = ['suppressed', 'missing'];

export function MapLegend({
  presentation,
  lang,
  selectedId,
  referenceMode,
  referenceCount
}: MapLegendProps) {
  const labels = copy[lang].territorial.mapLegend;
  const attentionEntries = presentation.entries.filter(
    (entry) => !availabilityBuckets.includes(entry.bucket)
  );
  const availabilityEntries = presentation.entries.filter((entry) =>
    availabilityBuckets.includes(entry.bucket)
  );
  const bucketLabels: Record<MapLayerBucket, string> = {
    high: labels.high,
    moderate: labels.moderate,
    low: labels.low,
    none: labels.none,
    suppressed: labels.suppressed,
    missing: labels.missing
  };

  return (
    <section className="map-legend" aria-label={labels.title}>
      <header className="map-legend-header">
        <div>
          <span>{labels.title}</span>
          <strong>{presentation.layer.label}</strong>
        </div>
        <small>
          {labels.unit}: {labelMapUnit(presentation.layer.unit, lang)}
        </small>
      </header>

      <p className="map-legend-note">
        {presentation.method === 'severity'
          ? labels.severityNote
          : labels.relativeNote}
      </p>

      {attentionEntries.length ? (
        <ul className="map-legend-list">
          {attentionEntries.map((entry) => (
            <li key={entry.bucket}>
              <span
                className={`map-legend-swatch ${entry.bucket}`}
                style={{ backgroundColor: mapBucketColors[entry.bucket] }}
                aria-hidden="true"
              />
              <span>{bucketLabels[entry.bucket]}</span>
              <span className="map-legend-values">
                <strong>
                  {formatMapLayerRange(
                    entry.min,
                    entry.max,
                    presentation.layer.unit,
                    lang
                  )}
                </strong>
                <small>{municipalityCount(entry.count, lang)}</small>
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="map-legend-section-label">{labels.availability}</div>
      <ul className="map-legend-list availability">
        {availabilityEntries.map((entry) => (
          <li key={entry.bucket}>
            <span
              className={`map-legend-swatch ${entry.bucket}`}
                style={{ backgroundColor: mapBucketColors[entry.bucket] }}
              aria-hidden="true"
            />
            <span>{bucketLabels[entry.bucket]}</span>
            <span className="map-legend-values">
              <small>{municipalityCount(entry.count, lang)}</small>
            </span>
          </li>
        ))}
      </ul>

      {selectedId || referenceMode ? (
        <ul className="map-legend-overlays">
          {selectedId ? (
            <li>
              <span className="map-legend-key selected" aria-hidden="true" />
              <span>{labels.selected}</span>
            </li>
          ) : null}
          {referenceMode ? (
            <li>
              <span className="map-legend-key reference" aria-hidden="true" />
              <span>{labels.reference}</span>
              <small>{referenceTerritoryCount(referenceCount, lang)}</small>
            </li>
          ) : null}
        </ul>
      ) : null}
    </section>
  );
}

function municipalityCount(count: number, lang: Language) {
  const labels = copy[lang].territorial.mapLegend;
  const noun =
    count === 1 ? labels.municipalitySingular : labels.municipalityPlural;
  return `${count} ${noun}`;
}

function referenceTerritoryCount(count: number, lang: Language) {
  const labels = copy[lang].territorial.mapLegend;
  const noun =
    count === 1 ? labels.referenceSingular : labels.referencePlural;
  return `${count} ${noun}`;
}
