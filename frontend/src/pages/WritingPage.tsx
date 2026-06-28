import { useCallback, useEffect, useRef, useState } from 'react';
import Header from '../components/Header/Header';
import SessionBar from '../components/SessionBar/SessionBar';
import Workspace from '../components/Workspace/Workspace';
import DrawingCanvas from '../components/Canvas/DrawingCanvas';
import type { DrawingCanvasHandle } from '../components/Canvas/DrawingCanvas';
import AnalysisPanel from '../components/AnalysisPanel/AnalysisPanel';
import CandidatePanel from '../components/CandidatePanel/CandidatePanel';
import OutlinePanel from '../components/OutlinePanel/OutlinePanel';
import PhonemePanel from '../components/PhonemePanel/PhonemePanel';
import CirclePanel from '../components/CirclePanel/CirclePanel';
import HookPanel from '../components/HookPanel/HookPanel';
import SymbolPanel from '../components/SymbolPanel/SymbolPanel';
import TranscriptPanel from '../components/TranscriptPanel/TranscriptPanel';
import WeightPanel from '../components/WeightPanel/WeightPanel';
import Toolbar from '../components/Toolbar/Toolbar';
import { useSocket } from '../hooks/useSocket';
import { useSession } from '../hooks/useSession';
import { useCandidates } from '../hooks/useCandidates';
import { useOutline } from '../hooks/useOutline';
import { usePhoneme } from '../hooks/usePhoneme';
import { useStrokeAnalysis } from '../hooks/useStrokeAnalysis';
import { useStrokeSymbol } from '../hooks/useStrokeSymbol';
import { useStrokeCircle } from '../hooks/useStrokeCircle';
import { useStrokeHook } from '../hooks/useStrokeHook';
import { useStrokeWeight } from '../hooks/useStrokeWeight';
import { useTranscript } from '../hooks/useTranscript';
import { api } from '../services/apiService';
import type { Stroke } from '../types/stroke';
import type { StrokeCreatePayload } from '../types/session';

