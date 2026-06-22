import { useEffect, useState } from 'react';
import type { SessionDetail, SessionSummary } from '../../types/session';

interface SessionBarProps {
  activeSession: SessionDetail | null;
  sessions: SessionSummary[];
  isSaving: boolean;
  isLoading: boolean;
  onSave: (name: string) => void;
  onLoad: (id: string) => void;
  onNew: () => void;
}

export default function SessionBar({
  activeSession,
  sessions,
  isSaving,
  isLoading,
  onSave,
  onLoad,
  onNew,
}: SessionBarProps) {
  const [sessionName, setSessionName] = useState('');

  // Sync name input with the active session
  useEffect(() => {
    setSessionName(activeSession?.name ?? '');
  }, [activeSession]);

  const handleSave = () => {
    onSave(sessionName.trim());
  };

  const busy = isSaving || isLoading;

  return (
    <div className="flex items-center gap-3 px-6 py-2 bg-white border-b border-gray-200 flex-none text-sm">
      {/* Session name input */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span className="text-gray-400 font-medium whitespace-nowrap">Session</span>
        <input
          type="text"
          value={sessionName}
          onChange={(e) => setSessionName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSave()}
          placeholder="Name this session..."
          disabled={busy}
          className="flex-1 min-w-0 px-2 py-1 text-sm border border-gray-200 rounded-md bg-gray-50 placeholder:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent disabled:opacity-50"
        />
      </div>

      {/* Status badge */}
      {activeSession && (
        <span className="text-xs text-green-600 font-medium whitespace-nowrap">
          ✓ Saved
        </span>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={busy}
        className="px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
      >
        {isSaving ? 'Saving…' : activeSession ? 'Save' : 'Save Session'}
      </button>

      <div className="w-px h-5 bg-gray-200" />

      {/* Session loader */}
      <select
        value=""
        onChange={(e) => {
          if (e.target.value) onLoad(e.target.value);
        }}
        disabled={busy || sessions.length === 0}
        className="px-2 py-1.5 text-sm border border-gray-200 rounded-md bg-gray-50 text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="" disabled>
          {sessions.length === 0 ? 'No saved sessions' : 'Load session…'}
        </option>
        {sessions.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name} ({s.stroke_count} stroke{s.stroke_count !== 1 ? 's' : ''})
          </option>
        ))}
      </select>

      {/* New session button */}
      <button
        onClick={onNew}
        disabled={busy}
        className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 border border-gray-200 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
      >
        New
      </button>
    </div>
  );
}
