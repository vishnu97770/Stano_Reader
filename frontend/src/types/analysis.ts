// M7 — Pressure types

export interface PressureStats {
  avg_pressure: number;
  max_pressure: number;
  variance: number;
  sample_count: number;
}

export interface WeightResult {
  stroke_id: string;
  weight: 'LIGHT' | 'HEAVY' | 'AMBIGUOUS';
  avg_pressure: number;
  max_pressure: number;
  variance: number;
  threshold_light: number;
  threshold_heavy: number;
}

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
  pressure_stats: PressureStats | null;
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

// M6 — Exact symbol classification types

export interface SymbolMatch {
  symbol: string;
  confidence: number;
}

export interface SymbolResult {
  stroke_id: string;
  family: string;
  family_confidence: number;
  symbol: string;
  confidence: number;
  alternatives: SymbolMatch[];
  thickness_missing: boolean;
  reason: string | null;
}
