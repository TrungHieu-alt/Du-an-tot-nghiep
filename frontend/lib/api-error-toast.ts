export interface ApiErrorToastEvent {
  message: string;
}

type ApiErrorToastListener = (event: ApiErrorToastEvent) => void;

const listeners = new Set<ApiErrorToastListener>();

export const subscribeApiErrorToast = (listener: ApiErrorToastListener): (() => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

export const publishApiErrorToast = (event: ApiErrorToastEvent): void => {
  listeners.forEach((listener) => {
    listener(event);
  });
};
