import maplibregl from 'maplibre-gl';
import { useEffect, useRef, useState } from 'react';

import type { FeatureCollection } from '../lib/api';
import {
  mapBounds,
  mapBoundsForTerritory,
  mapBucketColors
} from '../lib/geojson';

export interface MapFocusRequest {
  territoryId: string;
  requestId: number;
}

interface TerritorialMapProps {
  payload: FeatureCollection | undefined;
  referencePayload: FeatureCollection | undefined;
  selectedId: string | null;
  referenceMode: boolean;
  focusRequest: MapFocusRequest | null;
  ariaLabel: string;
  onSelect: (territoryId: string) => void;
}

const blankStyle: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: { 'background-color': '#edf4f7' }
    }
  ]
};

const municipalityFillColor: maplibregl.ExpressionSpecification = [
  'match',
  ['get', 'layer_bucket'],
  'high',
  mapBucketColors.high,
  'moderate',
  mapBucketColors.moderate,
  'low',
  mapBucketColors.low,
  'none',
  mapBucketColors.none,
  'suppressed',
  mapBucketColors.suppressed,
  'missing',
  mapBucketColors.missing,
  mapBucketColors.none
];

type WritableGeoJsonSource = {
  setData: (data: FeatureCollection) => void;
};

export function TerritorialMap({
  payload,
  referencePayload,
  selectedId,
  referenceMode,
  focusRequest,
  ariaLabel,
  onSelect
}: TerritorialMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const onSelectRef = useRef(onSelect);
  const [isReady, setIsReady] = useState(false);
  const fitKeyRef = useRef<string>('');
  const focusRequestRef = useRef<number>(0);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: blankStyle,
      attributionControl: false,
      cooperativeGestures: true
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
    map.on('load', () => setIsReady(true));
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) return;
    setOrAddSource(map, 'municipalities', payload);
    ensureMunicipalityLayers(map);
    const bounds = mapBounds(payload);
    const fitKey = `${payload?.metadata.geographic_scope ?? ''}-${payload?.metadata.year ?? ''}-${payload?.metadata.comparison_scope ?? ''}`;
    if (bounds && fitKeyRef.current !== fitKey) {
      map.fitBounds(bounds, { padding: 36, duration: 0 });
      fitKeyRef.current = fitKey;
    }
  }, [isReady, payload]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) return;
    const clickHandler = (event: maplibregl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      const territoryId = feature?.properties?.territory_id;
      if (typeof territoryId === 'string') {
        onSelectRef.current(territoryId);
      }
    };
    const enterHandler = () => {
      map.getCanvas().style.cursor = 'pointer';
    };
    const leaveHandler = () => {
      map.getCanvas().style.cursor = '';
    };
    map.on('click', 'municipalities-fill', clickHandler);
    map.on('mouseenter', 'municipalities-fill', enterHandler);
    map.on('mouseleave', 'municipalities-fill', leaveHandler);
    return () => {
      map.off('click', 'municipalities-fill', clickHandler);
      map.off('mouseenter', 'municipalities-fill', enterHandler);
      map.off('mouseleave', 'municipalities-fill', leaveHandler);
    };
  }, [isReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) return;
    const filter: maplibregl.FilterSpecification = [
      '==',
      ['get', 'territory_id'],
      selectedId ?? '__none__'
    ];
    if (map.getLayer('municipality-selected-halo')) {
      map.setFilter('municipality-selected-halo', filter);
    }
    if (map.getLayer('municipality-selected')) {
      map.setFilter('municipality-selected', filter);
    }
  }, [isReady, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (
      !map ||
      !isReady ||
      !focusRequest ||
      focusRequestRef.current === focusRequest.requestId
    ) {
      return;
    }
    const bounds = mapBoundsForTerritory(payload, focusRequest.territoryId);
    if (!bounds) return;
    focusRequestRef.current = focusRequest.requestId;
    const reduceMotion =
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    map.fitBounds(bounds, {
      padding: 56,
      maxZoom: 8,
      duration: reduceMotion ? 0 : 240
    });
  }, [focusRequest, isReady, payload]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) return;
    setOrAddSource(map, 'subterritories', referenceMode ? referencePayload : undefined);
    ensureSubterritoryLayers(map);
    map.setPaintProperty('subterritories-fill', 'fill-opacity', referenceMode ? 0.2 : 0);
    map.setPaintProperty('subterritories-line', 'line-opacity', referenceMode ? 0.95 : 0);
  }, [isReady, referenceMode, referencePayload]);

  return <div ref={containerRef} className="map-canvas" aria-label={ariaLabel} />;
}

