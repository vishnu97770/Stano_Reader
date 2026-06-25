import { useRef, useCallback, useState, useEffect } from 'react';
import type { RefObject } from 'react';
import type { Stroke, StrokePoint } from '../types/stroke';
import type { StrokeRecord } from '../types/session';
import { drawStrokeOnContext } from '../utils/drawStroke';

interface UseCanvasOptions {
  penColor: string;
  penWidth: number;
  onStrokeComplete: (stroke: Stroke) => void;
}

interface UseCanvasReturn {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  strokes: Stroke[];
  startStroke: (e: PointerEvent) => void;
  continueStroke: (e: PointerEvent) => void;
  endStroke: () => void;
  clearCanvas: () => void;
  drawRemoteStroke: (stroke: Stroke, penColor: string, penWidth: number) => void;
  loadStrokes: (strokes: StrokeRecord[]) => void;
}

export function useCanvas({
  penColor,
  penWidth,
  onStrokeComplete,
}: UseCanvasOptions): UseCanvasReturn {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawingRef = useRef(false);
  const currentPointsRef = useRef<StrokePoint[]>([]);
  const currentStrokeIdRef = useRef<string>('');
  const [strokes, setStrokes] = useState<Stroke[]>([]);

  // Keep onStrokeComplete stable in a ref so endStroke never goes stale
  const onStrokeCompleteRef = useRef(onStrokeComplete);
  useEffect(() => {
    onStrokeCompleteRef.current = onStrokeComplete;
  }, [onStrokeComplete]);

  const applyStyle = useCallback(
    (ctx: CanvasRenderingContext2D) => {
      ctx.strokeStyle = penColor;
      ctx.lineWidth = penWidth;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    },
    [penColor, penWidth],
  );

  const getContext = useCallback((): CanvasRenderingContext2D | null => {
    const ctx = canvasRef.current?.getContext('2d') ?? null;
    if (ctx) applyStyle(ctx);
    return ctx;
  }, [applyStyle]);

  // Returns coordinates and pressure in CSS pixel space.
  // e.pressure is normalized [0, 1] by the browser:
  //   mouse   → 0.5 when button pressed (W3C spec mandated default)
  //   stylus  → real hardware pressure
  //   touch   → 0.5 if device doesn't report force, otherwise real value
  const getPoint = useCallback((e: PointerEvent): StrokePoint => {
    const rect = canvasRef.current!.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      pressure: e.pressure,
      timestamp: Date.now(),
    };
  }, []);

  const startStroke = useCallback(
    (e: PointerEvent) => {
      const ctx = getContext();
      if (!ctx) return;

      isDrawingRef.current = true;
      currentStrokeIdRef.current = crypto.randomUUID();
      const point = getPoint(e);
      currentPointsRef.current = [point];

      ctx.beginPath();
      ctx.moveTo(point.x, point.y);
    },
    [getContext, getPoint],
  );

  const continueStroke = useCallback(
    (e: PointerEvent) => {
      if (!isDrawingRef.current) return;
      const ctx = getContext();
      if (!ctx) return;

      const point = getPoint(e);
      currentPointsRef.current.push(point);

      ctx.lineTo(point.x, point.y);
      ctx.stroke();
    },
    [getContext, getPoint],
  );

  const endStroke = useCallback(() => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;

    const points = [...currentPointsRef.current];
    currentPointsRef.current = [];

    if (points.length === 0) return;

    const stroke: Stroke = {
      id: currentStrokeIdRef.current,
      points,
    };

    setStrokes((prev) => [...prev, stroke]);
    onStrokeCompleteRef.current(stroke);
  }, []);

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setStrokes([]);
  }, []);

  const drawRemoteStroke = useCallback(
    (stroke: Stroke, penColor: string, penWidth: number) => {
      const ctx = canvasRef.current?.getContext('2d') ?? null;
      if (!ctx) return;
      drawStrokeOnContext(ctx, stroke, penColor, penWidth);
    },
    [],
  );

  // Clear the canvas and replay a set of persisted strokes loaded from the backend.
  const loadStrokes = useCallback((records: StrokeRecord[]) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setStrokes([]);

    records.forEach((r) => {
      drawStrokeOnContext(
        ctx,
        { id: r.id, points: r.points },
        r.pen_color,
        r.pen_width,
      );
    });
  }, []);

  return { canvasRef, strokes, startStroke, continueStroke, endStroke, clearCanvas, drawRemoteStroke, loadStrokes };
}
