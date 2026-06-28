import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Header from '../components/Header/Header';
import OfflineBanner from '../components/OfflineBanner/OfflineBanner';
import SessionBar from '../components/SessionBar/SessionBar';
import Workspace from '../components/Workspace/Workspace';
import DrawingCanvas from '../components/Canvas/DrawingCanvas';
import type { DrawingCanvasHandle } from '../components/Canvas/DrawingCanvas';
import AIPanel from '../components/AIPanel/AIPanel';
import AnalysisPanel from '../components/AnalysisPanel/AnalysisPanel';
import CandidatePanel from '../components/CandidatePanel/CandidatePanel';
import OutlinePanel from '../components/OutlinePanel/OutlinePanel';
import PhonemePanel from '../components/PhonemePanel/PhonemePanel';
import CirclePanel from '../components/CirclePanel/CirclePanel';
import HookPanel from '../components/HookPanel/HookPanel';
import LengthPanel from '../components/LengthPanel/LengthPanel';
import PhrasePanel from '../components/PhrasePanel/PhrasePanel';
import PositionPanel from '../components/PositionPanel/PositionPanel';
import SymbolPanel from '../components/SymbolPanel/SymbolPanel';
import TranscriptPanel from '../components/TranscriptPanel/TranscriptPanel';
import VowelPanel from '../components/VowelPanel/VowelPanel';
import WeightPanel from '../components/WeightPanel/WeightPanel';
import Toolbar from '../components/Toolbar/Toolbar';
import { useAIRefinement } from '../hooks/useAIRefinement';
import { useSocket } from '../hooks/useSocket';
import { useSession } from '../hooks/useSession';
import { useCandidates } from '../hooks/useCandidates';
import { useOutline } from '../hooks/useOutline';
import { usePhoneme } from '../hooks/usePhoneme';
import { useStrokeAnalysis } from '../hooks/useStrokeAnalysis';
import { useStrokeSymbol } from '../hooks/useStrokeSymbol';
import { useStrokeCircle } from '../hooks/useStrokeCircle';
import { useStrokeHook } from '../hooks/useStrokeHook';
import { useStrokeLength } from '../hooks/useStrokeLength';
import { usePhraseDetection } from '../hooks/usePhraseDetection';
import { useStrokePosition } from '../hooks/useStrokePosition';
import { useStrokeVowel } from '../hooks/useStrokeVowel';
import { useStrokeWeight } from '../hooks/useStrokeWeight';
import { useTranscript } from '../hooks/useTranscript';
import { api } from '../services/apiService';
import type { Domain } from '../types/ai';
import type { Stroke } from '../types/stroke';
import type { StrokeCreatePayload } from '../types/session';
import type { NearbyStrokeInfo, StrokeGeometry, VowelAttachment } from '../types/vowel';
import type { CandidateResult } from '../types/candidate';

// ── Pure helpers (no React dependency) ───────────────────────────────────────

function computeGeometry(points: { x: number; y: number }[]): StrokeGeometry {
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const n = points.length;
  return {
    centroid_x: xs.reduce((a, b) => a + b, 0) / n,
    centroid_y: ys.reduce((a, b) => a + b, 0) / n,
    start_x: xs[0],
    start_y: ys[0],
    end_x: xs[n - 1],
    end_y: ys[n - 1],
  };
}

function computeCentroid(points: { x: number; y: number }[]): { x: number; y: number } {
  const n = points.length;
  return {
    x: points.reduce((a, p) => a + p.x, 0) / n,
    y: points.reduce((a, p) => a + p.y, 0) / n,
  };
}

// IPA vowel → English letter patterns; used for client-side candidate boosting.
const IPA_TO_CHARS: Record<string, string[]> = {
  '/æ/':  ['a'],
  '/eɪ/': ['a', 'ai', 'ay'],
  '/ɑː/': ['a', 'ar'],
  '/ɛ/':  ['e', 'ea'],
  '/ɪ/':  ['i'],
  '/iː/': ['ee', 'ie', 'ea', 'e'],
  '/ʌ/':  ['u', 'o'],
  '/ɜː/': ['er', 'ur', 'ir', 'ear'],
  '/ɒ/':  ['o'],
  '/oʊ/': ['o', 'oa', 'ow'],
  '/ʊ/':  ['oo', 'u'],
  '/uː/': ['oo', 'u', 'ue'],
};

