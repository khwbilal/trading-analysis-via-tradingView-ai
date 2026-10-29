import { useCallback, useEffect, useRef, useState } from "react";
import type { TaskState } from "../api";

/**
 * Load a page's data, and while its background task runs (backtest, picks, hype), reload every few
 * seconds until it finishes. `load` returns the response; `taskOf` reads its task state.
 */
export function useTaskData<T>(load: () => Promise<T>, taskOf: (data: T) => TaskState | undefined, active: boolean) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const d = await load();
      setData(d);
      setError(null);
      if (timer.current) clearTimeout(timer.current);
      if (taskOf(d)?.running) timer.current = setTimeout(() => void refresh(), 3000);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [load, taskOf]);

  useEffect(() => {
    if (active) refresh().catch(() => undefined);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [active, refresh]);

  return { data, error, loading, refresh };
}
