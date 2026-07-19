import { describe, expect, it } from 'vitest';

import type {
  FeatureCollection,
  GeoFeature,
  MunicipalityProperties
} from './api';
import {
  buildMapLayerPresentation,
  mapBoundsForTerritory,
  type MapLayerBucket
} from './geojson';

describe('buildMapLayerPresentation', () => {
  it('uses scenario severity for priority while preserving explicit missing data', () => {
    const payload = collection('priority_score', 'high_bad', [
      feature('a', {
        priority_score: 8,
        top_severity: 'high',
        data_status: 'complete'
      }),
      feature('b', {
        priority_score: 4,
        top_severity: 'low',
        data_status: 'partial'
      }),
      feature('c', {
        priority_score: 2,
        top_severity: 'moderate',
        data_status: 'missing'
      })
    ]);

    const presentation = buildMapLayerPresentation(payload, 'priority_score');

    expect(buckets(presentation.payload)).toEqual(['high', 'low', 'missing']);
    expect(presentation.method).toBe('severity');
    expect(presentation.entries).toEqual([
      { bucket: 'high', count: 1, min: 8, max: 8 },
      { bucket: 'low', count: 1, min: 4, max: 4 },
      { bucket: 'suppressed', count: 0, min: null, max: null },
      { bucket: 'missing', count: 1, min: null, max: null }
    ]);
  });

  it('classifies indicator availability independently from municipality readiness', () => {
    const payload = collection('indicator', 'high_bad', [
      feature('a', {
        data_status: 'partial',
        indicators: { indicator: indicator(10) }
      }),
      feature('b', {
        indicators: { indicator: indicator(null, true) }
      }),
      feature('c'),
      feature('d', {
        indicators: { indicator: indicator(20) }
      }),
      feature('e', {
        indicators: { indicator: indicator(30) }
      })
    ]);

    const presentation = buildMapLayerPresentation(payload, 'indicator');

    expect(buckets(presentation.payload)).toEqual([
      'low',
      'suppressed',
      'missing',
      'moderate',
      'high'
    ]);
    expect(presentation.entries).toEqual([
      { bucket: 'high', count: 1, min: 30, max: 30 },
      { bucket: 'moderate', count: 1, min: 20, max: 20 },
      { bucket: 'low', count: 1, min: 10, max: 10 },
      { bucket: 'suppressed', count: 1, min: null, max: null },
      { bucket: 'missing', count: 1, min: null, max: null }
    ]);
  });

  it('uses average ranks for ties and a moderate bucket for one observed value', () => {
    const tied = collection('indicator', 'high_bad', [
      feature('a', { indicators: { indicator: indicator(10) } }),
      feature('b', { indicators: { indicator: indicator(10) } }),
      feature('c', { indicators: { indicator: indicator(30) } })
    ]);
    const single = collection('indicator', 'high_bad', [
      feature('only', { indicators: { indicator: indicator(12) } })
    ]);

    expect(buckets(buildMapLayerPresentation(tied, 'indicator').payload)).toEqual([
      'low',
      'low',
      'high'
    ]);
    expect(buckets(buildMapLayerPresentation(single, 'indicator').payload)).toEqual([
      'moderate'
    ]);
  });

  it('inverts low-bad layers and keeps zero scenarios in the no-signal bucket', () => {
    const lowBad = collection('indicator', 'low_bad', [
      feature('a', { indicators: { indicator: indicator(10) } }),
      feature('b', { indicators: { indicator: indicator(20) } }),
      feature('c', { indicators: { indicator: indicator(30) } })
    ]);
    const scenarios = collection('scenario_count', 'high_bad', [
      feature('a', { scenario_count: 0 }),
      feature('b', { scenario_count: 1 }),
      feature('c', { scenario_count: 2 })
    ]);

    expect(buckets(buildMapLayerPresentation(lowBad, 'indicator').payload)).toEqual([
      'high',
      'moderate',
      'low'
    ]);
    expect(
      buckets(buildMapLayerPresentation(scenarios, 'scenario_count').payload)
    ).toEqual(['none', 'low', 'high']);
  });

  it('counts only drawable geometries in the visible legend', () => {
    const payload = collection('indicator', 'high_bad', [
      feature('a', { indicators: { indicator: indicator(10) } }),
      {
        ...feature('b'),
        geometry: null
      }
    ]);

    const presentation = buildMapLayerPresentation(payload, 'indicator');

    expect(presentation.drawableCount).toBe(1);
    expect(
      presentation.entries.find((entry) => entry.bucket === 'missing')?.count
    ).toBe(0);
  });
});

describe('mapBoundsForTerritory', () => {
  it('returns only the selected geometry bounds and ignores unknown ids', () => {
    const payload = collection('priority_score', 'high_bad', [
      feature('a'),
      {
        ...feature('b'),
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [-4, -3],
              [-1, -3],
              [-1, 2],
              [-4, -3]
            ]
          ]
        }
      }
    ]);

    expect(mapBoundsForTerritory(payload, 'b')).toEqual([
      [-4, -3],
      [-1, 2]
    ]);
    expect(mapBoundsForTerritory(payload, 'unknown')).toBeNull();
  });
});

function collection(
  layerId: string,
  direction: string,
  features: Array<GeoFeature<MunicipalityProperties>>
): FeatureCollection {
  return {
    type: 'FeatureCollection',
    metadata: {
      feature_count: features.length,
      drawable_geometry_count: features.filter((item) => item.geometry).length,
      layers: {
        [layerId]: {
          label: layerId,
          kind: layerId === 'indicator' ? 'indicator' : 'property',
          unit: layerId === 'indicator' ? 'percent' : 'count',
          direction
        }
      }
    },
    features
  };
}

function feature(
  territoryId: string,
  overrides: Partial<MunicipalityProperties> = {}
): GeoFeature<MunicipalityProperties> {
  return {
    type: 'Feature',
    properties: {
      territory_id: territoryId,
      name: territoryId,
      uf: 'CE',
      priority_score: 0,
      scenario_count: 0,
      top_severity: null,
      top_explanations: [],
      top_scenarios: [],
      data_status: 'complete',
      indicators: {},
      ...overrides
    },
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [0, 0],
          [1, 0],
          [1, 1],
          [0, 0]
        ]
      ]
    }
  };
}

function indicator(value: number | null, isSuppressed = false) {
  return {
    name: 'Indicator',
    value,
    is_suppressed: isSuppressed,
    unit: 'percent',
    direction: 'high_bad'
  };
}

function buckets(payload: FeatureCollection): MapLayerBucket[] {
  return payload.features.map(
    (item) => item.properties.layer_bucket as MapLayerBucket
  );
}
