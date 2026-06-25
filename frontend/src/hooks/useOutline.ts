import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { SymbolResult } from '../types/analysis';
import type { Outline, RecognizedStroke } from '../types/outline';
import type { StrokeRecord } from '../types/session';

function emptyOutline(): Outline {
  return {
    id: crypto.randomUUID(),
    recognizedStrokes: [],
    createdAt: Date.now(),
  };
}

export interface UseOutlineReturn {
  outline: Outline;
  isRebuilding: boolean;
  addStroke: (result: SymbolResult) => void;
  clearOutline: () => void;
  rebuildFromStrokes: (strokes: StrokeRecord[]) => Promise<void>;
}

export function useOutline(): UseOutlineReturn {
  const [outline, setOutline] = useState<Outline>(emptyOutline);
  const [isRebuilding, setIsRebuilding] = useState(false);

  const addStroke = useCallback((result: SymbolResult) => {
    if (result.symbol === 'UNKNOWN') return;
    const entry: RecognizedStroke = {
      strokeId: result.stroke_id,
      symbol: result.symbol,
      family: result.family,
      confidence: result.confidence,
      timestamp: Date.now(),
    };
    setOutline((prev) => ({
      ...prev,
      recognizedStrokes: [...prev.recognizedStrokes, entry],
    }));
  }, []);

  const clearOutline = useCallback(() => {
    setOutline(emptyOutline());
  }, []);

  const rebuildFromStrokes = useCallback(async (strokes: StrokeRecord[]) => {
    setIsRebuilding(true);
    const recognized: RecognizedStroke[] = [];
    for (const stroke of strokes) {
      try {
        const result = await api.classify.classifySymbol(stroke.id, stroke.points);
        if (result.symbol !== 'UNKNOWN') {
          recognized.push({
            strokeId: result.stroke_id,
            symbol: result.symbol,
            family: result.family,
            confidence: result.confidence,
            timestamp: new Date(stroke.created_at).getTime(),
          });
        }
      } catch {
        // Stroke is unclassifiable — omit from outline
      }
    }
    setOutline({
      id: crypto.randomUUID(),
      recognizedStrokes: recognized,
      createdAt: Date.now(),
    });
    setIsRebuilding(false);
  }, []);

  return { outline, isRebuilding, addStroke, clearOutline, rebuildFromStrokes };
}
