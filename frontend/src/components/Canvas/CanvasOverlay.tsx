interface CanvasOverlayProps {
  strokeCount: number;
}

export default function CanvasOverlay({ strokeCount }: CanvasOverlayProps) {
  return (
    <div className="absolute bottom-3 right-3 pointer-events-none select-none">
      <span className="bg-black/20 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-full">
        {strokeCount} {strokeCount === 1 ? 'stroke' : 'strokes'}
      </span>
    </div>
  );
}
