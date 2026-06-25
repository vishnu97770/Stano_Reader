import type { Outline } from '../../types/outline';

interface OutlinePanelProps {
  outline: Outline;
  isRebuilding: boolean;
}

function pct(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

function familyShort(family: string): string {
  return family.replace('_FAMILY', '');
}

export default function OutlinePanel({ outline, isRebuilding }: OutlinePanelProps) {
  const strokes = outline.recognizedStrokes;
  const symbolString = strokes.map((s) => s.symbol).join('');
  const last = strokes.length > 0 ? strokes[strokes.length - 1] : null;

  return (
    <div className="flex flex-col shrink-0 min-h-[180px] bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Current Outline
        </h2>
        {isRebuilding && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">rebuilding…</span>
        )}
      </div>

      {/* Outline text — grows with content, never clips */}
      <div className="flex-1 flex items-center justify-center px-4 py-6">
        {strokes.length === 0 && !isRebuilding ? (
          <p className="text-xs text-gray-400">Draw strokes to build the outline.</p>
        ) : (
          <p className="text-4xl font-bold leading-none font-mono tracking-widest text-gray-900 break-all text-center w-full">
            {symbolString}
          </p>
        )}
      </div>

      {/* Footer */}
      {strokes.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between shrink-0">
          <span className="text-xs text-gray-400">
            {strokes.length} {strokes.length === 1 ? 'symbol' : 'symbols'}
          </span>
          {last && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-gray-400">Last</span>
              <span className="text-[10px] text-gray-400 font-mono">{familyShort(last.family)}</span>
              <span className="text-sm font-bold font-mono text-indigo-600">{last.symbol}</span>
              <span className="text-[10px] text-gray-400 font-mono">{pct(last.confidence)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
