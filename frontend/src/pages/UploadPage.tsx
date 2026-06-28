import { useCallback, useRef, useState } from 'react';
import Header from '../components/Header/Header';
import ProcessingView from '../components/ProcessingView/ProcessingView';
import ImageResultPanel from '../components/ImageResultPanel/ImageResultPanel';
import { useImageUpload } from '../hooks/useImageUpload';
import { useImageProcess } from '../hooks/useImageProcess';

type Route = 'write' | 'upload';

interface UploadPageProps {
  onNavigate?: (route: Route) => void;
}

const ACCEPTED_TYPES = 'image/jpeg,image/png,image/webp';

export default function UploadPage({ onNavigate }: UploadPageProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedStrokeId, setSelectedStrokeId] = useState<string | null>(null);

  const {
    uploadResult,
    previewUrl,
    isUploading,
    error: uploadError,
    uploadFile,
    reset,
  } = useImageUpload();

  const {
    processResult,
    isProcessing,
    error: processError,
    processStrokes,
    clearResult,
  } = useImageProcess();

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file) return;
      clearResult();
      setSelectedStrokeId(null);
      await uploadFile(file);
    },
    [uploadFile, clearResult],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      void handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleProcess = useCallback(async () => {
    if (!uploadResult) return;
    setSelectedStrokeId(null);
    await processStrokes(uploadResult.strokes, uploadResult.page_metadata);
  }, [uploadResult, processStrokes]);

  const handleReset = useCallback(() => {
    reset();
    clearResult();
    setSelectedStrokeId(null);
  }, [reset, clearResult]);

  const error = uploadError ?? processError;

  return (
    <div className="h-screen flex flex-col bg-gray-100 overflow-hidden">
      <Header route="upload" onNavigate={onNavigate} />

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        className="hidden"
        onChange={(e) => {
          void handleFiles(e.target.files);
          e.target.value = '';
        }}
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          void handleFiles(e.target.files);
          e.target.value = '';
        }}
      />

      <main className="flex-1 overflow-y-auto">
        {!previewUrl ? (
          /* ── Drop zone ───────────────────────────────────────────── */
          <div className="flex items-center justify-center h-full p-6">
            <div
              className={`w-full max-w-xl border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
                isDragging
                  ? 'border-indigo-400 bg-indigo-50'
                  : 'border-gray-300 bg-white'
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              <div className="mx-auto mb-4 w-12 h-12 text-gray-300">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              <p className="text-sm font-medium text-gray-700 mb-1">
                Drop a shorthand photo here
              </p>
              <p className="text-xs text-gray-400 mb-6">
                JPEG, PNG, or WEBP — max 10 MB
              </p>

              <div className="flex items-center justify-center gap-3">
                <button
                  className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Pick file
                </button>
                <button
                  className="px-4 py-2 bg-gray-700 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors"
                  onClick={() => cameraInputRef.current?.click()}
                >
                  Use camera
                </button>
              </div>

              {error && <p className="mt-4 text-xs text-red-500">{error}</p>}
            </div>
          </div>
        ) : (
          /* ── Preview + results ───────────────────────────────────── */
          <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="flex items-center gap-3 px-6 py-3 bg-white border-b border-gray-200 flex-none">
              {isUploading && (
                <span className="text-xs text-indigo-500 animate-pulse">
                  Analysing image…
                </span>
              )}
              {!isUploading && uploadResult && (
                <span className="text-xs text-gray-500">
                  {uploadResult.stroke_count} stroke
                  {uploadResult.stroke_count !== 1 ? 's' : ''} extracted
                </span>
              )}

              <div className="flex-1" />

              {error && (
                <span className="text-xs text-red-500 mr-2">{error}</span>
              )}

              <button
                disabled={!uploadResult || isProcessing || isUploading}
                className="px-4 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                onClick={() => {
                  void handleProcess();
                }}
              >
                {isProcessing ? 'Recognising…' : 'Recognise'}
              </button>

              <button
                className="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs rounded-lg hover:bg-gray-200 transition-colors"
                onClick={handleReset}
              >
                Reset
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              {/* Left: image + stroke overlay */}
              <div>
                {isUploading ? (
                  <div className="w-full aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                    <span className="text-sm text-gray-400 animate-pulse">
                      Processing image…
                    </span>
                  </div>
                ) : uploadResult ? (
                  <ProcessingView
                    previewUrl={previewUrl}
                    strokes={uploadResult.strokes}
                    page={uploadResult.page_metadata}
                    selectedStrokeId={selectedStrokeId}
                    onSelectStroke={setSelectedStrokeId}
                  />
                ) : (
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="w-full rounded-lg"
                  />
                )}
              </div>

              {/* Right: recognition results */}
              <ImageResultPanel
                result={processResult}
                isProcessing={isProcessing}
                error={processError}
                selectedStrokeId={selectedStrokeId}
                onSelectStroke={setSelectedStrokeId}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
