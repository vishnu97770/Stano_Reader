interface TranscriptToolbarProps {
  words: string[];
  onUndo: () => void;
  onClear: () => void;
  onCopy: () => void;
  onExport: () => void;
}

export default function TranscriptToolbar({
  words,
  onUndo,
  onClear,
  onCopy,
  onExport,
}: TranscriptToolbarProps) {
  const disabled = words.length === 0;

  return (
    <div className="flex items-center gap-1 shrink-0">
      <button
        onClick={onUndo}
        disabled={disabled}
        title="Undo last word"
        className="px-2 py-1 rounded text-[10px] font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Undo
      </button>
      <button
        onClick={onClear}
        disabled={disabled}
        title="Clear transcript"
        className="px-2 py-1 rounded text-[10px] font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Clear
      </button>
      <button
        onClick={onCopy}
        disabled={disabled}
        title="Copy transcript to clipboard"
        className="px-2 py-1 rounded text-[10px] font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Copy
      </button>
      <button
        onClick={onExport}
        disabled={disabled}
        title="Export transcript as .txt"
        className="px-2 py-1 rounded text-[10px] font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Export
      </button>
    </div>
  );
}
