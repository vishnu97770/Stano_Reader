import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/apiService';
import type { SessionDetail, SessionSummary, StrokeCreatePayload } from '../types/session';

interface UseSessionReturn {
  sessions: SessionSummary[];
  activeSession: SessionDetail | null;
  isSaving: boolean;
  isLoading: boolean;
  refreshSessions: () => Promise<void>;
  createAndSave: (name: string, strokes: StrokeCreatePayload[]) => Promise<SessionDetail>;
  appendStrokes: (strokes: StrokeCreatePayload[]) => Promise<void>;
  loadSession: (id: string) => Promise<SessionDetail>;
  startNewSession: () => void;
}

export function useSession(): UseSessionReturn {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const refreshSessions = useCallback(async () => {
    try {
      const data = await api.sessions.list();
      setSessions(data);
    } catch (err) {
      console.error('[useSession] failed to fetch sessions:', err);
    }
  }, []);

  useEffect(() => {
    void refreshSessions();
  }, [refreshSessions]);

  // Create a new DB session and save all pending strokes in a single round-trip.
  const createAndSave = useCallback(
    async (name: string, strokes: StrokeCreatePayload[]): Promise<SessionDetail> => {
      setIsSaving(true);
      try {
        const session = await api.sessions.create(name);
        if (strokes.length > 0) {
          await api.sessions.saveStrokes(session.id, strokes);
        }
        setActiveSession(session);
        await refreshSessions();
        return session;
      } finally {
        setIsSaving(false);
      }
    },
    [refreshSessions],
  );

  // Append new strokes to the currently active session.
  const appendStrokes = useCallback(
    async (strokes: StrokeCreatePayload[]): Promise<void> => {
      if (!activeSession || strokes.length === 0) return;
      setIsSaving(true);
      try {
        await api.sessions.saveStrokes(activeSession.id, strokes);
        await refreshSessions();
      } finally {
        setIsSaving(false);
      }
    },
    [activeSession, refreshSessions],
  );

  // Fetch a session with all its strokes from the backend.
  const loadSession = useCallback(async (id: string): Promise<SessionDetail> => {
    setIsLoading(true);
    try {
      const session = await api.sessions.get(id);
      setActiveSession(session);
      return session;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startNewSession = useCallback(() => {
    setActiveSession(null);
  }, []);

  return {
    sessions,
    activeSession,
    isSaving,
    isLoading,
    refreshSessions,
    createAndSave,
    appendStrokes,
    loadSession,
    startNewSession,
  };
}
