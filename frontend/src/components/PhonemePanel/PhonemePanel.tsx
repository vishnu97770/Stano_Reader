interface PhonemePanelProps {
  phonemes: string[];
  isMapping: boolean;
  error: string | null;
}

export default function PhonemePanel({ phonemes, isMapping, error }: PhonemePanelProps) {
  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Phonemes
        </h2>
        {isMapping && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">mapping…</span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-4">
        {error && (
          <p className="text-xs text-red-500">{error}</p>
        )}

        {!error && phonemes.length === 0 && !isMapping && (
          <p className="text-xs text-gray-400">Phonemes appear as you draw.</p>
        )}

        {phonemes.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {phonemes.map((phoneme, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2.5 py-1 rounded-md bg-indigo-50 border border-indigo-100 text-sm font-mono font-semibold text-indigo-700 leading-none"
              >
                {phoneme}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
