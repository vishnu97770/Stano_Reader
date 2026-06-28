import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { LengthResult } from '../types/length';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeLengthReturn {
  result: LengthResult | null;
  isClassifying: boolean;
  error: string | null;
  classifyLength: (strokeId: string, points: StrokePoint[], familyName?: string) => Promise<LengthResult | null>;
}

export function useStrokeLength(): UseStrokeLengthReturn {
  const [result, setResult] = useState<LengthResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyLength = useCallback(
    async (strokeId: string, points: StrokePoint[], familyName?: string): Promise<LengthResult | null> => {
      if (points.length < 2) return null;
      setIsClassifying(true);
      setError(null);
      try {
        const lengthResult = await api.length.classify(strokeId, points, familyName);
        setResult(lengthResult);
        return lengthResult;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Length classification failed');
        return null;
      } finally {
        setIsClassifying(false);
      }
    },
    [],
  );

  return { result, isClassifying, error, classifyLength };
}
