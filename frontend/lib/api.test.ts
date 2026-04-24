import { describe, expect, it, vi } from 'vitest';
import api from './api';
import { reportApiError } from './api-error';

vi.mock('./api-error', () => ({
  reportApiError: vi.fn(() => ({
    displayMessage: 'Lỗi',
    source: 'axios',
  })),
}));

const getResponseRejectedHandler = () => {
  const handlers = (api.interceptors.response as unknown as { handlers: Array<{ rejected?: (error: unknown) => Promise<unknown> }> }).handlers;
  const handler = handlers[handlers.length - 1]?.rejected;
  if (!handler) {
    throw new Error('Missing axios response rejected interceptor');
  }
  return handler;
};

describe('lib/api interceptor', () => {
  it('reports api errors and rejects original error', async () => {
    const rejected = getResponseRejectedHandler();
    const error = {
      config: {
        suppressGlobalErrorToast: false,
      },
    };

    await expect(rejected(error)).rejects.toBe(error);
    expect(reportApiError).toHaveBeenCalledWith(error, {
      suppressToast: false,
      context: { source: 'axios' },
    });
  });

  it('respects toast opt-out flag from request config', async () => {
    const rejected = getResponseRejectedHandler();
    const error = {
      config: {
        suppressGlobalErrorToast: true,
      },
    };

    await expect(rejected(error)).rejects.toBe(error);
    expect(reportApiError).toHaveBeenCalledWith(error, {
      suppressToast: true,
      context: { source: 'axios' },
    });
  });
});
