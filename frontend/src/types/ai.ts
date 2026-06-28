export type Domain = 'general' | 'legal' | 'diplomatic' | 'parliamentary';

export const DOMAIN_LABELS: Record<Domain, string> = {
  general: 'General',
  legal: 'Legal',
  diplomatic: 'Diplomatic',
  parliamentary: 'Parliamentary',
};

export interface AICandidateInput {
  word: string;
  confidence: number;
}

export interface AIRefinementRequest {
  stroke_id: string;
  candidates: AICandidateInput[];
  transcript_context: string[];
  outline: string;
  ipa_sequence: string[];
  domain: Domain;
  vowel_signals: string[];
  phrase_detected: boolean;
  socket_id: string | null;
}

export interface AIRefinementResult {
  stroke_id: string;
  was_invoked: boolean;
  promoted_candidate: string | null;
  confidence_boost: number;
  reasoning: string;
  original_ranking: string[];
  refined_ranking: string[];
  fallback_used: boolean;
  detected: boolean;
  confidence: number;
  alternatives: unknown[];
}
