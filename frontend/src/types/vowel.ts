export interface NearbyStrokeInfo {
  stroke_id: string;
  family: string;
  centroid_x: number;
  centroid_y: number;
  start_x: number;
  start_y: number;
  end_x: number;
  end_y: number;
}

export interface VowelResult {
  stroke_id: string;
  is_vowel: boolean;
  vowel_symbol: string | null;
  ipa: string | null;
  degree: number | null;
  position: string | null;
  attached_to_stroke_id: string | null;
  detected: boolean;
  confidence: number;
  reasoning: string;
  alternatives: unknown[];
}

export interface VowelAttachment {
  vowelStrokeId: string;
  ipa: string;
  degree: number;
  position: 'before' | 'after';
}

export interface StrokeGeometry {
  centroid_x: number;
  centroid_y: number;
  start_x: number;
  start_y: number;
  end_x: number;
  end_y: number;
}
