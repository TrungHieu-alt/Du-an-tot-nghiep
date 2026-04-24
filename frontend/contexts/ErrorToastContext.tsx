import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle } from 'lucide-react';
import { subscribeApiErrorToast } from '../lib/api-error-toast';
import { NormalizedApiError } from '../lib/api-error';

interface ErrorToastContextValue {
  pushApiError: (error: string | NormalizedApiError) => void;
}

interface ToastItem {
  id: number;
  message: string;
}

const TOAST_DURATION_MS = 5000;
const DEDUPE_WINDOW_MS = 1500;

const ErrorToastContext = createContext<ErrorToastContextValue | undefined>(undefined);

export const ErrorToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const lastSeenRef = useRef<Map<string, number>>(new Map());
  const timerRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
    const timer = timerRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timerRef.current.delete(id);
    }
  }, []);

  const pushApiError = useCallback(
    (error: string | NormalizedApiError) => {
      const message = typeof error === 'string' ? error.trim() : error.displayMessage.trim();
      if (!message) {
        return;
      }

      const now = Date.now();
      const lastSeen = lastSeenRef.current.get(message) ?? 0;
      if (now - lastSeen < DEDUPE_WINDOW_MS) {
        return;
      }
      lastSeenRef.current.set(message, now);

      const id = now + Math.floor(Math.random() * 10000);
      setToasts((prev) => [...prev, { id, message }]);

      const timer = setTimeout(() => {
        removeToast(id);
      }, TOAST_DURATION_MS);
      timerRef.current.set(id, timer);
    },
    [removeToast]
  );

  useEffect(() => {
    const unsubscribe = subscribeApiErrorToast((event) => {
      pushApiError(event.message);
    });

    return () => {
      unsubscribe();
      timerRef.current.forEach((timer) => clearTimeout(timer));
      timerRef.current.clear();
    };
  }, [pushApiError]);

  const value = useMemo(
    () => ({
      pushApiError,
    }),
    [pushApiError]
  );

  return (
    <ErrorToastContext.Provider value={value}>
      {children}
      <div className="fixed top-4 right-4 z-[120] flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="max-w-sm bg-red-600 text-white rounded-lg shadow-xl px-4 py-3 text-sm font-medium flex items-start gap-2"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </ErrorToastContext.Provider>
  );
};

export const useErrorToast = (): ErrorToastContextValue => {
  const context = useContext(ErrorToastContext);
  if (!context) {
    throw new Error('useErrorToast must be used within ErrorToastProvider');
  }
  return context;
};
