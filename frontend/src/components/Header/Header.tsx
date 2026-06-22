import type { ConnectionStatus } from '../../types/socket';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
}

const statusConfig: Record<ConnectionStatus, { dot: string; label: string }> = {
  connected: { dot: 'bg-green-400', label: 'Connected' },
  connecting: { dot: 'bg-yellow-400 animate-pulse', label: 'Connecting...' },
  disconnected: { dot: 'bg-gray-500', label: 'Offline' },
};

export default function Header({ connectionStatus }: HeaderProps) {
  const { dot, label } = statusConfig[connectionStatus];

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-gray-900 text-white flex-none">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold tracking-tight">Stano Reader</h1>
        <span className="text-xs text-gray-400 font-mono">MVP v0.1</span>
      </div>

      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${dot}`} />
        <span className="text-xs text-gray-300">{label}</span>
      </div>
    </header>
  );
}
