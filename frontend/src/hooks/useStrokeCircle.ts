import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { CircleResult } from '../types/circle';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeCircleReturn {
  result: CircleResult | null;
  isClassifying: boolean;
  error: string | null;
  classifyCircle: (strokeId: string, points: StrokePoint[]) => Promise<CircleResult | null>;
}

export function useStrokeCircle(): UseStrokeCircleReturn {
  const [result, setResult] = useState<CircleResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyCircle = useCallback(
    async (strokeId: string, points: StrokePoint[]): Promise<CircleResult | null> => {
      if (points.length < 2) return null;
      setIsClassifying(true);
      setError(null);
      try {
        const circleResult = await api.circle.classify(strokeId, points);
        setResult(circleResult);
        return circleResult;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Circle classification failed');
        return null;
      } finally {
        setIsClassifying(false);
      }
    },
    [],
  );

  return { result, isClassifying, error, classifyCircle };
}
