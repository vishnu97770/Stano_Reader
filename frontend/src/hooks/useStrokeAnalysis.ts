import { useCallback, useState } from 'react';

import { api } from '../services/apiService';
import type { StrokeFeatures } from '../types/analysis';
import type { StrokePoint } from '../types/stroke';

export interface UseStrokeAnalysisReturn {
  features: StrokeFeatures | null;
  isAnalyzing: boolean;
  error: string | null;
  analyzeStroke: (strokeId: string, points: StrokePoint[]) => Promise<void>;
}

export function useStrokeAnalysis(): UseStrokeAnalysisReturn {
  const [features, setFeatures] = useState<StrokeFeatures | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeStroke = useCallback(async (strokeId: string, points: StrokePoint[]) => {
    if (points.length < 2) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await api.analysis.analyzeStroke(strokeId, points);
      setFeatures(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  return { features, isAnalyzing, error, analyzeStroke };
}
