import React from 'react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import { ErrorToastProvider } from './ErrorToastContext';
import { publishApiErrorToast } from '../lib/api-error-toast';

describe('ErrorToastProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders one toast for duplicate messages in dedupe window', () => {
    render(
      <ErrorToastProvider>
        <div>page</div>
      </ErrorToastProvider>
    );

    act(() => {
      publishApiErrorToast({ message: 'Duplicate error' });
      publishApiErrorToast({ message: 'Duplicate error' });
    });

    expect(screen.getAllByRole('alert')).toHaveLength(1);
  });

  it('auto dismisses toast after default timeout', () => {
    render(
      <ErrorToastProvider>
        <div>page</div>
      </ErrorToastProvider>
    );

    act(() => {
      publishApiErrorToast({ message: 'Temporary error' });
    });
    expect(screen.getByText('Temporary error')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(screen.queryByText('Temporary error')).not.toBeInTheDocument();
  });
});
