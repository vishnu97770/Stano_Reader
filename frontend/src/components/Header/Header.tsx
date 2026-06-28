import type { ConnectionStatus } from '../../types/socket';

type Route = 'write' | 'upload';

interface HeaderProps {
  connectionStatus?: ConnectionStatus;
  route?: Route;
  onNavigate?: (route: Route) => void;
}

const statusConfig: Record<ConnectionStatus, { dot: string; label: string }> = {
  connected: { dot: 'bg-green-400', label: 'Connected' },
  connecting: { dot: 'bg-yellow-400 animate-pulse', label: 'Connecting...' },
  disconnected: { dot: 'bg-gray-500', label: 'Offline' },
};

export default function Header({ connectionStatus, route, onNavigate }: HeaderProps) {
  const statusInfo = connectionStatus ? statusConfig[connectionStatus] : null;

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-gray-900 text-white flex-none">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold tracking-tight">Stano Reader</h1>
        <span className="text-xs text-gray-400 font-mono">MVP v0.1</span>
      </div>

      {onNavigate && (
        <nav className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
          <button
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              route === 'write'
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
            onClick={() => onNavigate('write')}
          >
            Write
          </button>
          <button
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              route === 'upload'
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
            onClick={() => onNavigate('upload')}
          >
            Upload
          </button>
        </nav>
      )}

      <div className="flex items-center gap-2">
        {statusInfo && (
          <>
            <div className={`w-2 h-2 rounded-full ${statusInfo.dot}`} />
            <span className="text-xs text-gray-300">{statusInfo.label}</span>
          </>
        )}
      </div>
    </header>
  );
}
