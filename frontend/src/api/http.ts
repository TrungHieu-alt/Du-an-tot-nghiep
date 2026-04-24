
import { ENV } from '../config/env';
import { toApiRequestError } from '../../lib/api-error';

interface RequestOptions extends RequestInit {
  body?: unknown;
  suppressGlobalErrorToast?: boolean;
}

export async function http<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, suppressGlobalErrorToast = false, ...rest } = options;
  
  const headers = new Headers(options.headers);
  if (body && !(body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Bypass ngrok warning if necessary
  headers.set('ngrok-skip-browser-warning', 'true');

  const config: RequestInit = {
    ...rest,
    headers,
    body:
      body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
  };

  const method = options.method?.toUpperCase() ?? 'GET';
  let response: Response;
  try {
    response = await fetch(`${ENV.API_BASE_URL}${path}`, config);
  } catch (error) {
    throw toApiRequestError(error, {
      suppressToast: suppressGlobalErrorToast,
      context: {
        source: 'fetch',
        endpoint: path,
        method,
      },
    });
  }

  if (!response.ok) {
    let errorPayload: unknown;
    try {
      const contentType = response.headers.get('content-type') ?? '';
      if (contentType.includes('application/json')) {
        errorPayload = await response.json();
      } else {
        const text = await response.text();
        if (text.trim()) {
          errorPayload = text;
        }
      }
    } catch {
      errorPayload = undefined;
    }

    throw toApiRequestError(errorPayload ?? response.statusText, {
      suppressToast: suppressGlobalErrorToast,
      context: {
        source: 'fetch',
        endpoint: path,
        method,
        statusCode: response.status,
        payload: errorPayload,
      },
    });
  }

  if (response.status === 204) return {} as T;
  
  return response.json();
}
