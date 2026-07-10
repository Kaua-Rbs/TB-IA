import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

class MockMap {
  loaded() {
    return true;
  }

  on(_event: string, layerOrHandler?: unknown, handler?: unknown) {
    if (typeof layerOrHandler === 'function') {
      layerOrHandler();
    }
    if (typeof handler === 'function' && _event === 'load') {
      handler();
    }
    return this;
  }

  off() {
    return this;
  }

  addControl() {
    return this;
  }

  addSource() {
    return this;
  }

  getSource() {
    return { setData: vi.fn() };
  }

  addLayer() {
    return this;
  }

  getLayer() {
    return true;
  }

  setPaintProperty() {
    return this;
  }

  setFilter() {
    return this;
  }

  fitBounds() {
    return this;
  }

  remove() {
    return this;
  }

  getCanvas() {
    return { style: {} };
  }
}

class MockNavigationControl {}

vi.mock('maplibre-gl', () => ({
  default: {
    Map: MockMap,
    NavigationControl: MockNavigationControl
  },
  Map: MockMap,
  NavigationControl: MockNavigationControl
}));
