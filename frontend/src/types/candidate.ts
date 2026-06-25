export interface CandidateResult {
  word: string;
  confidence: number;
  reasoning: string | null;
}

export interface CandidateResponse {
  candidates: CandidateResult[];
  query: string[];
}
