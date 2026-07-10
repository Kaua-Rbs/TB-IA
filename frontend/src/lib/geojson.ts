import type { FeatureCollection, GeoFeature, MapLayerDefinition, MunicipalityProperties } from './api';

type Bounds = [[number, number], [number, number]];

const emptyCollection: FeatureCollection = {
  type: 'FeatureCollection',
  metadata: { feature_count: 0, drawable_geometry_count: 0 },
  features: []
};

export function withLayerValues(payload: FeatureCollection | undefined, layerId: string) {
  if (!payload) return emptyCollection;
  const values = payload.features
    .map((feature) => rawLayerValue(feature, layerId))
    .filter((value): value is number => Number.isFinite(value));
  const sortedValues = [...values].sort((a, b) => a - b);
  const direction = payload.metadata.layers?.[layerId]?.direction;

  return {
    ...payload,
    features: payload.features.map((feature) => {
      const value = rawLayerValue(feature, layerId);
      const bucket = layerBucket(feature, layerId, value, sortedValues, direction);
      return {
        ...feature,
        properties: {
          ...feature.properties,
          layer_value: value,
          layer_bucket: bucket
        }
      };
    })
  } satisfies FeatureCollection;
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

export function layerLabel(layer: MapLayerDefinition | undefined, fallback: string) {
  return layer?.label ?? fallback;
}

function rawLayerValue(feature: GeoFeature, layerId: string) {
  const properties = feature.properties;
  if (layerId === 'priority_score') return properties.priority_score;
  if (layerId === 'scenario_count') return properties.scenario_count;
  const indicator = properties.indicators[layerId];
  if (!indicator || indicator.is_suppressed) return null;
  return indicator.value;
}

function layerBucket(
  feature: GeoFeature<MunicipalityProperties>,
  layerId: string,
  value: number | null,
  sortedValues: number[],
  direction: string | null | undefined
) {
  if (layerId === 'priority_score') {
    return feature.properties.top_severity ?? 'none';
  }
  if (value === null || value === undefined) {
    return feature.properties.data_status === 'partial' ? 'suppressed' : 'missing';
  }
  if (sortedValues.length < 3) {
    return value > 0 ? 'moderate' : 'none';
  }
  const rank = percentileRank(value, sortedValues);
  const attention = direction === 'low_bad' ? 1 - rank : rank;
  if (attention >= 0.67) return 'high';
  if (attention >= 0.34) return 'moderate';
  return 'low';
}

function percentileRank(value: number, sortedValues: number[]) {
  if (sortedValues.length <= 1) return 1;
  const index = sortedValues.findIndex((candidate) => candidate >= value);
  const boundedIndex = index === -1 ? sortedValues.length - 1 : index;
  return boundedIndex / (sortedValues.length - 1);
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
