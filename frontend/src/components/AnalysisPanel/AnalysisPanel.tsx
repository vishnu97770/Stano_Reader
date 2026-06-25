import type { StrokeFeatures } from '../../types/analysis';

interface AnalysisPanelProps {
  features: StrokeFeatures | null;
  isAnalyzing: boolean;
  error: string | null;
}

interface RowProps {
  label: string;
  value: string | number | boolean;
}

function Row({ label, value }: RowProps) {
  return (
    <div className="flex justify-between items-baseline py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-xs text-gray-500 shrink-0 pr-2">{label}</span>
      <span className="text-xs font-mono text-gray-800 text-right truncate">
        {String(value)}
      </span>
    </div>
  );
}

export default function AnalysisPanel({ features, isAnalyzing, error }: AnalysisPanelProps) {
  return (
    <div className="flex flex-col shrink-0 bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 shrink-0 flex items-center gap-2">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Stroke Analysis
        </h2>
        {isAnalyzing && (
          <span className="ml-auto text-xs text-indigo-500 animate-pulse">analyzing…</span>
        )}
      </div>

      <div className="overflow-y-auto max-h-[260px]">
        {error && (
          <div className="m-3 px-3 py-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
            {error}
          </div>
        )}

        {!features && !isAnalyzing && !error && (
          <div className="flex flex-col items-center justify-center h-full p-6 text-center gap-2">
            <p className="text-gray-400 text-sm">Draw a stroke to see its features.</p>
          </div>
        )}

        {features && (
          <div className="px-4 py-2">
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider pt-2 pb-1">
              Geometry
            </p>
            <Row label="Length" value={`${features.length} px`} />
            <Row label="Avg segment" value={`${features.avg_segment_length} px`} />
            <Row label="Points" value={features.point_count} />
            <Row label="Direction" value={features.direction} />
            <Row label="Angle" value={`${features.angle}°`} />

            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider pt-3 pb-1">
              Bounding Box
            </p>
            <Row label="Width" value={`${features.bounding_box.width} px`} />
            <Row label="Height" value={`${features.bounding_box.height} px`} />
            <Row label="min x / max x" value={`${features.bounding_box.min_x} / ${features.bounding_box.max_x}`} />
            <Row label="min y / max y" value={`${features.bounding_box.min_y} / ${features.bounding_box.max_y}`} />

            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider pt-3 pb-1">
              Curvature
            </p>
            <Row label="Is curve" value={features.is_curve ? 'yes' : 'no'} />
            <Row label="Ratio" value={features.curvature_ratio} />

            <p className="text-[10px] text-gray-300 pt-3 pb-2 text-right font-mono truncate">
              id: {features.stroke_id.slice(0, 8)}…
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
