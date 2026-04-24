import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ENV } from '../config/env';
import { http } from './http';
import { ApiRequestError } from '../../lib/api-error';
import { subscribeApiErrorToast } from '../../lib/api-error-toast';

describe('http', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('builds request URL with configured base URL and JSON body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await http<{ ok: boolean }>('/users/register', {
      method: 'POST',
      body: { email: 'dev@example.com' },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe(`${ENV.API_BASE_URL}/users/register`);

    const requestInit = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = new Headers(requestInit.headers);
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('ngrok-skip-browser-warning')).toBe('true');
    expect(requestInit.body).toBe(JSON.stringify({ email: 'dev@example.com' }));
  });

  it('does not force JSON content-type for FormData', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ uploaded: true }), { status: 200 })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    const formData = new FormData();
    formData.append('file', new Blob(['cv']), 'cv.pdf');

    await http('/cv/upload', {
      method: 'POST',
      body: formData,
    });

    const requestInit = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = new Headers(requestInit.headers);
    expect(headers.get('Content-Type')).toBeNull();
    expect(requestInit.body).toBe(formData);
  });

  it('uses first backend error message item when message is an array', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: ['Invalid email format'] }), { status: 422 })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await expect(
      http('/users/register', { method: 'POST', body: { email: 'bad' } })
    ).rejects.toThrow('Invalid email format');
  });

  it('uses FastAPI detail field when backend returns only detail', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Unauthorized' }), { status: 401 })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await expect(http('/users/login', { method: 'POST', body: {} })).rejects.toThrow('Unauthorized');
  });

  it('throws ApiRequestError and publishes toast message', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Validation failed' }), { status: 422 })
    );
    const listener = vi.fn();
    const unsubscribe = subscribeApiErrorToast(listener);
    global.fetch = fetchMock as unknown as typeof fetch;

    await expect(http('/users/register', { method: 'POST', body: {} })).rejects.toBeInstanceOf(
      ApiRequestError
    );
    expect(listener).toHaveBeenCalledWith({ message: 'Validation failed' });
    unsubscribe();
  });

  it('supports suppressGlobalErrorToast option', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Validation failed' }), { status: 422 })
    );
    const listener = vi.fn();
    const unsubscribe = subscribeApiErrorToast(listener);
    global.fetch = fetchMock as unknown as typeof fetch;

    await expect(
      http('/users/register', { method: 'POST', body: {}, suppressGlobalErrorToast: true })
    ).rejects.toBeInstanceOf(ApiRequestError);
    expect(listener).not.toHaveBeenCalled();
    unsubscribe();
  });

  it('returns empty object for 204 responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    global.fetch = fetchMock as unknown as typeof fetch;

    const result = await http<Record<string, never>>('/users/1', {
      method: 'DELETE',
    });
    expect(result).toEqual({});
  });
});