export default function WritingPage() {
  const [sessionId] = useState<string>(() => crypto.randomUUID());
  const [penColor, setPenColor] = useState('#1a1a1a');
  const [penWidth, setPenWidth] = useState(2.5);

  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const { status, emitStroke, remoteStrokes } = useSocket(sessionId);
  const { features, isAnalyzing, error: analysisError, analyzeStroke } = useStrokeAnalysis();
  const { result: symbolResult, isClassifying, error: symbolError, classifySymbol } = useStrokeSymbol();
  const { result: weightResult, isClassifying: isWeightClassifying, error: weightError, classifyWeight } = useStrokeWeight();
  const { result: circleResult, isClassifying: isCircleClassifying, error: circleError, classifyCircle } = useStrokeCircle();
  const { result: hookResult, isClassifying: isHookClassifying, error: hookError, classifyHook } = useStrokeHook();
  const { outline, isRebuilding, addStroke, clearOutline, rebuildFromStrokes } = useOutline();
  const { phonemes, isMapping, error: phonemeError } = usePhoneme(outline);
  const { words, appendWord, undoLast, clearTranscript, setTranscript } = useTranscript();
  const { candidates, isLoading: isCandidateLoading, error: candidateError } = useCandidates(phonemes, words);
  const {
    sessions,
    activeSession,
    isSaving,
    isLoading,
    createAndSave,
    appendStrokes,
    loadSession,
    startNewSession,
  } = useSession();

  // Ref-track pen values so stroke callbacks always capture the current setting
  // without needing to re-create the callback on every color/width change.
  const penColorRef = useRef(penColor);
  const penWidthRef = useRef(penWidth);
  useEffect(() => { penColorRef.current = penColor; }, [penColor]);
  useEffect(() => { penWidthRef.current = penWidth; }, [penWidth]);

  // Accumulates strokes drawn since the last Save (or Load / New).
  const pendingStrokes = useRef<StrokeCreatePayload[]>([]);

  // ── Remote stroke rendering ───────────────────────────────────────────────
  const lastRenderedRemoteRef = useRef(0);
  useEffect(() => {
    for (let i = lastRenderedRemoteRef.current; i < remoteStrokes.length; i++) {
      const { stroke, penColor: color, penWidth: width } = remoteStrokes[i];
      canvasRef.current?.drawRemoteStroke(stroke, color, width);
    }
    lastRenderedRemoteRef.current = remoteStrokes.length;
  }, [remoteStrokes]);

  // ── Stroke completion handler ─────────────────────────────────────────────
  const handleStrokeComplete = useCallback(
    async (stroke: Stroke) => {
      pendingStrokes.current.push({
        id: stroke.id,
        points: stroke.points,
        pen_color: penColorRef.current,
        pen_width: penWidthRef.current,
      });
      emitStroke(stroke, penColorRef.current, penWidthRef.current);
      void analyzeStroke(stroke.id, stroke.points);
      void classifyWeight(stroke.id, stroke.points);
      void classifyCircle(stroke.id, stroke.points);
      void classifyHook(stroke.id, stroke.points);
      const symbolResult = await classifySymbol(stroke.id, stroke.points);
      if (symbolResult) addStroke(symbolResult);
    },
    [emitStroke, analyzeStroke, classifySymbol, classifyWeight, classifyCircle, classifyHook, addStroke],
  );

  // ── Candidate selection: append word, clear outline ───────────────────────
  const handleSelectCandidate = useCallback(
    (word: string) => {
      appendWord(word);
      clearOutline();
    },
    [appendWord, clearOutline],
  );

  // ── Session actions ───────────────────────────────────────────────────────
  const handleSave = useCallback(
    async (name: string) => {
      if (activeSession) {
        await appendStrokes(pendingStrokes.current);
        await api.sessions.saveTranscript(activeSession.id, words);
      } else {
        const session = await createAndSave(name, pendingStrokes.current);
        await api.sessions.saveTranscript(session.id, words);
      }
      pendingStrokes.current = [];
    },
    [activeSession, appendStrokes, createAndSave, words],
  );

  const handleLoad = useCallback(
    async (id: string) => {
      const session = await loadSession(id);
      pendingStrokes.current = [];
      canvasRef.current?.loadStrokes(session.strokes);
      await rebuildFromStrokes(session.strokes);
      setTranscript(session.transcript ?? []);
    },
    [loadSession, rebuildFromStrokes, setTranscript],
  );

  const handleNew = useCallback(() => {
    startNewSession();
    pendingStrokes.current = [];
    canvasRef.current?.clear();
    clearOutline();
    clearTranscript();
  }, [startNewSession, clearOutline, clearTranscript]);

  const handleClear = useCallback(() => {
    canvasRef.current?.clear();
    pendingStrokes.current = [];
    clearOutline();
  }, [clearOutline]);

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden">
      <Header connectionStatus={status} />

      <SessionBar
        activeSession={activeSession}
        sessions={sessions}
        isSaving={isSaving}
        isLoading={isLoading}
        onSave={(name) => { void handleSave(name); }}
        onLoad={(id) => { void handleLoad(id); }}
        onNew={handleNew}
      />

      <Workspace
        canvas={
          <DrawingCanvas
            ref={canvasRef}
            penColor={penColor}
            penWidth={penWidth}
            remoteStrokeCount={remoteStrokes.length}
            onStrokeComplete={handleStrokeComplete}
          />
        }
        outputPanel={
          <div className="flex flex-col gap-3 h-full overflow-y-auto">
            <OutlinePanel
              outline={outline}
              isRebuilding={isRebuilding}
            />
            <PhonemePanel
              phonemes={phonemes}
              isMapping={isMapping}
              error={phonemeError}
            />
            <CandidatePanel
              candidates={candidates}
              isLoading={isCandidateLoading}
              error={candidateError}
              onSelect={handleSelectCandidate}
            />
            <TranscriptPanel
              words={words}
              onUndo={undoLast}
              onClear={clearTranscript}
            />
            <SymbolPanel
              result={symbolResult}
              isClassifying={isClassifying}
              error={symbolError}
            />
            <CirclePanel
              result={circleResult}
              isClassifying={isCircleClassifying}
              error={circleError}
            />
            <HookPanel
              result={hookResult}
              isClassifying={isHookClassifying}
              error={hookError}
            />
            <WeightPanel
              result={weightResult}
              isClassifying={isWeightClassifying}
              error={weightError}
            />
            <AnalysisPanel
              features={features}
              isAnalyzing={isAnalyzing}
              error={analysisError}
            />
          </div>
        }
      />

      <Toolbar
        penColor={penColor}
        penWidth={penWidth}
        onColorChange={setPenColor}
        onWidthChange={setPenWidth}
        onClear={handleClear}
      />
    </div>
  );
}
