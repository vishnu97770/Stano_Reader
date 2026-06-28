import type { PositionResult } from '../../types/position';

interface PositionPanelProps {
  result: PositionResult | null;
  isClassifying: boolean;
  error: string | null;
  showGuides: boolean;
  onToggleGuides: () => void;
}

function positionBadgeClass(position: string): string {
  switch (position) {
    case 'FIRST':  return 'bg-indigo-100 text-indigo-700';
    case 'SECOND': return 'bg-emerald-100 text-emerald-700';
    case 'THIRD':  return 'bg-amber-100 text-amber-700';
    default:       return 'bg-gray-100 text-gray-500';
  }
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-emerald-600';
  if (confidence >= 0.5) return 'text-indigo-600';
  return 'text-gray-500';
}

function positionLabel(position: string): string {
  switch (position) {
    case 'FIRST':  return 'First';
    case 'SECOND': return 'Second';
    case 'THIRD':  return 'Third';
    default:       return 'Unknown';
  }
}

export default function PositionPanel({
  result,
  isClassifying,
  error,
  showGuides,
  onToggleGuides,
}: PositionPanelProps) {
  const detected = result !== null && result.position !== 'UNKNOWN';

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Position
        </h2>

        {/* Guide lines toggle */}
        <button
          type="button"
          onClick={onToggleGuides}
          className={`ml-auto text-[10px] px-2 py-0.5 rounded border transition-colors ${
            showGuides
              ? 'border-sky-400 bg-sky-50 text-sky-600'
              : 'border-gray-200 bg-white text-gray-400 hover:border-gray-300 hover:text-gray-500'
          }`}
          title={showGuides ? 'Hide position guides' : 'Show position guides'}
        >
          {showGuides ? 'guides on' : 'guides off'}
        </button>

        {isClassifying && (
          <span className="text-xs text-indigo-500 animate-pulse">detecting…</span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {error && <p className="text-xs text-red-500">{error}</p>}

        {!error && !isClassifying && !detected && (
          <p className="text-xs text-gray-400">No stroke yet.</p>
        )}

        {!error && result && (
          <div className="space-y-2">
            {/* Position badge */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Position
              </span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${positionBadgeClass(result.position)}`}>
                {positionLabel(result.position)}
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

            {/* Centroid Y */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Centroid Y
              </span>
              <span className="text-xs font-mono text-gray-600">
                {result.centroid_y.toFixed(1)}px
                {' '}({(result.normalized_y * 100).toFixed(1)}%)
              </span>
            </div>

            {/* Reasoning */}
            <p className="text-[10px] text-gray-400 font-mono leading-relaxed pt-1 border-t border-gray-100">
              {result.reasoning}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