function setOrAddSource(
  map: maplibregl.Map,
  sourceId: string,
  payload: FeatureCollection | undefined
) {
  const data = payload ?? {
    type: 'FeatureCollection',
    metadata: { feature_count: 0, drawable_geometry_count: 0 },
    features: []
  } satisfies FeatureCollection;
  const source = map.getSource(sourceId) as WritableGeoJsonSource | undefined;
  if (source) {
    source.setData(data);
    return;
  }
  map.addSource(sourceId, {
    type: 'geojson',
    data
  } as maplibregl.GeoJSONSourceSpecification);
}

function ensureMunicipalityLayers(map: maplibregl.Map) {
  if (!map.getLayer('municipalities-fill')) {
    map.addLayer({
      id: 'municipalities-fill',
      type: 'fill',
      source: 'municipalities',
      paint: {
        'fill-color': municipalityFillColor,
        'fill-opacity': 0.9
      }
    });
  }
  if (!map.getLayer('municipalities-line')) {
    map.addLayer({
      id: 'municipalities-line',
      type: 'line',
      source: 'municipalities',
      paint: {
        'line-color': '#50606f',
        'line-width': 0.7,
        'line-opacity': 0.72
      }
    });
  }
  if (!map.getLayer('municipalities-suppressed')) {
    map.addLayer({
      id: 'municipalities-suppressed',
      type: 'line',
      source: 'municipalities',
      filter: ['==', ['get', 'layer_bucket'], 'suppressed'],
      paint: {
        'line-color': '#837967',
        'line-width': 1.4,
        'line-dasharray': [2, 1.5],
        'line-opacity': 1
      }
    });
  }
  if (!map.getLayer('municipalities-missing')) {
    map.addLayer({
      id: 'municipalities-missing',
      type: 'line',
      source: 'municipalities',
      filter: ['==', ['get', 'layer_bucket'], 'missing'],
      paint: {
        'line-color': '#6f7d8b',
        'line-width': 1.4,
        'line-opacity': 1
      }
    });
  }
  if (!map.getLayer('municipality-selected-halo')) {
    map.addLayer({
      id: 'municipality-selected-halo',
      type: 'line',
      source: 'municipalities',
      filter: ['==', ['get', 'territory_id'], '__none__'],
      paint: {
        'line-color': '#ffffff',
        'line-width': 6.4,
        'line-opacity': 0.96
      }
    });
  }
  if (!map.getLayer('municipality-selected')) {
    map.addLayer({
      id: 'municipality-selected',
      type: 'line',
      source: 'municipalities',
      filter: ['==', ['get', 'territory_id'], '__none__'],
      paint: {
        'line-color': '#073c42',
        'line-width': 3.2,
        'line-opacity': 1
      }
    });
  }
}

function ensureSubterritoryLayers(map: maplibregl.Map) {
  if (!map.getLayer('subterritories-fill')) {
    map.addLayer({
      id: 'subterritories-fill',
      type: 'fill',
      source: 'subterritories',
      paint: {
        'fill-color': '#ffffff',
        'fill-opacity': 0,
        'fill-outline-color': '#24566b'
      }
    });
  }
  if (!map.getLayer('subterritories-line')) {
    map.addLayer({
      id: 'subterritories-line',
      type: 'line',
      source: 'subterritories',
      paint: {
        'line-color': '#24566b',
        'line-width': 1.7,
        'line-dasharray': [2, 2],
        'line-opacity': 0
      }
    });
  }
}
