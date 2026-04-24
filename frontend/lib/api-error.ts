import { isAxiosError } from 'axios';
import { publishApiErrorToast } from './api-error-toast';

const DEFAULT_ERROR_MESSAGE = 'Đã có lỗi xảy ra. Vui lòng thử lại.';
const NETWORK_ERROR_MESSAGE = 'Không thể kết nối đến máy chủ. Vui lòng thử lại sau.';

type ApiErrorSource = 'axios' | 'fetch' | 'unknown';

export interface ApiErrorContext {
  source?: ApiErrorSource;
  endpoint?: string;
  method?: string;
  statusCode?: number;
  payload?: unknown;
}

export interface NormalizedApiError {
  source: ApiErrorSource;
  statusCode?: number;
  endpoint?: string;
  method?: string;
  backendDetail?: string;
  displayMessage: string;
  debugPayload?: unknown;
  rawError: unknown;
}

export class ApiRequestError extends Error {
  statusCode?: number;
  backendDetail?: string;
  endpoint?: string;
  method?: string;
  debugPayload?: unknown;
  normalized: NormalizedApiError;

  constructor(normalized: NormalizedApiError) {
    super(normalized.displayMessage);
    this.name = 'ApiRequestError';
    this.statusCode = normalized.statusCode;
    this.backendDetail = normalized.backendDetail;
    this.endpoint = normalized.endpoint;
    this.method = normalized.method;
    this.debugPayload = normalized.debugPayload;
    this.normalized = normalized;
  }
}

const readFirstText = (value: unknown): string | undefined => {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed ? trimmed : undefined;
  }
  if (Array.isArray(value)) {
    const items = value
      .map((item) => (typeof item === 'string' ? item.trim() : ''))
      .filter(Boolean);
    if (!items.length) {
      return undefined;
    }
    return items.join(', ');
  }
  return undefined;
};

const extractBackendDetail = (payload: unknown): string | undefined => {
  if (!payload) {
    return undefined;
  }

  if (typeof payload === 'string') {
    const trimmed = payload.trim();
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
      try {
        const parsed = JSON.parse(trimmed);
        const parsedDetail = extractBackendDetail(parsed);
        if (parsedDetail) {
          return parsedDetail;
        }
      } catch {
        // Keep fallback to raw string below.
      }
    }
  }

  const payloadText = readFirstText(payload);
  if (payloadText) {
    return payloadText;
  }

  if (typeof payload !== 'object') {
    return undefined;
  }

  const rawDetail = (payload as { detail?: unknown }).detail;
  const detail = readFirstText(rawDetail);
  if (detail) {
    return detail;
  }

  const rawMessage = (payload as { message?: unknown }).message;
  const message = readFirstText(rawMessage);
  if (message) {
    return message;
  }

  return undefined;
};

const isNetworkError = (error: unknown, source: ApiErrorSource): boolean => {
  if (source === 'axios' && isAxiosError(error)) {
    return !error.response;
  }

  if (error instanceof TypeError) {
    return true;
  }

  return false;
};

export const normalizeApiError = (error: unknown, context: ApiErrorContext = {}): NormalizedApiError => {
  if (error instanceof ApiRequestError) {
    return error.normalized;
  }

  let source: ApiErrorSource = context.source ?? 'unknown';
  let statusCode = context.statusCode;
  let endpoint = context.endpoint;
  let method = context.method?.toUpperCase();
  let payload = context.payload;

  if (isAxiosError(error)) {
    source = 'axios';
    statusCode = error.response?.status ?? statusCode;
    endpoint = endpoint ?? error.config?.url;
    method = method ?? error.config?.method?.toUpperCase();
    payload = error.response?.data ?? payload;
  }

  if (!isAxiosError(error) && error && typeof error === 'object') {
    const errorLike = error as {
      response?: { status?: number; data?: unknown };
      config?: { url?: string; method?: string };
    };

    statusCode = statusCode ?? errorLike.response?.status;
    endpoint = endpoint ?? errorLike.config?.url;
    method = method ?? errorLike.config?.method?.toUpperCase();
    payload = payload ?? errorLike.response?.data;
  }

  const backendDetail = extractBackendDetail(payload);
  const fallbackMessage =
    isNetworkError(error, source) || (isAxiosError(error) && !error.response)
      ? NETWORK_ERROR_MESSAGE
      : DEFAULT_ERROR_MESSAGE;

  const displayMessage = backendDetail || fallbackMessage;

  return {
    source,
    statusCode,
    endpoint,
    method,
    backendDetail,
    displayMessage,
    debugPayload: payload,
    rawError: error,
  };
};

export const logApiError = (normalized: NormalizedApiError): void => {
  console.error('API request failed', {
    source: normalized.source,
    method: normalized.method,
    endpoint: normalized.endpoint,
    statusCode: normalized.statusCode,
    backendDetail: normalized.backendDetail,
    payload: normalized.debugPayload,
  });
};

export const reportApiError = (
  error: unknown,
  options: {
    context?: ApiErrorContext;
    suppressToast?: boolean;
  } = {}
): NormalizedApiError => {
  const normalized = normalizeApiError(error, options.context);
  logApiError(normalized);

  if (!options.suppressToast) {
    publishApiErrorToast({ message: normalized.displayMessage });
  }

  return normalized;
};

export const toApiRequestError = (
  error: unknown,
  options: {
    context?: ApiErrorContext;
    suppressToast?: boolean;
  } = {}
): ApiRequestError => {
  const normalized = reportApiError(error, options);
  return new ApiRequestError(normalized);
};
