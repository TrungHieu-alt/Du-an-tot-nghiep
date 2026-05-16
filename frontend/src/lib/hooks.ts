import { useState, useEffect, type DependencyList } from "react";
import { ApiError } from "./api";

export interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  setData: React.Dispatch<React.SetStateAction<T | null>>;
  reload: () => void;
}

export function useFetch<T>(fetcher: () => Promise<T>, deps: DependencyList): FetchState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetcher()
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof ApiError ? e.body.message : "Không thể kết nối. Kiểm tra mạng và thử lại.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = () => setTick((t) => t + 1);
  return { data, loading, error, setData, reload };
}
