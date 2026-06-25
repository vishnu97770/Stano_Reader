import type { CandidateResult } from '../../types/candidate';

interface CandidatePanelProps {
  candidates: CandidateResult[];
  isLoading: boolean;
  error: string | null;
}

function pct(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'bg-emerald-400';
  if (confidence >= 0.5) return 'bg-indigo-400';
  return 'bg-gray-300';
}

export default function CandidatePanel({ candidates, isLoading, error }: CandidatePanelProps) {
  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Word Candidates
        </h2>
        {isLoading && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">searching…</span>
        )}
        {!isLoading && candidates.length > 0 && (
          <span className="ml-auto text-[10px] text-gray-400 font-mono">
            {candidates.length} {candidates.length === 1 ? 'match' : 'matches'}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {error && (
          <p className="text-xs text-red-500">{error}</p>
        )}

        {!error && candidates.length === 0 && !isLoading && (
          <p className="text-xs text-gray-400">Candidates appear as you draw.</p>
        )}

        {candidates.length > 0 && (
          <ol className="space-y-2">
            {candidates.map((c, index) => (
              <li key={c.word} className="flex items-center gap-3">
                {/* Rank */}
                <span className="text-[10px] text-gray-400 font-mono w-4 shrink-0 text-right">
                  {index + 1}.
                </span>

                {/* Word */}
                <span className="text-sm font-semibold text-gray-900 w-24 shrink-0 truncate">
                  {c.word}
                </span>

                {/* Confidence bar */}
                <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${confidenceColor(c.confidence)}`}
                    style={{ width: pct(c.confidence) }}
                  />
                </div>

                {/* Confidence label */}
                <span className="text-[10px] font-mono text-gray-400 w-8 text-right shrink-0">
                  {pct(c.confidence)}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
