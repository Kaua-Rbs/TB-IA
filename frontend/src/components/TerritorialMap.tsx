import maplibregl from 'maplibre-gl';
import { useEffect, useMemo, useRef, useState } from 'react';

import type { FeatureCollection } from '../lib/api';
import { mapBounds, withLayerValues } from '../lib/geojson';

interface TerritorialMapProps {
  payload: FeatureCollection | undefined;
  referencePayload: FeatureCollection | undefined;
  layerId: string;
  selectedId: string | null;
  referenceMode: boolean;
  visualTone?: 'current' | 'concept';
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
  '#b91c1c',
  'moderate',
  '#e2a007',
  'low',
  '#8ac6b0',
  'none',
  '#d9e7e7',
  'suppressed',
  '#edf0f4',
  'missing',
  '#cbd5df',
  '#d9e7e7'
];

const conceptMunicipalityFillColor: maplibregl.ExpressionSpecification = [
  'match',
  ['get', 'layer_bucket'],
  'high',
  '#b4232f',
  'moderate',
  '#d77a1f',
  'low',
  '#7fc6a6',
  'none',
  '#dcebea',
  'suppressed',
  '#eef2f4',
  'missing',
  '#c9d4df',
  '#dcebea'
];

type WritableGeoJsonSource = {
  setData: (data: FeatureCollection) => void;
};

export function TerritorialMap({
  payload,
  referencePayload,
  layerId,
  selectedId,
  referenceMode,
  visualTone = 'current',
  onSelect
}: TerritorialMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const onSelectRef = useRef(onSelect);
  const [isReady, setIsReady] = useState(false);
  const fitKeyRef = useRef<string>('');
  const styledPayload = useMemo(() => withLayerValues(payload, layerId), [payload, layerId]);

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
    setOrAddSource(map, 'municipalities', styledPayload);
    ensureMunicipalityLayers(map);
    map.setPaintProperty(
      'municipalities-fill',
      'fill-color',
      visualTone === 'concept' ? conceptMunicipalityFillColor : municipalityFillColor
    );
    map.setPaintProperty(
      'municipalities-line',
      'line-color',
      visualTone === 'concept' ? '#4d6472' : '#50606f'
    );
    map.setPaintProperty(
      'municipality-selected',
      'line-color',
      visualTone === 'concept' ? '#063f4f' : '#083c5f'
    );
    const bounds = mapBounds(styledPayload);
    const fitKey = `${styledPayload.metadata.geographic_scope ?? ''}-${styledPayload.metadata.year ?? ''}-${styledPayload.metadata.comparison_scope ?? ''}`;
    if (bounds && fitKeyRef.current !== fitKey) {
      map.fitBounds(bounds, { padding: 36, duration: 0 });
      fitKeyRef.current = fitKey;
    }
  }, [isReady, styledPayload, visualTone]);

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
    if (!map || !isReady || !map.getLayer('municipality-selected')) return;
    map.setFilter('municipality-selected', [
      '==',
      ['get', 'territory_id'],
      selectedId ?? '__none__'
    ]);
  }, [isReady, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) return;
    setOrAddSource(map, 'subterritories', referenceMode ? referencePayload : undefined);
    ensureSubterritoryLayers(map);
    map.setPaintProperty('subterritories-fill', 'fill-opacity', referenceMode ? 0.2 : 0);
    map.setPaintProperty('subterritories-line', 'line-opacity', referenceMode ? 0.95 : 0);
  }, [isReady, referenceMode, referencePayload]);

  return <div ref={containerRef} className="map-canvas" aria-label="Mapa territorial" />;
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
  if (!map.getLayer('municipality-selected')) {
    map.addLayer({
      id: 'municipality-selected',
      type: 'line',
      source: 'municipalities',
      filter: ['==', ['get', 'territory_id'], '__none__'],
      paint: {
        'line-color': '#083c5f',
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
