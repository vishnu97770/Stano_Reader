import type { PhraseResult } from '../../types/phrase';

interface PhrasePanelProps {
  result: PhraseResult | null;
  isDetecting: boolean;
  error: string | null;
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'text-emerald-600';
  if (confidence >= 0.75) return 'text-indigo-600';
  return 'text-gray-500';
}

export default function PhrasePanel({ result, isDetecting, error }: PhrasePanelProps) {
  const detected = result?.is_phrase === true;

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Phraseography
        </h2>
        {isDetecting && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">detecting…</span>
        )}
        {!isDetecting && detected && (
          <span className="ml-auto text-[10px] text-emerald-600 font-medium">phrase detected</span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {error && <p className="text-xs text-red-500">{error}</p>}

        {!error && !isDetecting && !detected && (
          <p className="text-xs text-gray-400">No phrase detected.</p>
        )}

        {!error && detected && result && (
          <div className="space-y-2">
            {/* Phrase text + confidence */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Phrase
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-900">
                  {result.phrase_text}
                </span>
                <span className={`text-xs font-mono font-semibold ${confidenceColor(result.confidence)}`}>
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Alternatives */}
            {result.alternatives.length > 0 && (
              <div className="flex items-start gap-2">
                <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide pt-0.5">
                  Also
                </span>
                <div className="flex flex-wrap gap-1">
                  {result.alternatives.map((alt) => (
                    <span
                      key={alt.phrase_text}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-medium"
                    >
                      {alt.phrase_text} ({Math.round(alt.confidence * 100)}%)
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Reasoning */}
            {result.reasoning && (
              <p className="text-[10px] text-gray-400 font-mono leading-relaxed pt-1 border-t border-gray-100">
                {result.reasoning}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
