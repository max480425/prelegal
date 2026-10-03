'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export function useDownload() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadPDF = async (downloadUrl: string, filename: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await apiClient.downloadPDF(downloadUrl, filename);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to download PDF';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    downloadPDF,
    isLoading,
    error,
  };
}
