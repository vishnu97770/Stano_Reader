import { useOnlineStatus } from '../../hooks/useOnlineStatus';

export default function OfflineBanner() {
  const isOnline = useOnlineStatus();

  if (isOnline) return null;

  return (
    <div className="w-full bg-amber-500 text-white text-center text-sm font-medium py-1.5 px-4 shrink-0">
      You are offline — recognition still works, but session sync is paused.
    </div>
  );
}
