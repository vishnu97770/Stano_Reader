export interface BoundingBox {
  min_x: number;
  max_x: number;
  min_y: number;
  max_y: number;
  width: number;
  height: number;
}

export interface StrokeFeatures {
  stroke_id: string;
  length: number;
  avg_segment_length: number;
  direction: string;
  angle: number;
  bounding_box: BoundingBox;
  point_count: number;
  avg_point_distance: number;
  is_curve: boolean;
  curvature_ratio: number;
}

// M5 — Family classification types

export interface FamilyMatch {
  family: string;
  confidence: number;
}

export interface FamilyResult {
  stroke_id: string;
  family: string;
  confidence: number;
  alternatives: FamilyMatch[];
}
