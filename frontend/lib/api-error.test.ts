import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AxiosError } from 'axios';
import { normalizeApiError, reportApiError } from './api-error';
import { subscribeApiErrorToast } from './api-error-toast';

describe('api-error', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('prefers backend detail for display message', () => {
    const normalized = normalizeApiError('Request failed', {
      source: 'fetch',
      statusCode: 422,
      payload: { detail: 'Email đã tồn tại' },
      endpoint: '/users/register',
      method: 'POST',
    });

    expect(normalized.backendDetail).toBe('Email đã tồn tại');
    expect(normalized.displayMessage).toBe('Email đã tồn tại');
    expect(normalized.statusCode).toBe(422);
  });

  it('uses message when detail is absent', () => {
    const normalized = normalizeApiError('Request failed', {
      source: 'fetch',
      statusCode: 400,
      payload: { message: ['Invalid role'] },
    });

    expect(normalized.backendDetail).toBe('Invalid role');
    expect(normalized.displayMessage).toBe('Invalid role');
  });

  it('falls back to generic message when payload is empty', () => {
    const normalized = normalizeApiError('Request failed', {
      source: 'fetch',
      statusCode: 500,
      payload: undefined,
    });

    expect(normalized.displayMessage).toBe('Đã có lỗi xảy ra. Vui lòng thử lại.');
  });

  it('maps network errors to connection message', () => {
    const axiosError = new AxiosError('Network Error');
    const normalized = normalizeApiError(axiosError, { source: 'axios' });

    expect(normalized.displayMessage).toBe('Không thể kết nối đến máy chủ. Vui lòng thử lại sau.');
  });

  it('logs and publishes toast event', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const listener = vi.fn();
    const unsubscribe = subscribeApiErrorToast(listener);

    reportApiError('Request failed', {
      context: {
        source: 'fetch',
        statusCode: 422,
        endpoint: '/users/register',
        method: 'POST',
        payload: { detail: 'Email đã tồn tại' },
      },
    });

    expect(consoleSpy).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith({ message: 'Email đã tồn tại' });
    unsubscribe();
  });

  it('supports toast opt-out', () => {
    const listener = vi.fn();
    const unsubscribe = subscribeApiErrorToast(listener);

    reportApiError('Request failed', {
      suppressToast: true,
      context: {
        source: 'fetch',
        statusCode: 422,
        payload: { detail: 'Email đã tồn tại' },
      },
    });

    expect(listener).not.toHaveBeenCalled();
    unsubscribe();
  });
});
