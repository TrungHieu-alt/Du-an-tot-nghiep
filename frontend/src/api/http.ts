
import { ENV } from '../config/env';

interface RequestOptions extends RequestInit {
  body?: any;
}

export async function http<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, ...rest } = options;
  
  const headers = new Headers(options.headers);
  if (body && !(body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Bypass ngrok warning if necessary
  headers.set('ngrok-skip-browser-warning', 'true');

  const config: RequestInit = {
    ...rest,
    headers,
    body: body instanceof FormData ? body : JSON.stringify(body),
  };

  const response = await fetch(`${ENV.API_BASE_URL}${path}`, config);

  if (!response.ok) {
    let errorMessage = 'Đã có lỗi xảy ra';
    try {
      const errorData = await response.json();
      // NestJS common error structure: { message: string | string[], error: string, statusCode: number }
      errorMessage = Array.isArray(errorData.message) 
        ? errorData.message[0] 
        : errorData.message || errorMessage;
    } catch {
      errorMessage = `Error ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) return {} as T;
  
  return response.json();
}
