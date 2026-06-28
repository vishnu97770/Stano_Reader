import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { ExtractedStroke, ImageProcessResult, PageMetadata } from '../types/image';

export interface UseImageProcessReturn {
  processResult: ImageProcessResult | null;
  isProcessing: boolean;
  error: string | null;
  processStrokes: (strokes: ExtractedStroke[], page: PageMetadata) => Promise<ImageProcessResult | null>;
  clearResult: () => void;
}

export function useImageProcess(): UseImageProcessReturn {
  const [processResult, setProcessResult] = useState<ImageProcessResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processStrokes = useCallback(
    async (strokes: ExtractedStroke[], page: PageMetadata): Promise<ImageProcessResult | null> => {
      if (strokes.length === 0) {
        setError('No strokes found in the uploaded image.');
        return null;
      }
      setIsProcessing(true);
      setError(null);
      try {
        const result = await api.image.process(strokes, page.canvas_height, page.canvas_width);
        setProcessResult(result);
        return result;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Processing failed');
        return null;
      } finally {
        setIsProcessing(false);
      }
    },
    [],
  );

  const clearResult = useCallback(() => {
    setProcessResult(null);
    setError(null);
  }, []);

  return { processResult, isProcessing, error, processStrokes, clearResult };
}
