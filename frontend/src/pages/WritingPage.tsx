import { useCallback, useEffect, useRef, useState } from 'react';
import Header from '../components/Header/Header';
import SessionBar from '../components/SessionBar/SessionBar';
import Workspace from '../components/Workspace/Workspace';
import DrawingCanvas from '../components/Canvas/DrawingCanvas';
import type { DrawingCanvasHandle } from '../components/Canvas/DrawingCanvas';
import AnalysisPanel from '../components/AnalysisPanel/AnalysisPanel';
import SymbolPanel from '../components/SymbolPanel/SymbolPanel';
import Toolbar from '../components/Toolbar/Toolbar';
import { useSocket } from '../hooks/useSocket';
import { useSession } from '../hooks/useSession';
import { useStrokeAnalysis } from '../hooks/useStrokeAnalysis';
import { useStrokeSymbol } from '../hooks/useStrokeSymbol';
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
  // Using a ref avoids re-renders on every stroke.
  const pendingStrokes = useRef<StrokeCreatePayload[]>([]);

  // ── Remote stroke rendering (Milestone 2) ────────────────────────────────
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
    (stroke: Stroke) => {
      pendingStrokes.current.push({
        id: stroke.id,
        points: stroke.points,
        pen_color: penColorRef.current,
        pen_width: penWidthRef.current,
      });
      emitStroke(stroke, penColorRef.current, penWidthRef.current);
      void analyzeStroke(stroke.id, stroke.points);
      void classifySymbol(stroke.id, stroke.points);
    },
    [emitStroke, analyzeStroke, classifySymbol],
  );

  // ── Session actions ───────────────────────────────────────────────────────
  const handleSave = useCallback(
    async (name: string) => {
      if (activeSession) {
        await appendStrokes(pendingStrokes.current);
      } else {
        await createAndSave(name, pendingStrokes.current);
      }
      pendingStrokes.current = [];
    },
    [activeSession, appendStrokes, createAndSave],
  );

  const handleLoad = useCallback(
    async (id: string) => {
      const session = await loadSession(id);
      pendingStrokes.current = [];
      canvasRef.current?.loadStrokes(session.strokes);
    },
    [loadSession],
  );

  const handleNew = useCallback(() => {
    startNewSession();
    pendingStrokes.current = [];
    canvasRef.current?.clear();
  }, [startNewSession]);

  const handleClear = useCallback(() => {
    canvasRef.current?.clear();
    pendingStrokes.current = [];
  }, []);

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
            <SymbolPanel
              result={symbolResult}
              isClassifying={isClassifying}
              error={symbolError}
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
