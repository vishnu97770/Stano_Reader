import { useCallback, useState } from 'react';
import { api } from '../services/apiService';
import type { ImageUploadResult } from '../types/image';

const ACCEPTED_MIME = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_BYTES = 10 * 1024 * 1024;

export interface UseImageUploadReturn {
  uploadResult: ImageUploadResult | null;
  previewUrl: string | null;
  isUploading: boolean;
  error: string | null;
  uploadFile: (file: File) => Promise<ImageUploadResult | null>;
  reset: () => void;
}

export function useImageUpload(): UseImageUploadReturn {
  const [uploadResult, setUploadResult] = useState<ImageUploadResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File): Promise<ImageUploadResult | null> => {
    if (!ACCEPTED_MIME.has(file.type)) {
      setError(`Unsupported format: ${file.type}. Please use JPEG, PNG, or WEBP.`);
      return null;
    }
    if (file.size > MAX_BYTES) {
      setError(`File is ${(file.size / 1024 / 1024).toFixed(1)} MB. Limit is 10 MB.`);
      return null;
    }

    // Generate local preview immediately
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setError(null);
    setIsUploading(true);

    try {
      const result = await api.image.upload(file);
      setUploadResult(result);
      return result;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      return null;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const reset = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setUploadResult(null);
    setPreviewUrl(null);
    setError(null);
  }, [previewUrl]);

  return { uploadResult, previewUrl, isUploading, error, uploadFile, reset };
}
