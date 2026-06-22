import {
  forwardRef,
  useImperativeHandle,
  useLayoutEffect,
  useEffect,
} from 'react';
import type { Stroke } from '../../types/stroke';
import { useCanvas } from '../../hooks/useCanvas';
import CanvasOverlay from './CanvasOverlay';

interface DrawingCanvasProps {
  penColor: string;
  penWidth: number;
  remoteStrokeCount: number;
  onStrokeComplete: (stroke: Stroke) => void;
}

export interface DrawingCanvasHandle {
  clear: () => void;
  drawRemoteStroke: (stroke: Stroke, penColor: string, penWidth: number) => void;
}

const DrawingCanvas = forwardRef<DrawingCanvasHandle, DrawingCanvasProps>(
  ({ penColor, penWidth, remoteStrokeCount, onStrokeComplete }, ref) => {
    const {
      canvasRef,
      strokes,
      startStroke,
      continueStroke,
      endStroke,
      clearCanvas,
      drawRemoteStroke,
    } = useCanvas({ penColor, penWidth, onStrokeComplete });

    useImperativeHandle(
      ref,
      () => ({ clear: clearCanvas, drawRemoteStroke }),
      [clearCanvas, drawRemoteStroke],
    );

    // Size the canvas buffer to match CSS size × devicePixelRatio for sharp rendering.
    // Resizing resets the canvas context transform, so ctx.scale is reapplied each time.
    useLayoutEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.round(rect.width * dpr);
        canvas.height = Math.round(rect.height * dpr);
        const ctx = canvas.getContext('2d');
        if (ctx) ctx.scale(dpr, dpr);
      };

      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);
      return () => observer.disconnect();
    }, [canvasRef]);

    // Attach native pointer event listeners. Using native events (not React synthetic)
    // gives us access to PointerEvent.pressure and stylus properties in the future.
    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const onPointerDown = (e: PointerEvent) => {
        canvas.setPointerCapture(e.pointerId);
        startStroke(e);
      };

      canvas.addEventListener('pointerdown', onPointerDown);
      canvas.addEventListener('pointermove', continueStroke);
      canvas.addEventListener('pointerup', endStroke);
      canvas.addEventListener('pointercancel', endStroke);

      return () => {
        canvas.removeEventListener('pointerdown', onPointerDown);
        canvas.removeEventListener('pointermove', continueStroke);
        canvas.removeEventListener('pointerup', endStroke);
        canvas.removeEventListener('pointercancel', endStroke);
      };
    }, [canvasRef, startStroke, continueStroke, endStroke]);

    return (
      <div className="relative w-full h-full rounded-lg overflow-hidden bg-white border border-gray-200 shadow-inner">
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-crosshair"
          style={{ touchAction: 'none' }}
        />
        <CanvasOverlay localCount={strokes.length} remoteCount={remoteStrokeCount} />
      </div>
    );
  },
);

DrawingCanvas.displayName = 'DrawingCanvas';

export default DrawingCanvas;
