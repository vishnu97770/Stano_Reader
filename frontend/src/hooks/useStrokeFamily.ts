import { useCallback, useState } from 'react';

import { api } from '../services/apiService';
import type { FamilyResult } from '../types/analysis';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeFamilyReturn {
  result: FamilyResult | null;
  isClassifying: boolean;
  error: string | null;
  classifyFamily: (strokeId: string, points: StrokePoint[]) => Promise<void>;
}

export function useStrokeFamily(): UseStrokeFamilyReturn {
  const [result, setResult] = useState<FamilyResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyFamily = useCallback(async (strokeId: string, points: StrokePoint[]) => {
    if (points.length < 2) return;

    setIsClassifying(true);
    setError(null);

    try {
      const familyResult = await api.classify.classifyFamily(strokeId, points);
      setResult(familyResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Classification failed');
    } finally {
      setIsClassifying(false);
    }
  }, []);

  return { result, isClassifying, error, classifyFamily };
}
