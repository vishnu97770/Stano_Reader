interface PositionGuidesProps {
  show: boolean;
}

export default function PositionGuides({ show }: PositionGuidesProps) {
  if (!show) return null;

  return (
    <>
      {/* FIRST / SECOND boundary at 33% */}
      <div
        className="absolute inset-x-0 pointer-events-none"
        style={{ top: '33.33%' }}
      >
        <div className="w-full border-t border-dashed border-sky-400/50" />
        <span className="absolute left-2 top-0.5 text-[9px] text-sky-500/60 select-none leading-none">
          1st / 2nd
        </span>
      </div>

      {/* SECOND / THIRD boundary at 67% */}
      <div
        className="absolute inset-x-0 pointer-events-none"
        style={{ top: '66.67%' }}
      >
        <div className="w-full border-t border-dashed border-sky-400/50" />
        <span className="absolute left-2 top-0.5 text-[9px] text-sky-500/60 select-none leading-none">
          2nd / 3rd
        </span>
      </div>
    </>
  );
}
