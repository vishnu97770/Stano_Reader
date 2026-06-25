import type { SymbolResult } from '../../types/analysis';

interface SymbolPanelProps {
  result: SymbolResult | null;
  isClassifying: boolean;
  error: string | null;
}

function pct(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

function familyShort(family: string): string {
  return family.replace('_FAMILY', '');
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.58) return 'text-emerald-600';
  if (confidence >= 0.45) return 'text-amber-500';
  return 'text-gray-400';
}

export default function SymbolPanel({ result, isClassifying, error }: SymbolPanelProps) {
  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Symbol Recognition
        </h2>
        {isClassifying && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">recognizing…</span>
        )}
      </div>

      <div className="px-4 py-3 space-y-3">
        {error && (
          <p className="text-xs text-red-500">{error}</p>
        )}

        {!result && !isClassifying && !error && (
          <p className="text-xs text-gray-400">Draw a stroke to recognize it.</p>
        )}

        {result && (
          <>
            {/* Family context */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-gray-400 uppercase tracking-wider">Family</span>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-gray-600">
                  {familyShort(result.family)}
                </span>
                <span className="text-[10px] text-gray-400 font-mono">
                  {pct(result.family_confidence)}
                </span>
              </div>
            </div>

            {/* Thickness warning badge */}
            {result.thickness_missing && (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-amber-50 border border-amber-200 rounded text-[10px] text-amber-600">
                <span>⚠</span>
                <span>Thickness unavailable — using frequency prior</span>
              </div>
            )}

            {/* Primary symbol */}
            {result.symbol === 'UNKNOWN' ? (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">
                  Detected Symbol
                </p>
                <p className="text-sm font-semibold text-gray-400">UNKNOWN</p>
              </div>
            ) : (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">
                  Detected Symbol
                </p>
                <div className="flex items-baseline justify-between mb-1.5">
                  <span className="text-3xl font-bold text-gray-900 font-mono leading-none">
                    {result.symbol}
                  </span>
                  <span className={`text-lg font-semibold font-mono ${confidenceColor(result.confidence)}`}>
                    {pct(result.confidence)}
                  </span>
                </div>
                {/* Confidence bar */}
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Alternatives */}
            {result.alternatives.length > 0 && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1.5">
                  Alternatives
                </p>
                <div className="space-y-1">
                  {result.alternatives.map((alt) => (
                    <div key={alt.symbol} className="flex items-center justify-between">
                      <span className="text-sm font-mono font-semibold text-gray-500">
                        {alt.symbol}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1 bg-gray-100 rounded-full overflow-hidden">
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
