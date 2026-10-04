'use client';

import React from 'react';

interface NDAPreviewProps {
  // Keys must match the template's coverpage_link field names
  // (e.g. "Purpose", "Effective Date"), not the form's camelCase keys.
  values: Record<string, string | undefined>;
  template: string;
}

export function NDAPreview({ values, template }: NDAPreviewProps) {
  const renderContent = () => {
    let content = template;

    // Replace fields with values
    Object.entries(values).forEach(([key, value]) => {
      if (value) {
        const pattern = new RegExp(`<span class="coverpage_link">${key}</span>`, 'g');
        content = content.replace(pattern, String(value));
      }
    });

    return content;
  };

  const parseMarkdown = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, index) => {
      if (line.startsWith('# ')) {
        return (
          <h1 key={index} className="text-2xl font-bold mt-4 mb-3">
            {line.replace(/^# /, '')}
          </h1>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={index} className="text-xl font-bold mt-3 mb-2">
            {line.replace(/^## /, '')}
          </h2>
        );
      }
      if (line.startsWith('- ')) {
        return (
          <li key={index} className="ml-6">
            {line.replace(/^- /, '')}
          </li>
        );
      }
      if (line.trim() === '') {
        return <div key={index} className="h-2" />;
      }
      return (
        <p key={index} className="mb-2 text-justify">
          {line}
        </p>
      );
    });
  };

  return (
    <div className="nda-document border border-gray-200 rounded-lg overflow-y-auto max-h-96 bg-white">
      {parseMarkdown(renderContent())}
    </div>
  );
}
