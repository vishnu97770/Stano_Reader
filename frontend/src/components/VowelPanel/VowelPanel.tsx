import type { VowelAttachment, VowelResult } from '../../types/vowel';

interface VowelPanelProps {
  result: VowelResult | null;
  isDetecting: boolean;
  error: string | null;
  attachments: Map<string, VowelAttachment[]>;
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.85) return 'text-emerald-600';
  if (confidence >= 0.65) return 'text-indigo-600';
  return 'text-gray-500';
}

function degreeName(degree: number): string {
  if (degree === 1) return '1st (start)';
  if (degree === 2) return '2nd (mid)';
  return '3rd (end)';
}

export default function VowelPanel({ result, isDetecting, error, attachments }: VowelPanelProps) {
  const detected = result?.is_vowel === true;
  const totalAttached = Array.from(attachments.values()).reduce((n, arr) => n + arr.length, 0);

  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2 shrink-0">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Vowel Signs
        </h2>
        {isDetecting && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">detecting…</span>
        )}
        {!isDetecting && totalAttached > 0 && (
          <span className="ml-auto text-[10px] text-emerald-600 font-medium">
            {totalAttached} vowel{totalAttached > 1 ? 's' : ''} active
          </span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3 space-y-2">
        {error && <p className="text-xs text-red-500">{error}</p>}

        {!error && !isDetecting && !detected && totalAttached === 0 && (
          <p className="text-xs text-gray-400">No vowel sign detected.</p>
        )}

        {/* Most-recently detected vowel */}
        {!error && detected && result && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">Sign</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-900 font-mono">
                  {result.ipa}
                </span>
                <span className={`text-xs font-mono font-semibold ${confidenceColor(result.confidence)}`}>
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">Symbol</span>
              <span className="text-xs text-gray-700 font-mono">{result.vowel_symbol}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">Degree</span>
              <span className="text-xs text-gray-700">
                {result.degree !== null ? degreeName(result.degree) : '—'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-20 shrink-0 uppercase tracking-wide">Position</span>
              <span className="text-xs text-gray-700 capitalize">{result.position ?? '—'}</span>
            </div>

            {result.reasoning && (
              <p className="text-[10px] text-gray-400 font-mono leading-relaxed pt-1 border-t border-gray-100">
                {result.reasoning}
              </p>
            )}
          </div>
        )}

        {/* Accumulated vowel attachments summary */}
        {totalAttached > 0 && (
          <div className="pt-2 border-t border-gray-100">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Attached to outline</p>
            <div className="flex flex-wrap gap-1">
              {Array.from(attachments.values())
                .flat()
                .map((va, i) => (
                  <span
                    key={i}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 font-mono font-medium"
                  >
                    {va.ipa} d{va.degree}{va.position === 'before' ? '←' : '→'}
                  </span>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
