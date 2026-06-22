import type { SessionDetail, SessionSummary, StrokeCreatePayload } from '../types/session';

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
  },
};
