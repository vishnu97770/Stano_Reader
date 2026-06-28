export interface ExtractedStrokePoint {
  x: number;
  y: number;
  pressure: number;
  timestamp: number;
}

export interface ExtractedStroke {
  id: string;
  points: ExtractedStrokePoint[];
}

export interface WritingZone {
  top: number;
  bottom: number;
  baseline: number;
}

export interface PageMetadata {
  canvas_width: number;
  canvas_height: number;
  writing_zones: WritingZone[];
  line_count: number;
  image_width: number;
  image_height: number;
}

export interface ImageUploadResult {
  strokes: ExtractedStroke[];
  stroke_count: number;
  page_metadata: PageMetadata;
}

export interface ImageStrokeResult {
  stroke_id: string;
  symbol: string;
  family: string;
  confidence: number;
  circle_is_circle: boolean;
  hook_is_hook: boolean;
  length_is_modified: boolean;
  position: string;
  weight: string;
}

export interface ImageCandidateResult {
  word: string;
  confidence: number;
}

export interface ImageProcessResult {
  stroke_results: ImageStrokeResult[];
  phonemes: string[];
  candidates: ImageCandidateResult[];
  phrase_text: string | null;
  phrase_confidence: number;
  transcript: string[];
}
