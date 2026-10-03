'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { NDAFormSchema, NDAFormValues } from '@/lib/validation';

export function useNDAForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<NDAFormValues>({
    resolver: zodResolver(NDAFormSchema),
    defaultValues: {
      purpose: '',
      effectiveDate: '',
      mndaTerm: '1 year',
      termOfConfidentiality: '3 years after termination',
      governingLaw: 'California',
      jurisdiction: '',
      partyAName: '',
      partyBName: '',
    },
  });

  const setFormError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const clearError = () => {
    setError(null);
  };

  return {
    form,
    isLoading,
    setIsLoading,
    error,
    setError: setFormError,
    clearError,
  };
}
