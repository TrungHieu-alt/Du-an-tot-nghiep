
import axios from 'axios';
import { getStoredAccessToken } from './auth-session';
import { ENV } from '../src/config/env';
import { reportApiError } from './api-error';

declare module 'axios' {
  export interface InternalAxiosRequestConfig<D = any> {
    suppressGlobalErrorToast?: boolean;
  }
}

const api = axios.create({
  baseURL: ENV.API_BASE_URL,
  timeout: 30000,
  headers: {
    'ngrok-skip-browser-warning': 'true',
    'Bypass-Tunnel-Reminder': 'true',
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getStoredAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const suppressToast = Boolean(error?.config?.suppressGlobalErrorToast);
    const normalized = reportApiError(error, {
      suppressToast,
      context: {
        source: 'axios',
      },
    });
    if (error && typeof error === 'object') {
      (error as { normalizedApiError?: unknown }).normalizedApiError = normalized;
    }
    return Promise.reject(error);
  }
);

export default api;
