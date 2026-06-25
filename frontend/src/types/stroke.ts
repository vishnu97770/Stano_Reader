export interface StrokePoint {
  x: number;
  y: number;
  /** Normalized pressure in [0, 1]. Mouse: 0.5 (W3C spec default). Stylus: real value. */
  pressure: number;
  timestamp: number;
  // Future stylus fields (available via PointerEvent, not yet captured):
  // tiltX?: number;   // −90 to 90, pen lean left/right
  // tiltY?: number;   // −90 to 90, pen lean front/back
  // twist?: number;   // 0–359, clockwise rotation around pen axis
}

export interface Stroke {
  id: string;
  points: StrokePoint[];
}
