export interface PositionResult {
  stroke_id: string;
  position: string;       // "FIRST" | "SECOND" | "THIRD" | "UNKNOWN"
  confidence: number;
  centroid_y: number;
  normalized_y: number;
  canvas_height: number;
  reasoning: string;
}
