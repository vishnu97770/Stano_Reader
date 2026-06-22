import type { FamilyResult } from '../../types/analysis';

interface FamilyPanelProps {
  result: FamilyResult | null;
  isClassifying: boolean;
  error: string | null;
}

// Strip "_FAMILY" suffix for compact display: "TD_FAMILY" → "TD"
function shortName(family: string): string {
  return family.replace('_FAMILY', '');
}

function pct(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

// Color coding by confidence tier
function confidenceColor(confidence: number): string {
  if (confidence >= 0.75) return 'text-emerald-600';
  if (confidence >= 0.45) return 'text-amber-500';
  return 'text-red-400';
}

export default function FamilyPanel({ result, isClassifying, error }: FamilyPanelProps) {
  return (
    <div className="flex flex-col bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Family
        </h2>
        {isClassifying && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">classifying…</span>
        )}
      </div>

      <div className="px-4 py-3">
        {error && (
          <p className="text-xs text-red-500 mb-2">{error}</p>
        )}

        {!result && !isClassifying && !error && (
          <p className="text-xs text-gray-400">Draw a stroke to classify it.</p>
        )}

        {result && (
          <>
            {/* Primary match */}
            <div className="mb-3">
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">
                Detected Family
              </p>
              {result.family === 'UNKNOWN' ? (
                <p className="text-sm font-semibold text-gray-400">UNKNOWN</p>
              ) : (
                <div className="flex items-baseline justify-between">
                  <span className="text-lg font-bold text-gray-800 font-mono">
                    {shortName(result.family)}
                  </span>
                  <span className={`text-sm font-semibold font-mono ${confidenceColor(result.confidence)}`}>
                    {pct(result.confidence)}
                  </span>
                </div>
              )}

              {/* Confidence bar */}
              {result.family !== 'UNKNOWN' && (
                <div className="mt-1.5 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
              )}
            </div>

            {/* Alternatives */}
            {result.alternatives.length > 0 && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1.5">
                  Alternatives
                </p>
                <div className="space-y-1">
                  {result.alternatives.map((alt) => (
                    <div key={alt.family} className="flex items-center justify-between">
                      <span className="text-xs font-mono text-gray-600">
                        {shortName(alt.family)}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gray-300 rounded-full"
                            style={{ width: `${alt.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400 font-mono w-8 text-right">
                          {pct(alt.confidence)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
