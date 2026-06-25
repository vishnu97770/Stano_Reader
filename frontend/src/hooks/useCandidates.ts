import { useEffect, useState } from 'react';
import { api } from '../services/apiService';
import type { CandidateResult } from '../types/candidate';

export interface UseCandidatesReturn {
  candidates: CandidateResult[];
  isLoading: boolean;
  error: string | null;
}

export function useCandidates(phonemes: string[], transcript: string[]): UseCandidatesReturn {
  const [candidates, setCandidates] = useState<CandidateResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (phonemes.length === 0) {
      setCandidates([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    api.candidates
      .get(phonemes, transcript)
      .then((result) => {
        setCandidates(result.candidates);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Candidate lookup failed');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [phonemes, transcript]);

  return { candidates, isLoading, error };
}
