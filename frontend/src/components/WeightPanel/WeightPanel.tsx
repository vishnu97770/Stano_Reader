import type { WeightResult } from '../../types/analysis';

interface WeightPanelProps {
  result: WeightResult | null;
  isClassifying: boolean;
  error: string | null;
}

type Weight = 'LIGHT' | 'HEAVY' | 'AMBIGUOUS';

function weightColor(weight: Weight): string {
  if (weight === 'LIGHT') return 'text-emerald-600';
  if (weight === 'HEAVY') return 'text-indigo-600';
  return 'text-amber-500';
}

function weightBg(weight: Weight): string {
  if (weight === 'LIGHT') return 'bg-emerald-50 border-emerald-200 text-emerald-700';
  if (weight === 'HEAVY') return 'bg-indigo-50 border-indigo-200 text-indigo-700';
  return 'bg-amber-50 border-amber-200 text-amber-700';
}

function weightBar(weight: Weight): string {
  if (weight === 'LIGHT') return 'bg-emerald-400';
  if (weight === 'HEAVY') return 'bg-indigo-500';
  return 'bg-amber-400';
}

function pct(v: number): string {
  return `${Math.round(v * 100)}%`;
}

export default function WeightPanel({ result, isClassifying, error }: WeightPanelProps) {
  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Stroke Weight
        </h2>
        {isClassifying && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">classifying…</span>
        )}
      </div>

      <div className="px-4 py-3 space-y-3">
        {error && (
          <p className="text-xs text-red-500">{error}</p>
        )}

        {!result && !isClassifying && !error && (
          <p className="text-xs text-gray-400">Draw a stroke to measure weight.</p>
        )}

        {result && (
          <>
            {/* Weight badge */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-gray-400 uppercase tracking-wider">Weight</span>
              <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wide ${weightBg(result.weight)}`}>
                {result.weight}
              </span>
            </div>

            {/* Pressure bar */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">
                  Avg Pressure
                </span>
                <span className={`text-sm font-semibold font-mono ${weightColor(result.weight)}`}>
                  {pct(result.avg_pressure)}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                {/* Light threshold marker */}
                <div
                  className="absolute top-0 bottom-0 w-px bg-gray-300"
                  style={{ left: `${result.threshold_light * 100}%` }}
                />
                {/* Heavy threshold marker */}
                <div
                  className="absolute top-0 bottom-0 w-px bg-gray-300"
                  style={{ left: `${result.threshold_heavy * 100}%` }}
                />
                {/* Pressure fill */}
                <div
                  className={`h-full rounded-full transition-all duration-300 ${weightBar(result.weight)}`}
                  style={{ width: `${result.avg_pressure * 100}%` }}
                />
              </div>
              {/* Threshold labels */}
              <div className="flex justify-between mt-0.5">
                <span className="text-[9px] text-gray-300">0</span>
                <span className="text-[9px] text-gray-400"
                  style={{ marginLeft: `${result.threshold_light * 100 - 6}%` }}>
                  {pct(result.threshold_light)}
                </span>
                <span className="text-[9px] text-gray-400">
                  {pct(result.threshold_heavy)}
                </span>
                <span className="text-[9px] text-gray-300">100</span>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex gap-4">
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Max</span>
                <span className="text-xs font-mono text-gray-600">{pct(result.max_pressure)}</span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Variance</span>
                <span className="text-xs font-mono text-gray-600">{result.variance.toFixed(4)}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
