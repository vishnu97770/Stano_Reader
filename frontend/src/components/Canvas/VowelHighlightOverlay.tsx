interface VowelHighlight {
  x: number;
  y: number;
}

interface VowelHighlightOverlayProps {
  highlights: VowelHighlight[];
}

export default function VowelHighlightOverlay({ highlights }: VowelHighlightOverlayProps) {
  if (highlights.length === 0) return null;

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      aria-hidden="true"
    >
      {highlights.map((h, i) => (
        <circle
          key={i}
          cx={h.x}
          cy={h.y}
          r={14}
          fill="rgba(99, 102, 241, 0.12)"
          stroke="rgba(99, 102, 241, 0.45)"
          strokeWidth={1.5}
        />
      ))}
    </svg>
  );
}
