import { useCallback, useState } from 'react';

import { api } from '../services/apiService';
import type { WeightResult } from '../types/analysis';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeWeightReturn {
  result: WeightResult | null;
  isClassifying: boolean;
  error: string | null;
  classifyWeight: (strokeId: string, points: StrokePoint[]) => Promise<void>;
}

export function useStrokeWeight(): UseStrokeWeightReturn {
  const [result, setResult] = useState<WeightResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyWeight = useCallback(async (strokeId: string, points: StrokePoint[]) => {
    if (points.length < 2) return;

    setIsClassifying(true);
    setError(null);

    try {
      const weightResult = await api.classify.classifyWeight(strokeId, points);
      setResult(weightResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Weight classification failed');
    } finally {
      setIsClassifying(false);
    }
  }, []);

  return { result, isClassifying, error, classifyWeight };
}
