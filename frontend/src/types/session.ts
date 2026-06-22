import type { StrokePoint } from './stroke';

export interface SessionSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  stroke_count: number;
}

export interface StrokeRecord {
  id: string;
  session_id: string;
  points: StrokePoint[];
  pen_color: string;
  pen_width: number;
  created_at: string;
}

export interface SessionDetail {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  strokes: StrokeRecord[];
}

// Shape sent to POST /api/sessions/{id}/strokes — matches backend StrokeCreate schema
export interface StrokeCreatePayload {
  id: string;
  points: StrokePoint[];
  pen_color: string;
  pen_width: number;
}
