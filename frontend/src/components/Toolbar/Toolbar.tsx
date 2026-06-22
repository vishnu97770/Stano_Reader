const PEN_COLORS = [
  { label: 'Black', value: '#1a1a1a' },
  { label: 'Blue', value: '#1d4ed8' },
  { label: 'Red', value: '#dc2626' },
] as const;

const PEN_WIDTHS = [
  { label: 'Thin', value: 1, dot: 4 },
  { label: 'Medium', value: 2.5, dot: 7 },
  { label: 'Thick', value: 5, dot: 12 },
] as const;

interface ToolbarProps {
  penColor: string;
  penWidth: number;
  onColorChange: (color: string) => void;
  onWidthChange: (width: number) => void;
  onClear: () => void;
}

export default function Toolbar({
  penColor,
  penWidth,
  onColorChange,
  onWidthChange,
  onClear,
}: ToolbarProps) {
  return (
    <footer className="flex items-center gap-6 px-6 py-3 bg-white border-t border-gray-200 flex-none">
      {/* Color selector */}
      <div className="flex items-center gap-2.5">
        <span className="text-xs font-medium text-gray-500">Color</span>
        <div className="flex gap-1.5">
          {PEN_COLORS.map((color) => (
            <button
              key={color.value}
              title={color.label}
              onClick={() => onColorChange(color.value)}
              className={`w-6 h-6 rounded-full border-2 transition-transform focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                penColor === color.value
                  ? 'border-indigo-500 scale-110'
                  : 'border-gray-300 hover:scale-105'
              }`}
              style={{ backgroundColor: color.value }}
            />
          ))}
        </div>
      </div>

      <div className="w-px h-6 bg-gray-200" />

      {/* Width selector */}
      <div className="flex items-center gap-2.5">
        <span className="text-xs font-medium text-gray-500">Size</span>
        <div className="flex gap-1">
          {PEN_WIDTHS.map((w) => (
            <button
              key={w.value}
              title={w.label}
              onClick={() => onWidthChange(w.value)}
              className={`flex items-center justify-center w-8 h-8 rounded-md transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                penWidth === w.value
                  ? 'bg-indigo-50 ring-1 ring-indigo-400'
                  : 'hover:bg-gray-100'
              }`}
            >
              <div
                className="rounded-full bg-gray-700"
                style={{ width: w.dot, height: w.dot }}
              />
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1" />

      {/* Clear button */}
      <button
        onClick={onClear}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
        Clear
      </button>
    </footer>
  );
}
