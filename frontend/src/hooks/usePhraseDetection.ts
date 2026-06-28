import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { PhraseResult } from '../types/phrase';

export interface UsePhraseDetectionReturn {
  result: PhraseResult | null;
  isDetecting: boolean;
  error: string | null;
  detectPhrase: (
    strokeId: string,
    outlineFamilies: string[],
    candidates: string[],
  ) => Promise<PhraseResult | null>;
  clearPhrase: () => void;
}

export function usePhraseDetection(): UsePhraseDetectionReturn {
  const [result, setResult] = useState<PhraseResult | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detectPhrase = useCallback(
    async (
      strokeId: string,
      outlineFamilies: string[],
      candidates: string[],
    ): Promise<PhraseResult | null> => {
      if (outlineFamilies.length === 0) {
        setResult(null);
        return null;
      }
      setIsDetecting(true);
      setError(null);
      try {
        const r = await api.phrase.detect(strokeId, outlineFamilies, candidates);
        setResult(r);
        return r;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Phrase detection failed');
        return null;
      } finally {
        setIsDetecting(false);
      }
    },
    [],
  );

  const clearPhrase = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, isDetecting, error, detectPhrase, clearPhrase };
}
