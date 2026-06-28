export interface LengthResult {
  stroke_id: string;
  is_modified: boolean;
  modification_type: string | null;  // "HALF" | "DOUBLE"
  added_phoneme: string | null;
  confidence: number;
  canonical_length: number;
  measured_length: number;
  length_ratio: number;
  reasoning: string | null;
}
