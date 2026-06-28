import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { HookResult } from '../types/hook';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeHookReturn {
  result: HookResult | null;
  isClassifying: boolean;
  error: string | null;
  classifyHook: (strokeId: string, points: StrokePoint[]) => Promise<HookResult | null>;
}

export function useStrokeHook(): UseStrokeHookReturn {
  const [result, setResult] = useState<HookResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyHook = useCallback(
    async (strokeId: string, points: StrokePoint[]): Promise<HookResult | null> => {
      if (points.length < 2) return null;
      setIsClassifying(true);
      setError(null);
      try {
        const hookResult = await api.hook.classify(strokeId, points);
        setResult(hookResult);
        return hookResult;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Hook classification failed');
        return null;
      } finally {
        setIsClassifying(false);
      }
    },
    [],
  );

  return { result, isClassifying, error, classifyHook };
}
