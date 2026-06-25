import { useCallback, useState } from 'react';

import { api } from '../services/apiService';
import type { SymbolResult } from '../types/analysis';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeSymbolReturn {
  result: SymbolResult | null;
  isClassifying: boolean;
  error: string | null;
  classifySymbol: (strokeId: string, points: StrokePoint[]) => Promise<SymbolResult | null>;
}

export function useStrokeSymbol(): UseStrokeSymbolReturn {
  const [result, setResult] = useState<SymbolResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifySymbol = useCallback(async (strokeId: string, points: StrokePoint[]): Promise<SymbolResult | null> => {
    if (points.length < 2) return null;

    setIsClassifying(true);
    setError(null);

    try {
      const symbolResult = await api.classify.classifySymbol(strokeId, points);
      setResult(symbolResult);
      return symbolResult;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Symbol classification failed');
      return null;
    } finally {
      setIsClassifying(false);
    }
  }, []);

  return { result, isClassifying, error, classifySymbol };
}
