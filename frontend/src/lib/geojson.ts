import type {
  FeatureCollection,
  GeoFeature,
  MapLayerDefinition,
  MunicipalityProperties
} from './api';

type Bounds = [[number, number], [number, number]];

const emptyCollection: FeatureCollection = {
  type: 'FeatureCollection',
  metadata: { feature_count: 0, drawable_geometry_count: 0 },
  features: []
};

export type MapLayerBucket =
  | 'high'
  | 'moderate'
  | 'low'
  | 'none'
  | 'suppressed'
  | 'missing';

export interface MapLegendEntry {
  bucket: MapLayerBucket;
  count: number;
  min: number | null;
  max: number | null;
}

export interface MapLayerPresentation {
  payload: FeatureCollection;
  layer: MapLayerDefinition & { id: string };
  method: 'severity' | 'relative';
  entries: MapLegendEntry[];
  drawableCount: number;
}

type LayerObservation = {
  state: 'available' | 'suppressed' | 'missing';
  value: number | null;
};

const attentionBuckets: MapLayerBucket[] = ['high', 'moderate', 'low', 'none'];
const availabilityBuckets: MapLayerBucket[] = ['suppressed', 'missing'];

export const mapBucketColors: Record<MapLayerBucket, string> = {
  high: '#b91c1c',
  moderate: '#e2a007',
  low: '#79b7a4',
  none: '#d9e7e7',
  suppressed: '#f1eee5',
  missing: '#cbd5df'
};

export function buildMapLayerPresentation(
  payload: FeatureCollection | undefined,
  layerId: string
): MapLayerPresentation {
  const layerDefinition = payload?.metadata.layers?.[layerId];
  const layer = {
    id: layerId,
    label: layerDefinition?.label ?? layerId,
    kind: layerDefinition?.kind ?? 'unknown',
    unit: layerDefinition?.unit ?? null,
    direction: layerDefinition?.direction ?? null
  };
  const method = layerId === 'priority_score' ? 'severity' : 'relative';
  if (!payload) {
    return {
      payload: emptyCollection,
      layer,
      method,
      entries: availabilityBuckets.map((bucket) => ({
        bucket,
        count: 0,
        min: null,
        max: null
      })),
      drawableCount: 0
    };
  }

  const observations = payload.features.map((feature) =>
    layerObservation(feature, layerId)
  );
  const sortedValues = observations
    .filter(
      (observation) =>
        observation.state === 'available' && finiteNumber(observation.value)
    )
    .map((observation) => observation.value)
    .filter((value): value is number => finiteNumber(value))
    .filter((value) => layerId !== 'scenario_count' || value > 0)
    .sort((a, b) => a - b);

  const styledPayload = {
    ...payload,
    features: payload.features.map((feature, index) => {
      const observation = observations[index];
      const bucket = observationBucket(
        feature,
        layerId,
        observation,
        sortedValues,
        layer.direction
      );
      return {
        ...feature,
        properties: {
          ...feature.properties,
          layer_value: observation.value,
          layer_bucket: bucket
        }
      };
    })
  } satisfies FeatureCollection;

  const drawableFeatures = styledPayload.features.filter(
    (feature) => feature.geometry !== null
  );
  const entries = attentionBuckets.flatMap((bucket) => {
    const values = drawableFeatures
      .filter((feature) => feature.properties.layer_bucket === bucket)
      .map((feature) => feature.properties.layer_value)
      .filter((value): value is number => finiteNumber(value));
    if (!values.length) return [];
    return [legendEntry(bucket, values)];
  });
  entries.push(
    ...availabilityBuckets.map((bucket) => ({
      bucket,
      count: drawableFeatures.filter(
        (feature) => feature.properties.layer_bucket === bucket
      ).length,
      min: null,
      max: null
    }))
  );

  return {
    payload: styledPayload,
    layer,
    method,
    entries,
    drawableCount: drawableFeatures.length
  };
}

export function layerOptions(payload: FeatureCollection | undefined) {
  const layers = payload?.metadata.layers ?? {};
  return Object.entries(layers).map(([id, layer]) => ({ id, ...layer }));
}

