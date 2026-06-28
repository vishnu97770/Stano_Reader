import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { NearbyStrokeInfo, VowelResult } from '../types/vowel';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeVowelReturn {
  result: VowelResult | null;
  isDetecting: boolean;
  error: string | null;
  detectVowel: (
    strokeId: string,
    points: StrokePoint[],
    nearbyStrokes: NearbyStrokeInfo[],
  ) => Promise<VowelResult | null>;
  clearVowel: () => void;
}

export function useStrokeVowel(): UseStrokeVowelReturn {
  const [result, setResult] = useState<VowelResult | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detectVowel = useCallback(
    async (
      strokeId: string,
      points: StrokePoint[],
      nearbyStrokes: NearbyStrokeInfo[],
    ): Promise<VowelResult | null> => {
      if (points.length < 1) return null;
      setIsDetecting(true);
      setError(null);
      try {
        const r = await api.vowel.detect(strokeId, points, nearbyStrokes);
        setResult(r);
        return r;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Vowel detection failed');
        return null;
      } finally {
        setIsDetecting(false);
      }
    },
    [],
  );

  const clearVowel = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, isDetecting, error, detectVowel, clearVowel };
}
