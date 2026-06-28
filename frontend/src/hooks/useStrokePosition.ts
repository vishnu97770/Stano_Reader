import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { PositionResult } from '../types/position';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokePositionReturn {
  result: PositionResult | null;
  isClassifying: boolean;
  error: string | null;
  classifyPosition: (
    strokeId: string,
    points: StrokePoint[],
    canvasHeight: number,
  ) => Promise<PositionResult | null>;
}

export function useStrokePosition(): UseStrokePositionReturn {
  const [result, setResult] = useState<PositionResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyPosition = useCallback(
    async (
      strokeId: string,
      points: StrokePoint[],
      canvasHeight: number,
    ): Promise<PositionResult | null> => {
      if (points.length < 1) return null;
      setIsClassifying(true);
      setError(null);
      try {
        const positionResult = await api.position.classify(strokeId, points, canvasHeight);
        setResult(positionResult);
        return positionResult;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Position classification failed');
        return null;
      } finally {
        setIsClassifying(false);
      }
    },
    [],
  );

  return { result, isClassifying, error, classifyPosition };
}