export function mapBounds(payload: FeatureCollection | undefined): Bounds | null {
  if (!payload) return null;
  const bounds = {
    minLng: Number.POSITIVE_INFINITY,
    minLat: Number.POSITIVE_INFINITY,
    maxLng: Number.NEGATIVE_INFINITY,
    maxLat: Number.NEGATIVE_INFINITY
  };
  for (const feature of payload.features) {
    visitCoordinates(feature.geometry?.coordinates, (lng, lat) => {
      bounds.minLng = Math.min(bounds.minLng, lng);
      bounds.minLat = Math.min(bounds.minLat, lat);
      bounds.maxLng = Math.max(bounds.maxLng, lng);
      bounds.maxLat = Math.max(bounds.maxLat, lat);
    });
  }
  if (!Number.isFinite(bounds.minLng)) return null;
  return [
    [bounds.minLng, bounds.minLat],
    [bounds.maxLng, bounds.maxLat]
  ];
}

export function mapBoundsForTerritory(
  payload: FeatureCollection | undefined,
  territoryId: string
): Bounds | null {
  if (!payload) return null;
  const feature = payload.features.find(
    (candidate) => candidate.properties.territory_id === territoryId
  );
  if (!feature) return null;
  return mapBounds({ ...payload, features: [feature] });
}

export function layerLabel(layer: MapLayerDefinition | undefined, fallback: string) {
  return layer?.label ?? fallback;
}

function layerObservation(feature: GeoFeature, layerId: string): LayerObservation {
  const properties = feature.properties;
  if (layerId === 'priority_score' || layerId === 'scenario_count') {
    const value =
      layerId === 'priority_score'
        ? properties.priority_score
        : properties.scenario_count;
    return properties.data_status === 'missing' || !finiteNumber(value)
      ? { state: 'missing', value: null }
      : { state: 'available', value };
  }

  const indicator = properties.indicators[layerId];
  if (indicator?.is_suppressed) {
    return { state: 'suppressed', value: null };
  }
  if (!indicator || !finiteNumber(indicator.value)) {
    return { state: 'missing', value: null };
  }
  return { state: 'available', value: indicator.value };
}

function observationBucket(
  feature: GeoFeature<MunicipalityProperties>,
  layerId: string,
  observation: LayerObservation,
  sortedValues: number[],
  direction: string | null | undefined
): MapLayerBucket {
  if (observation.state !== 'available') return observation.state;
  if (layerId === 'priority_score') {
    const severity = feature.properties.top_severity;
    return severity && attentionBuckets.includes(severity as MapLayerBucket)
      ? (severity as MapLayerBucket)
      : 'none';
  }

  const value = observation.value;
  if (!finiteNumber(value)) return 'missing';
  if (layerId === 'scenario_count' && value === 0) return 'none';
  const rank = percentileRank(value, sortedValues);
  const attention = direction === 'low_bad' ? 1 - rank : rank;
  if (attention >= 0.67) return 'high';
  if (attention >= 0.34) return 'moderate';
  return 'low';
}

function percentileRank(value: number, sortedValues: number[]) {
  if (sortedValues.length <= 1) return 0.5;
  const firstIndex = sortedValues.findIndex((candidate) => candidate === value);
  if (firstIndex === -1) return 0.5;
  let lastIndex = firstIndex;
  while (sortedValues[lastIndex + 1] === value) lastIndex += 1;
  return (firstIndex + lastIndex) / 2 / (sortedValues.length - 1);
}

function legendEntry(bucket: MapLayerBucket, values: number[]): MapLegendEntry {
  return {
    bucket,
    count: values.length,
    min: Math.min(...values),
    max: Math.max(...values)
  };
}

function finiteNumber(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function visitCoordinates(value: unknown, visitor: (lng: number, lat: number) => void) {
  if (!Array.isArray(value)) return;
  if (typeof value[0] === 'number' && typeof value[1] === 'number') {
    visitor(value[0], value[1]);
    return;
  }
  for (const child of value) {
    visitCoordinates(child, visitor);
  }
}
