export interface PhraseMatch {
  phrase_text: string;
  confidence: number;
}

export interface PhraseResult {
  stroke_id: string;
  is_phrase: boolean;
  phrase_text: string | null;
  confidence: number;
  alternatives: PhraseMatch[];
  reasoning: string;
}
