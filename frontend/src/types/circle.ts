export interface CircleResult {
  stroke_id: string;
  is_circle: boolean;
  circle_type: string | null;   // "SMALL_CIRCLE" | "LARGE_CIRCLE" | "SMALL_LOOP" | "LARGE_LOOP"
  phoneme: string | null;
  confidence: number;
  word_position: string;        // "ANY" now; future: "INITIAL" | "MEDIAL" | "FINAL"
  reasoning: string | null;
}
