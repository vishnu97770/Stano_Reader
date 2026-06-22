export default function OutputPanel() {
  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex-none">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Transcript
        </h2>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center gap-2">
        <p className="text-gray-400 text-sm">Recognized text will appear here.</p>
        <p className="text-gray-300 text-xs">AI recognition engine — Phase 2.</p>
      </div>
    </div>
  );
}
