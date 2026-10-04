'use client';

import { useNDAForm } from '@/hooks/useNDAForm';
import { useDownload } from '@/hooks/useDownload';
import { FormField } from './FormField';
import { NDAPreview } from '@/components/nda/NDAPreview';
import { apiClient } from '@/lib/api-client';
import { useState } from 'react';

interface NDAFormProps {
  template: string;
}

export function NDAForm({ template }: NDAFormProps) {
  const { form, isLoading, setIsLoading, error, setError, clearError } = useNDAForm();
  const { downloadPDF } = useDownload();
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(true);
  const watchValues = form.watch();

  // Map form keys to the template's coverpage_link field names (same
  // mapping used on submit) so the preview substitutes correctly.
  const previewValues: Record<string, string | undefined> = {
    Purpose: watchValues.purpose,
    'Effective Date': watchValues.effectiveDate,
    'MNDA Term': watchValues.mndaTerm,
    'Term of Confidentiality': watchValues.termOfConfidentiality,
    'Governing Law': watchValues.governingLaw,
    Jurisdiction: watchValues.jurisdiction,
  };

  const onSubmit = async (values: any) => {
    try {
      clearError();
      setIsLoading(true);
      setDownloadSuccess(false);

      const response = await apiClient.generatePDF({
        template_name: 'Mutual-NDA',
        fields: {
          Purpose: values.purpose,
          'Effective Date': values.effectiveDate,
          'MNDA Term': values.mndaTerm,
          'Term of Confidentiality': values.termOfConfidentiality,
          'Governing Law': values.governingLaw,
          Jurisdiction: values.jurisdiction,
        },
      });

      await downloadPDF(response.download_url, response.filename);
      setDownloadSuccess(true);

      setTimeout(() => setDownloadSuccess(false), 5000);
    } catch (err: any) {
      const message = err?.error || 'Failed to generate PDF';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Form Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-6">NDA Information</h2>

        <form onSubmit={form.handleSubmit(onSubmit)}>
          {/* Party Information */}
          <div className="form-section">
            <h3 className="text-lg font-semibold mb-4">Party Information</h3>
            <FormField
              label="Party A Name"
              name="partyAName"
              placeholder="Company or Individual Name"
              description="The first party to the agreement"
              register={form.register('partyAName')}
              error={form.formState.errors.partyAName?.message}
              required
            />
            <FormField
              label="Party B Name"
              name="partyBName"
              placeholder="Company or Individual Name"
              description="The second party to the agreement"
              register={form.register('partyBName')}
              error={form.formState.errors.partyBName?.message}
              required
            />
          </div>

          {/* Document Terms */}
          <div className="form-section">
            <h3 className="text-lg font-semibold mb-4">Document Terms</h3>
            <FormField
              label="Purpose"
              name="purpose"
              type="textarea"
              placeholder="e.g., Evaluation of potential business partnership"
              description="The purpose for which Confidential Information will be disclosed"
              register={form.register('purpose')}
              error={form.formState.errors.purpose?.message}
              required
            />
            <FormField
              label="Effective Date"
              name="effectiveDate"
              type="date"
              register={form.register('effectiveDate')}
              error={form.formState.errors.effectiveDate?.message}
              required
            />
            <FormField
              label="MNDA Term"
              name="mndaTerm"
              placeholder="e.g., 1 year, 2 years"
              register={form.register('mndaTerm')}
              error={form.formState.errors.mndaTerm?.message}
              required
            />
            <FormField
              label="Term of Confidentiality"
              name="termOfConfidentiality"
              placeholder="e.g., 3 years after termination"
              register={form.register('termOfConfidentiality')}
              error={form.formState.errors.termOfConfidentiality?.message}
              required
            />
          </div>

          {/* Legal Terms */}
          <div className="form-section">
            <h3 className="text-lg font-semibold mb-4">Legal Terms</h3>
            <FormField
              label="Governing Law"
              name="governingLaw"
              type="select"
              options={['California', 'New York', 'Delaware', 'Texas', 'Other']}
              register={form.register('governingLaw')}
              error={form.formState.errors.governingLaw?.message}
              required
            />
            <FormField
              label="Jurisdiction"
              name="jurisdiction"
              placeholder="e.g., California"
              register={form.register('jurisdiction')}
              error={form.formState.errors.jurisdiction?.message}
              required
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
              {error}
            </div>
          )}

          {/* Success Message */}
          {downloadSuccess && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded text-green-800 text-sm">
              ✓ PDF downloaded successfully!
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary w-full mt-6"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <div className="loading-spinner mr-2" style={{ width: '16px', height: '16px' }} />
                Generating PDF...
              </span>
            ) : (
              'Download NDA as PDF'
            )}
          </button>
        </form>
      </div>

      {/* Preview Section */}
      {previewVisible && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-4">Preview</h2>
          <NDAPreview values={previewValues} template={template} />
        </div>
      )}
    </div>
  );
}