function boostByVowels(
  candidates: CandidateResult[],
  vowelSignals: { ipa: string }[],
): CandidateResult[] {
  if (!vowelSignals.length || !candidates.length) return candidates;
  const boosted = candidates.map((c) => {
    let boost = 0;
    const word = c.word.toLowerCase();
    for (const sig of vowelSignals) {
      const chars = IPA_TO_CHARS[sig.ipa] ?? [];
      if (chars.some((ch) => word.includes(ch))) boost += 0.05;
    }
    return { ...c, confidence: Math.min(1, Math.round((c.confidence + boost) * 10000) / 10000) };
  });
  return boosted.sort((a, b) => b.confidence - a.confidence || a.word.localeCompare(b.word));
}

// ── Component ─────────────────────────────────────────────────────────────────

type Route = 'write' | 'upload';

export default function WritingPage({ onNavigate }: { onNavigate?: (r: Route) => void } = {}) {
  const [sessionId] = useState<string>(() => crypto.randomUUID());
  const [penColor, setPenColor] = useState('#1a1a1a');
  const [penWidth, setPenWidth] = useState(2.5);
  const [showPositionGuides, setShowPositionGuides] = useState(false);

  // M17 — AI refinement settings (persisted to sessionStorage)
  const [aiEnabled, setAIEnabled] = useState(() => sessionStorage.getItem('ai_enabled') === 'true');
  const [domain, setDomain] = useState<Domain>(
    () => (sessionStorage.getItem('ai_domain') as Domain) ?? 'general',
  );

  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const { status, socketId, emitStroke, remoteStrokes } = useSocket(sessionId);
  const { features, isAnalyzing, error: analysisError, analyzeStroke } = useStrokeAnalysis();
  const { result: symbolResult, isClassifying, error: symbolError, classifySymbol } = useStrokeSymbol();
  const { result: weightResult, isClassifying: isWeightClassifying, error: weightError, classifyWeight } = useStrokeWeight();
  const { result: circleResult, isClassifying: isCircleClassifying, error: circleError, classifyCircle } = useStrokeCircle();
  const { result: hookResult, isClassifying: isHookClassifying, error: hookError, classifyHook } = useStrokeHook();
  const { result: lengthResult, isClassifying: isLengthClassifying, error: lengthError, classifyLength } = useStrokeLength();
  const { result: positionResult, isClassifying: isPositionClassifying, error: positionError, classifyPosition } = useStrokePosition();
  const { result: phraseResult, isDetecting: isPhraseDetecting, error: phraseError, detectPhrase, clearPhrase } = usePhraseDetection();
  const { result: vowelResult, isDetecting: isVowelDetecting, error: vowelError, detectVowel, clearVowel } = useStrokeVowel();
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

  // M15.5 — vowel state
  const [vowelAttachments, setVowelAttachments] = useState<Map<string, VowelAttachment[]>>(new Map());
  const [vowelHighlights, setVowelHighlights] = useState<{ x: number; y: number }[]>([]);

  // Maps strokeId → geometry for nearby-stroke lookup in vowel detection
  const strokeGeometryRef = useRef<Map<string, StrokeGeometry>>(new Map());

  // M17 — AI refinement hook
  const { aiResult, isRefining, error: aiError, refine, clear: clearAI } = useAIRefinement(aiEnabled);

  // Ref holding current AI-context params so the candidates effect can read
  // their latest values without listing them all as effect dependencies.
  const aiParamsRef = useRef({ words, outline, phonemes, vowelAttachments, phraseResult, domain, socketId });
  aiParamsRef.current = { words, outline, phonemes, vowelAttachments, phraseResult, domain, socketId };

  // Ref-track pen values so stroke callbacks always capture the current setting
  // without needing to re-create the callback on every color/width change.
  const penColorRef = useRef(penColor);
  const penWidthRef = useRef(penWidth);
  useEffect(() => { penColorRef.current = penColor; }, [penColor]);
  useEffect(() => { penWidthRef.current = penWidth; }, [penWidth]);

  // Debounce: minimum 16ms between recognition calls (60fps cap).
  const lastRecognitionTimeRef = useRef(0);

  // Ref-track outline and candidates so the stroke callback always sees the
  // latest values without being recreated on every state change.
  const outlineRef = useRef(outline);
  const candidatesRef = useRef(candidates);
  useEffect(() => { outlineRef.current = outline; }, [outline]);
  useEffect(() => { candidatesRef.current = candidates; }, [candidates]);

  // M17 — trigger AI refinement whenever candidates change (new stroke completed)
  useEffect(() => {
    if (!aiEnabled || candidates.length === 0) {
      clearAI();
      return;
    }
    const { words: w, outline: o, phonemes: p, vowelAttachments: va, phraseResult: pr, domain: d, socketId: sid } = aiParamsRef.current;
    const lastStrokeId = o.recognizedStrokes.at(-1)?.strokeId ?? 'none';
    void refine({
      strokeId: lastStrokeId,
      candidates,
      transcriptContext: w.slice(-10),
      outline: o,
      ipaSequence: p,
      domain: d,
      vowelSignals: Array.from(va.values()).flat().map((a) => a.ipa),
      phraseDetected: !!pr?.is_phrase,
      socketId: sid,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidates, aiEnabled]);

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
      const now = performance.now();
      if (now - lastRecognitionTimeRef.current < 16) return;
      lastRecognitionTimeRef.current = now;

      // Build nearby consonant descriptors from the current outline's geometry.
      const nearbyStrokes: NearbyStrokeInfo[] = outlineRef.current.recognizedStrokes
        .map((rs) => {
          const geo = strokeGeometryRef.current.get(rs.strokeId);
          if (!geo) return null;
          return { stroke_id: rs.strokeId, family: rs.family, ...geo };
        })
        .filter((x): x is NearbyStrokeInfo => x !== null);

      // Vowel detection runs first on every stroke (fast: size check only).
      const vowelRes = await detectVowel(stroke.id, stroke.points, nearbyStrokes);

      if (vowelRes?.is_vowel) {
        // This stroke is a vowel mark — track its attachment and highlight.
        if (vowelRes.attached_to_stroke_id && vowelRes.ipa) {
          const consonantId = vowelRes.attached_to_stroke_id;
          setVowelAttachments((prev) => {
            const next = new Map(prev);
            const existing = next.get(consonantId) ?? [];
            next.set(consonantId, [
              ...existing,
              {
                vowelStrokeId: stroke.id,
                ipa: vowelRes.ipa!,
                degree: vowelRes.degree ?? 2,
                position: (vowelRes.position ?? 'after') as 'before' | 'after',
              },
            ]);
            return next;
          });
        }
        const centroid = computeCentroid(stroke.points);
        setVowelHighlights((prev) => [...prev, centroid]);
        return; // Do not classify vowel marks as consonant strokes
      }

      // ── Consonant path ────────────────────────────────────────────────────
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
      void classifyLength(stroke.id, stroke.points);
      void classifyPosition(stroke.id, stroke.points, canvasRef.current?.getCanvasHeight() ?? 600);
      const symResult = await classifySymbol(stroke.id, stroke.points);
      if (symResult) {
        addStroke(symResult);
        // Store geometry for future vowel attachment lookups.
        strokeGeometryRef.current.set(stroke.id, computeGeometry(stroke.points));
      }

      // Compute projected outline families including the just-added stroke
      // (state update from addStroke is async; use refs for current values).
      const prevFamilies = outlineRef.current.recognizedStrokes.map((s) => s.family);
      const newFamilies =
        symResult && symResult.symbol !== 'UNKNOWN'
          ? [...prevFamilies, symResult.family]
          : prevFamilies;
      void detectPhrase(stroke.id, newFamilies, candidatesRef.current.map((c) => c.word));
    },
    [emitStroke, analyzeStroke, classifySymbol, classifyWeight, classifyCircle, classifyHook, classifyLength, classifyPosition, addStroke, detectPhrase, detectVowel],
  );

  // M17 — AI settings handlers (persist to sessionStorage)
  const handleToggleAI = useCallback((enabled: boolean) => {
    setAIEnabled(enabled);
    sessionStorage.setItem('ai_enabled', String(enabled));
    if (!enabled) clearAI();
  }, [clearAI]);

  const handleDomainChange = useCallback((d: Domain) => {
    setDomain(d);
    sessionStorage.setItem('ai_domain', d);
  }, []);

  // ── Candidate display: vowel boosting + AI re-ranking + phrase injection ───
  const displayCandidates = useMemo(() => {
    const vowelSignals = Array.from(vowelAttachments.values())
      .flat()
      .map((va) => ({ ipa: va.ipa }));
    const boosted = boostByVowels(candidates, vowelSignals);

    // Apply AI re-ranking when a valid (non-fallback) result is available
    let ranked: CandidateResult[] = boosted;
    if (
      aiEnabled &&
      aiResult !== null &&
      !aiResult.fallback_used &&
      aiResult.refined_ranking.length > 0
    ) {
      const rankMap = new Map(aiResult.refined_ranking.map((w, i) => [w, i]));
      ranked = [...boosted].sort((a, b) => {
        const ra = rankMap.get(a.word) ?? 9999;
        const rb = rankMap.get(b.word) ?? 9999;
        return ra !== rb ? ra - rb : b.confidence - a.confidence;
      });
      // Tag the AI-promoted candidate with ✦ indicator
      if (aiResult.promoted_candidate) {
        ranked = ranked.map((c) =>
          c.word === aiResult.promoted_candidate
            ? { ...c, reasoning: `✦ AI: ${aiResult.reasoning || 'context re-ranked'}` }
            : c,
        );
      }
    }

    if (phraseResult?.is_phrase && phraseResult.phrase_text) {
      return [
        {
          word: `[PHRASE] ${phraseResult.phrase_text}`,
          confidence: phraseResult.confidence,
          reasoning: 'Phraseography match',
        },
        ...ranked,
      ];
    }
    return ranked;
  }, [phraseResult, candidates, vowelAttachments, aiEnabled, aiResult]);

  // ── Vowel state reset ─────────────────────────────────────────────────────
  const clearVowelState = useCallback(() => {
    clearVowel();
    setVowelAttachments(new Map());
    setVowelHighlights([]);
    strokeGeometryRef.current.clear();
  }, [clearVowel]);

  // ── Candidate selection: append word, clear outline ───────────────────────
  const handleSelectCandidate = useCallback(
    (word: string) => {
      const transcriptWord = word.startsWith('[PHRASE] ') ? word.slice(9) : word;
      appendWord(transcriptWord);
      clearOutline();
      clearPhrase();
      clearVowelState();
      clearAI();
    },
    [appendWord, clearOutline, clearPhrase, clearVowelState, clearAI],
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
    clearPhrase();
    clearVowelState();
    clearAI();
  }, [startNewSession, clearOutline, clearTranscript, clearPhrase, clearVowelState, clearAI]);

  const handleClear = useCallback(() => {
    canvasRef.current?.clear();
    pendingStrokes.current = [];
    clearOutline();
    clearPhrase();
    clearVowelState();
    clearAI();
  }, [clearOutline, clearPhrase, clearVowelState, clearAI]);

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden">
      <Header connectionStatus={status} route="write" onNavigate={onNavigate} />
      <OfflineBanner />

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
            showPositionGuides={showPositionGuides}
            vowelHighlights={vowelHighlights}
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
              candidates={displayCandidates}
              isLoading={isCandidateLoading}
              error={candidateError}
              onSelect={handleSelectCandidate}
            />
            <AIPanel
              result={aiResult}
              isRefining={isRefining}
              error={aiError}
              enabled={aiEnabled}
              domain={domain}
              onToggle={handleToggleAI}
              onDomainChange={handleDomainChange}
            />
            <PhrasePanel
              result={phraseResult}
              isDetecting={isPhraseDetecting}
              error={phraseError}
            />
            <VowelPanel
              result={vowelResult}
              isDetecting={isVowelDetecting}
              error={vowelError}
              attachments={vowelAttachments}
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
            <LengthPanel
              result={lengthResult}
              isClassifying={isLengthClassifying}
              error={lengthError}
            />
            <PositionPanel
              result={positionResult}
              isClassifying={isPositionClassifying}
              error={positionError}
              showGuides={showPositionGuides}
              onToggleGuides={() => setShowPositionGuides((v) => !v)}
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
