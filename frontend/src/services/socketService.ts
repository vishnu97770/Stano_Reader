import { io, type Socket } from 'socket.io-client';
import type { ServerToClientEvents, ClientToServerEvents } from '../types/socket';

const SOCKET_URL = (import.meta.env.VITE_SOCKET_URL as string | undefined) ?? 'http://localhost:8000';

type AppSocket = Socket<ServerToClientEvents, ClientToServerEvents>;

let socket: AppSocket | null = null;

export function getSocket(): AppSocket {
  if (!socket) {
    socket = io(SOCKET_URL, {
      autoConnect: false,
      transports: ['websocket'],
    });
  }
  return socket;
}

export function getSocketId(): string | undefined {
  return socket?.id;
}

export function disconnectSocket(): void {
  socket?.disconnect();
  socket = null;
}
