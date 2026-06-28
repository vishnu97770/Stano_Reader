import type { FamilyResult, StrokeFeatures, SymbolResult, WeightResult } from '../types/analysis';
import type { CandidateResponse } from '../types/candidate';
import type { CircleResult } from '../types/circle';
import type { HookResult } from '../types/hook';
import type { LengthResult } from '../types/length';
import type { PhonemeResponse } from '../types/phoneme';
import type { SessionDetail, SessionSummary, StrokeCreatePayload } from '../types/session';
import type { StrokePoint } from '../types/stroke';
import type { TranscriptSaveResponse } from '../types/transcript';

const BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  analysis: {
    analyzeStroke: (strokeId: string, points: StrokePoint[]): Promise<StrokeFeatures> =>
      request('/api/analyze-stroke', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points }),
      }),
  },

  classify: {
    classifyFamily: (strokeId: string, points: StrokePoint[]): Promise<FamilyResult> =>
      request('/api/classify-family', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points }),
      }),

    classifySymbol: (strokeId: string, points: StrokePoint[]): Promise<SymbolResult> =>
      request('/api/classify-symbol', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points }),
      }),

    classifyWeight: (strokeId: string, points: StrokePoint[]): Promise<WeightResult> =>
      request('/api/classify-weight', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points }),
      }),
  },

  circle: {
    classify: (strokeId: string, points: StrokePoint[]): Promise<CircleResult> =>
      request('/api/classify-circle', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points }),
      }),
  },

  hook: {
    classify: (strokeId: string, points: StrokePoint[]): Promise<HookResult> =>
      request('/api/classify-hook', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points }),
      }),
  },

  length: {
    classify: (strokeId: string, points: StrokePoint[], familyName?: string): Promise<LengthResult> =>
      request('/api/classify-length', {
        method: 'POST',
        body: JSON.stringify({ stroke_id: strokeId, points, family_name: familyName ?? null }),
      }),
  },

  candidates: {
    get: (phonemes: string[], transcript: string[], maxResults = 10): Promise<CandidateResponse> =>
      request('/api/candidates', {
        method: 'POST',
        body: JSON.stringify({ phonemes, transcript, max_results: maxResults }),
      }),
  },

  phonemes: {
    map: (symbols: string[]): Promise<PhonemeResponse> =>
      request('/api/phonemes', {
        method: 'POST',
        body: JSON.stringify({ symbols }),
      }),
  },

  sessions: {
    list: (): Promise<SessionSummary[]> => request('/api/sessions'),

    create: (name: string): Promise<SessionDetail> =>
      request('/api/sessions', {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),

    get: (id: string): Promise<SessionDetail> => request(`/api/sessions/${id}`),

    saveStrokes: (
      id: string,
      strokes: StrokeCreatePayload[],
    ): Promise<{ saved: number }> =>
      request(`/api/sessions/${id}/strokes`, {
        method: 'POST',
        body: JSON.stringify({ strokes }),
      }),

    saveTranscript: (
      id: string,
      words: string[],
    ): Promise<TranscriptSaveResponse> =>
      request(`/api/sessions/${id}/transcript`, {
        method: 'PATCH',
        body: JSON.stringify({ words }),
      }),
  },
};
