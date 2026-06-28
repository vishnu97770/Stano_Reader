import type { HookResult } from '../../types/hook';

interface HookPanelProps {
  result: HookResult | null;
  isClassifying: boolean;
  error: string | null;
}

function hookLabel(hookType: string): string {
  // "L_HOOK_INITIAL" → "L Hook — Initial"
  const parts = hookType.split('_');
  // parts = ["L", "HOOK", "INITIAL"] or ["FV", "HOOK", "FINAL"]
  const type = parts[0];      // "L" | "R" | "N" | "FV"
  const pos  = parts[parts.length - 1]; // "INITIAL" | "FINAL"
  return `${type} Hook — ${pos.charAt(0) + pos.slice(1).toLowerCase()}`;
}

function positionBadge(position: string): string {
  return position === 'INITIAL' ? 'bg-indigo-100 text-indigo-700' : 'bg-amber-100 text-amber-700';
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-emerald-600';
  if (confidence >= 0.5) return 'text-indigo-600';
  return 'text-gray-500';
}

export default function HookPanel({ result, isClassifying, error }: HookPanelProps) {
  const detected = result?.is_hook === true;

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Hook
        </h2>
        {isClassifying && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">detecting…</span>
        )}
        {!isClassifying && detected && (
          <span className="ml-auto text-[10px] text-emerald-600 font-medium">detected</span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {error && <p className="text-xs text-red-500">{error}</p>}

        {!error && !isClassifying && !detected && (
          <p className="text-xs text-gray-400">No hook detected.</p>
        )}

        {!error && detected && result && (
          <div className="space-y-2">
            {/* Hook type + position badge */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Type
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-900">
                  {result.hook_type ? hookLabel(result.hook_type) : '—'}
                </span>
                {result.attachment_position && (
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${positionBadge(result.attachment_position)}`}>
                    {result.attachment_position.toLowerCase()}
                  </span>
                )}
              </div>
            </div>

            {/* Phoneme */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">
                Phoneme
              </span>
              <span className="text-sm font-mono text-indigo-600">
                {result.phoneme ?? '—'}
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
