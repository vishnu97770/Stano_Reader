import { useCallback, useState } from 'react';

export interface UseTranscriptReturn {
  words: string[];
  appendWord: (word: string) => void;
  undoLast: () => void;
  clearTranscript: () => void;
  setTranscript: (words: string[]) => void;
}

export function useTranscript(): UseTranscriptReturn {
  const [words, setWords] = useState<string[]>([]);

  const appendWord = useCallback((word: string) => {
    setWords((prev) => [...prev, word]);
  }, []);

  const undoLast = useCallback(() => {
    setWords((prev) => prev.slice(0, -1));
  }, []);

  const clearTranscript = useCallback(() => {
    setWords([]);
  }, []);

  const setTranscript = useCallback((incoming: string[]) => {
    setWords(incoming);
  }, []);

  return { words, appendWord, undoLast, clearTranscript, setTranscript };
}
