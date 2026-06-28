import { useEffect, useState, useCallback } from 'react';
import { getSocket, disconnectSocket, getSocketId } from '../services/socketService';
import type { ConnectionStatus, StrokePayload } from '../types/socket';
import type { Stroke } from '../types/stroke';

export function useSocket(sessionId: string) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [socketId, setSocketId] = useState<string | undefined>(undefined);
  const [remoteStrokes, setRemoteStrokes] = useState<StrokePayload[]>([]);

  useEffect(() => {
    const socket = getSocket();
    setStatus('connecting');
    socket.connect();

    socket.on('connect', () => { setStatus('connected'); setSocketId(getSocketId()); });
    socket.on('disconnect', () => setStatus('disconnected'));
    socket.on('connect_error', () => setStatus('disconnected'));

    // Server broadcasts a completed stroke from another client.
    // The server uses skip_sid so this client never receives its own strokes here.
    socket.on('stroke_broadcast', (payload: StrokePayload) => {
      setRemoteStrokes((prev) => [...prev, payload]);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');
      socket.off('stroke_broadcast');
      disconnectSocket();
    };
  }, []);

  const emitStroke = useCallback(
    (stroke: Stroke, penColor: string, penWidth: number) => {
      const socket = getSocket();
      if (socket.connected) {
        socket.emit('stroke_data', { sessionId, stroke, penColor, penWidth });
      }
    },
    [sessionId],
  );

  return { status, socketId, emitStroke, remoteStrokes };
}
