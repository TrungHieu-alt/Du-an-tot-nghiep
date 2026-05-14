import '@testing-library/jest-dom/vitest';

const createMemoryStorage = (): Storage => {
  let values: Record<string, string> = {};
  return {
    get length() {
      return Object.keys(values).length;
    },
    clear() {
      values = {};
    },
    getItem(key: string) {
      return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null;
    },
    key(index: number) {
      return Object.keys(values)[index] ?? null;
    },
    removeItem(key: string) {
      delete values[key];
    },
    setItem(key: string, value: string) {
      values[key] = String(value);
    },
  };
};

try {
  if (typeof window !== 'undefined' && typeof window.localStorage?.getItem !== 'function') {
    Object.defineProperty(window, 'localStorage', {
      value: createMemoryStorage(),
      configurable: true,
    });
  }
} catch {
  Object.defineProperty(window, 'localStorage', {
    value: createMemoryStorage(),
    configurable: true,
  });
}
