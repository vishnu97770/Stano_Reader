import type { ImageProcessResult, ImageStrokeResult } from '../../types/image';

interface ImageResultPanelProps {
  result: ImageProcessResult | null;
  isProcessing: boolean;
  error: string | null;
  selectedStrokeId: string | null;
  onSelectStroke: (id: string) => void;
}

function confidenceColor(c: number) {
  if (c >= 0.85) return 'text-emerald-600';
  if (c >= 0.6) return 'text-indigo-600';
  return 'text-gray-400';
}

function StrokeRow({ row, index, selected, onClick }: {
  row: ImageStrokeResult;
  index: number;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <tr
      className={`cursor-pointer transition-colors ${selected ? 'bg-orange-50' : 'hover:bg-gray-50'}`}
      onClick={onClick}
    >
      <td className="px-2 py-1 text-xs text-gray-400 tabular-nums">{index + 1}</td>
      <td className="px-2 py-1 text-xs font-mono font-bold text-gray-900">{row.symbol}</td>
      <td className="px-2 py-1 text-[10px] text-gray-500">{row.family.replace('_FAMILY', '')}</td>
      <td className={`px-2 py-1 text-[10px] font-mono font-semibold tabular-nums ${confidenceColor(row.confidence)}`}>
        {Math.round(row.confidence * 100)}%
      </td>
      <td className="px-2 py-1 text-[10px] text-gray-400">{row.position}</td>
    </tr>
  );
}

export default function ImageResultPanel({
  result,
  isProcessing,
  error,
  selectedStrokeId,
  onSelectStroke,
}: ImageResultPanelProps) {
  return (
    <div className="flex flex-col shrink-0 bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Recognition Results
        </h2>
        {isProcessing && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">processing…</span>
        )}
      </div>

      <div className="px-4 py-3 space-y-4">
        {error && <p className="text-xs text-red-500">{error}</p>}

        {!error && !result && !isProcessing && (
          <p className="text-xs text-gray-400">Upload and process an image to see results.</p>
        )}

        {result && (
          <>
            {/* Stroke table */}
            {result.stroke_results.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="px-2 py-1 text-left text-[10px] text-gray-400 uppercase">#</th>
                      <th className="px-2 py-1 text-left text-[10px] text-gray-400 uppercase">Symbol</th>
                      <th className="px-2 py-1 text-left text-[10px] text-gray-400 uppercase">Family</th>
                      <th className="px-2 py-1 text-left text-[10px] text-gray-400 uppercase">Conf.</th>
                      <th className="px-2 py-1 text-left text-[10px] text-gray-400 uppercase">Pos.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.stroke_results.map((row, i) => (
                      <StrokeRow
                        key={row.stroke_id}
                        row={row}
                        index={i}
                        selected={row.stroke_id === selectedStrokeId}
                        onClick={() => onSelectStroke(row.stroke_id)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Phonemes */}
            {result.phonemes.length > 0 && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Phonemes</p>
                <div className="flex flex-wrap gap-1">
                  {result.phonemes.map((ph, i) => (
                    <span key={i} className="text-xs font-mono px-1.5 py-0.5 bg-gray-100 rounded text-gray-700">
                      {ph}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Phrase */}
            {result.phrase_text && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Phrase</p>
                <span className="text-sm font-semibold text-gray-900">{result.phrase_text}</span>
                <span className="ml-2 text-xs text-emerald-600 font-mono">
                  {Math.round(result.phrase_confidence * 100)}%
                </span>
              </div>
            )}

            {/* Candidates */}
            {result.candidates.length > 0 && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Top candidates</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.candidates.slice(0, 8).map((c) => (
                    <span
                      key={c.word}
                      className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded font-medium"
                    >
                      {c.word}
                      <span className="ml-1 text-[10px] text-indigo-400 font-mono">
                        {Math.round(c.confidence * 100)}%
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.stroke_results.length === 0 && (
              <p className="text-xs text-gray-400">No strokes were recognised in this image.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
