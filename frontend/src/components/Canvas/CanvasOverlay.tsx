interface CanvasOverlayProps {
  localCount: number;
  remoteCount: number;
}

export default function CanvasOverlay({ localCount, remoteCount }: CanvasOverlayProps) {
  const total = localCount + remoteCount;

  return (
    <div className="absolute bottom-3 right-3 pointer-events-none select-none flex flex-col items-end gap-1">
      <span className="bg-black/20 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-full">
        {total} {total === 1 ? 'stroke' : 'strokes'}
      </span>
      {remoteCount > 0 && (
        <span className="bg-indigo-500/70 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-full">
          {remoteCount} remote
        </span>
      )}
    </div>
  );
}
