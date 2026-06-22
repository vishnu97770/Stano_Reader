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
