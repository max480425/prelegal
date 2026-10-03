'use client';

import Link from 'next/link';

export default function SuccessPage() {
  return (
    <div className="max-w-2xl mx-auto text-center py-16">
      <div className="text-6xl mb-4">✓</div>
      <h1 className="text-4xl font-bold text-green-600 mb-4">
        Document Downloaded Successfully!
      </h1>
      <p className="text-lg text-gray-600 mb-8">
        Your NDA document has been generated and downloaded.
      </p>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <p className="text-sm text-gray-700">
          <strong>Note:</strong> This document is provided as-is. Please review it carefully
          and consult with a lawyer before signing any legal documents.
        </p>
      </div>
      <Link href="/nda-creator" className="btn btn-primary">
        Create Another Document
      </Link>
    </div>
  );
}
