export interface RecognizedStroke {
  strokeId: string;
  symbol: string;
  family: string;
  confidence: number;
  timestamp: number;
}

export interface Outline {
  id: string;
  recognizedStrokes: RecognizedStroke[];
  createdAt: number;
}
