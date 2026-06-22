import { useRef, useState, useEffect } from 'react';
import Header from '../components/Header/Header';
import Workspace from '../components/Workspace/Workspace';
import DrawingCanvas from '../components/Canvas/DrawingCanvas';
import type { DrawingCanvasHandle } from '../components/Canvas/DrawingCanvas';
import OutputPanel from '../components/OutputPanel/OutputPanel';
import Toolbar from '../components/Toolbar/Toolbar';
import { useSocket } from '../hooks/useSocket';

export default function WritingPage() {
  const [sessionId] = useState<string>(() => crypto.randomUUID());
  const [penColor, setPenColor] = useState('#1a1a1a');
  const [penWidth, setPenWidth] = useState(2.5);

  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const { status, emitStroke, remoteStrokes } = useSocket(sessionId);

  // Track the index of the last remote stroke that has been rendered.
  // When remoteStrokes grows, we render only the new entries so we never
  // redraw strokes that are already on the canvas.
  const lastRenderedRemoteRef = useRef(0);

  useEffect(() => {
    for (let i = lastRenderedRemoteRef.current; i < remoteStrokes.length; i++) {
      const { stroke, penColor: color, penWidth: width } = remoteStrokes[i];
      canvasRef.current?.drawRemoteStroke(stroke, color, width);
    }
    lastRenderedRemoteRef.current = remoteStrokes.length;
  }, [remoteStrokes]);

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden">
      <Header connectionStatus={status} />

      <Workspace
        canvas={
          <DrawingCanvas
            ref={canvasRef}
            penColor={penColor}
            penWidth={penWidth}
            remoteStrokeCount={remoteStrokes.length}
            onStrokeComplete={(stroke) => emitStroke(stroke, penColor, penWidth)}
          />
        }
        outputPanel={<OutputPanel />}
      />

      <Toolbar
        penColor={penColor}
        penWidth={penWidth}
        onColorChange={setPenColor}
        onWidthChange={setPenWidth}
        onClear={() => canvasRef.current?.clear()}
      />
    </div>
  );
}
