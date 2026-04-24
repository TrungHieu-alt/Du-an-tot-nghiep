
const normalizeApiBaseUrl = (value: string): string => {
  const trimmed = value.replace(/\/+$/, '');
  if (trimmed.endsWith('/api')) {
    return trimmed;
  }
  return `${trimmed}/api`;
};

export const ENV = {
  API_BASE_URL: normalizeApiBaseUrl(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  ),
};
