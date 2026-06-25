export interface CandidateResult {
  word: string;
  confidence: number;
}

export interface CandidateResponse {
  candidates: CandidateResult[];
  query: string[];
}
