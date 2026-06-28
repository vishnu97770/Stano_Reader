import type { ExtractedStroke, PageMetadata } from '../../types/image';

interface ProcessingViewProps {
  previewUrl: string;
  strokes: ExtractedStroke[];
  page: PageMetadata;
  selectedStrokeId: string | null;
  onSelectStroke: (id: string) => void;
}

// Stroke colours cycle through a fixed palette so overlapping strokes are distinguishable
const PALETTE = [
  'rgba(99,102,241,0.55)',
  'rgba(16,185,129,0.55)',
  'rgba(245,158,11,0.55)',
  'rgba(239,68,68,0.55)',
  'rgba(59,130,246,0.55)',
  'rgba(168,85,247,0.55)',
];

function strokeColor(index: number, selected: boolean): string {
  if (selected) return 'rgba(251,146,60,0.85)';
  return PALETTE[index % PALETTE.length];
}

export default function ProcessingView({
  previewUrl,
  strokes,
  page,
  selectedStrokeId,
  onSelectStroke,
}: ProcessingViewProps) {
  const scaleX = 100 / (page.image_width || page.canvas_width);
  const scaleY = 100 / (page.image_height || page.canvas_height);

  return (
    <div className="relative w-full border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Uploaded image */}
      <img
        src={previewUrl}
        alt="Uploaded shorthand"
        className="w-full h-auto block"
        draggable={false}
      />

      {/* SVG overlay — coordinates are % of image dimensions */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox={`0 0 100 100`}
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {strokes.map((stroke, idx) => {
          if (stroke.points.length < 2) return null;
          const selected = stroke.id === selectedStrokeId;
          const color = strokeColor(idx, selected);

          // Build polyline points string in % coordinates
          const polyPts = stroke.points
            .map((p) => `${p.x * scaleX},${p.y * scaleY}`)
            .join(' ');

          return (
            <polyline
              key={stroke.id}
              points={polyPts}
              fill="none"
              stroke={color}
              strokeWidth={selected ? 0.7 : 0.4}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          );
        })}
      </svg>

      {/* Clickable hotspots per stroke (bounding boxes) */}
      {strokes.map((stroke, idx) => {
        if (stroke.points.length === 0) return null;
        const xs = stroke.points.map((p) => p.x * scaleX);
        const ys = stroke.points.map((p) => p.y * scaleY);
        const minX = Math.min(...xs);
        const minY = Math.min(...ys);
        const w = Math.max(1, Math.max(...xs) - minX);
        const h = Math.max(1, Math.max(...ys) - minY);
        const selected = stroke.id === selectedStrokeId;

        return (
          <div
            key={`hotspot-${stroke.id}`}
            className="absolute cursor-pointer"
            style={{
              left: `${minX}%`,
              top: `${minY}%`,
              width: `${w}%`,
              height: `${h}%`,
              border: selected ? '2px solid rgba(251,146,60,0.9)' : '1px solid transparent',
              borderRadius: 2,
              backgroundColor: selected ? 'rgba(251,146,60,0.08)' : 'transparent',
            }}
            title={`Stroke ${idx + 1}`}
            onClick={() => onSelectStroke(stroke.id)}
          />
        );
      })}
    </div>
  );
}
