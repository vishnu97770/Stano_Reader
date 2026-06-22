import type { Stroke } from '../types/stroke';

/**
 * Draws a complete stroke onto an existing canvas context.
 * Uses ctx.save/restore so caller's context state is not mutated.
 * Coordinates are in CSS pixel space (DPR scaling is handled by the canvas setup).
 */
export function drawStrokeOnContext(
  ctx: CanvasRenderingContext2D,
  stroke: Stroke,
  penColor: string,
  penWidth: number,
): void {
  if (stroke.points.length === 0) return;

  ctx.save();

  ctx.strokeStyle = penColor;
  ctx.lineWidth = penWidth;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  ctx.beginPath();
  ctx.moveTo(stroke.points[0].x, stroke.points[0].y);

  for (let i = 1; i < stroke.points.length; i++) {
    ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
  }

  ctx.stroke();
  ctx.restore();
}
