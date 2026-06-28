import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/apiService';
import { getSocket } from '../services/socketService';
import type { AIRefinementResult, Domain } from '../types/ai';
import type { CandidateResult } from '../types/candidate';
import type { Outline } from '../types/outline';

export interface AIRefinementParams {
  strokeId: string;
  candidates: CandidateResult[];
  transcriptContext: string[];
  outline: Outline;
  ipaSequence: string[];
  domain: Domain;
  vowelSignals: string[];
  phraseDetected: boolean;
  socketId: string | undefined;
}

export interface UseAIRefinementReturn {
  aiResult: AIRefinementResult | null;
  isRefining: boolean;
  error: string | null;
  refine: (params: AIRefinementParams) => Promise<void>;
  clear: () => void;
}

export function useAIRefinement(enabled: boolean): UseAIRefinementReturn {
  const [aiResult, setAIResult] = useState<AIRefinementResult | null>(null);
  const [isRefining, setIsRefining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Listen for async AI result pushed via Socket.IO
  useEffect(() => {
    if (!enabled) return;

    const socket = getSocket();
    const handleRefined = (result: AIRefinementResult) => {
      setAIResult(result);
      setIsRefining(false);
    };

    socket.on('candidates_refined', handleRefined);
    return () => {
      socket.off('candidates_refined', handleRefined);
    };
  }, [enabled]);

  const refine = useCallback(
    async (params: AIRefinementParams): Promise<void> => {
      if (!enabled) return;

      setIsRefining(true);
      setAIResult(null);
      setError(null);

      try {
        // Immediate HTTP response is a placeholder — real result arrives via socket
        await api.ai.refine({
          stroke_id: params.strokeId,
          candidates: params.candidates.map((c) => ({
            word: c.word,
            confidence: c.confidence,
          })),
          transcript_context: params.transcriptContext.slice(-10),
          outline: params.outline.recognizedStrokes.map((s) => s.symbol).join(', '),
          ipa_sequence: params.ipaSequence,
          domain: params.domain,
          vowel_signals: params.vowelSignals,
          phrase_detected: params.phraseDetected,
          socket_id: params.socketId ?? null,
        });
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'AI refinement failed');
        setIsRefining(false);
      }
    },
    [enabled],
  );

  const clear = useCallback(() => {
    setAIResult(null);
    setError(null);
    setIsRefining(false);
  }, []);

  return { aiResult, isRefining, error, refine, clear };
}
