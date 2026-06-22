import type { Stroke } from './stroke';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

export interface StrokePayload {
  sessionId: string;
  stroke: Stroke;
  penColor: string;
  penWidth: number;
}

export interface ServerToClientEvents {
  stroke_ack: (strokeId: string) => void;
  stroke_broadcast: (payload: StrokePayload) => void;
}

export interface ClientToServerEvents {
  stroke_data: (payload: StrokePayload) => void;
}
