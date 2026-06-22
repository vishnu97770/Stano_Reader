import { useRef, useState } from 'react';
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
  const { status, emitStroke } = useSocket(sessionId);

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden">
      <Header connectionStatus={status} />

      <Workspace
        canvas={
          <DrawingCanvas
            ref={canvasRef}
            penColor={penColor}
            penWidth={penWidth}
            onStrokeComplete={emitStroke}
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
