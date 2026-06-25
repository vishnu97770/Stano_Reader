import { useCallback } from 'react';
import TranscriptToolbar from '../TranscriptToolbar/TranscriptToolbar';

interface TranscriptPanelProps {
  words: string[];
  onUndo: () => void;
  onClear: () => void;
}

function exportTxt(words: string[]): void {
  const text = words.join(' ');
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'transcript.txt';
  a.click();
  URL.revokeObjectURL(url);
}

export default function TranscriptPanel({ words, onUndo, onClear }: TranscriptPanelProps) {
  const handleCopy = useCallback(() => {
    void navigator.clipboard.writeText(words.join(' '));
  }, [words]);

  const handleExport = useCallback(() => {
    exportTxt(words);
  }, [words]);

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Transcript
        </h2>
        {words.length > 0 && (
          <span className="ml-1 text-[10px] text-gray-400 font-mono">
            {words.length} {words.length === 1 ? 'word' : 'words'}
          </span>
        )}
        <div className="ml-auto">
          <TranscriptToolbar
            words={words}
            onUndo={onUndo}
            onClear={onClear}
            onCopy={handleCopy}
            onExport={handleExport}
          />
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4 min-h-[80px] flex items-start">
        {words.length === 0 ? (
          <p className="text-xs text-gray-400">Click a candidate word to begin transcribing.</p>
        ) : (
          <p className="text-sm text-gray-900 leading-relaxed break-words w-full">
            {words.map((word, i) => (
              <span key={i}>
                {i > 0 && ' '}
                {word}
              </span>
            ))}
          </p>
        )}
      </div>
    </div>
  );
}
