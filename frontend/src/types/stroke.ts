export interface StrokePoint {
  x: number;
  y: number;
  timestamp: number;
}

export interface Stroke {
  id: string;
  points: StrokePoint[];
}
