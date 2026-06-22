import { useEffect, useState, useCallback } from 'react';
import { getSocket, disconnectSocket } from '../services/socketService';
import type { ConnectionStatus } from '../types/socket';
import type { Stroke } from '../types/stroke';

export function useSocket(sessionId: string) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');

  useEffect(() => {
    const socket = getSocket();
    setStatus('connecting');
    socket.connect();

    socket.on('connect', () => setStatus('connected'));
    socket.on('disconnect', () => setStatus('disconnected'));
    socket.on('connect_error', () => setStatus('disconnected'));

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');
      disconnectSocket();
    };
  }, []);

  const emitStroke = useCallback(
    (stroke: Stroke) => {
      const socket = getSocket();
      if (socket.connected) {
        socket.emit('stroke_data', { sessionId, stroke });
      }
    },
    [sessionId],
  );

  return { status, emitStroke };
}
