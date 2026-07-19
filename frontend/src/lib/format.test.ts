import { describe, expect, it } from 'vitest';

import {
  formatIndicatorValue,
  formatMapLayerRange,
  labelMapUnit
} from './format';

describe('map and indicator formatting', () => {
  it('treats percent API values as values on a zero-to-one-hundred scale', () => {
    expect(formatIndicatorValue(77.27, 'percent', 'pt')).toBe('77,3%');
    expect(formatMapLayerRange(12.5, 77.27, 'percent', 'en')).toBe(
      '12.5% - 77.3%'
    );
  });

  it('keeps proportion compatibility for zero-to-one values', () => {
    expect(formatIndicatorValue(0.75, 'proportion', 'en')).toBe('75.0%');
  });

  it('localizes per-100k values and unit names', () => {
    expect(formatMapLayerRange(40, 40, 'per_100k', 'pt')).toBe('40,0/100 mil');
    expect(labelMapUnit('per_100k', 'en')).toBe('per 100k');
  });
});
