import { useEffect, useState } from 'react';
import { api } from '../services/apiService';
import type { Outline } from '../types/outline';

export interface UsePhonemeReturn {
  phonemes: string[];
  isMapping: boolean;
  error: string | null;
}

export function usePhoneme(outline: Outline): UsePhonemeReturn {
  const [phonemes, setPhonemes] = useState<string[]>([]);
  const [isMapping, setIsMapping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const symbols = outline.recognizedStrokes.map((s) => s.symbol);

    if (symbols.length === 0) {
      setPhonemes([]);
      setError(null);
      return;
    }

    setIsMapping(true);
    setError(null);

    api.phonemes
      .map(symbols)
      .then((result) => {
        setPhonemes(result.phonemes);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Phoneme mapping failed');
      })
      .finally(() => {
        setIsMapping(false);
      });
  }, [outline]);

  return { phonemes, isMapping, error };
}
