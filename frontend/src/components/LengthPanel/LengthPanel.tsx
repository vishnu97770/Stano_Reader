import type { LengthResult } from '../../types/length';

interface LengthPanelProps {
  result: LengthResult | null;
  isClassifying: boolean;
  error: string | null;
}

function modificationBadge(type: string): string {
  return type === 'HALF'
    ? 'bg-violet-100 text-violet-700'
    : 'bg-orange-100 text-orange-700';
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-emerald-600';
  if (confidence >= 0.5) return 'text-indigo-600';
  return 'text-gray-500';
}

export default function LengthPanel({ result, isClassifying, error }: LengthPanelProps) {
  const modified = result?.is_modified === true;

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Length
        </h2>
        {isClassifying && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">detecting…</span>
        )}
        {!isClassifying && modified && (
          <span className="ml-auto text-[10px] text-emerald-600 font-medium">modified</span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {error && <p className="text-xs text-red-500">{error}</p>}

        {!error && !isClassifying && !modified && (
          <p className="text-xs text-gray-400">Normal length.</p>
        )}

        {!error && modified && result && (
          <div className="space-y-2">
            {/* Modification type badge */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Type
              </span>
              {result.modification_type && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${modificationBadge(result.modification_type)}`}>
                  {result.modification_type}
                </span>
              )}
            </div>

            {/* Added phoneme */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Adds
              </span>
              <span className="text-sm font-mono text-indigo-600">
                {result.added_phoneme ?? '—'}
              </span>
            </div>

            {/* Confidence */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Confidence
              </span>
              <span className={`text-sm font-mono font-semibold ${confidenceColor(result.confidence)}`}>
                {Math.round(result.confidence * 100)}%
              </span>
            </div>

            {/* Length ratio */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Ratio
              </span>
              <span className="text-xs font-mono text-gray-600">
                {result.measured_length.toFixed(1)}px / {result.canonical_length.toFixed(0)}px
                {' '}= {result.length_ratio.toFixed(2)}×
              </span>
            </div>

            {/* Reasoning */}
            {result.reasoning && (
              <p className="text-[10px] text-gray-400 font-mono leading-relaxed pt-1 border-t border-gray-100">
                {result.reasoning}
              </p>
            )}
          </div>
        )}

        {/* Always show length metrics when result is present but not modified */}
        {!error && !modified && result && (
          <div className="mt-1">
            <span className="text-[10px] font-mono text-gray-400">
              {result.measured_length.toFixed(1)}px ({result.length_ratio.toFixed(2)}× canonical)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
