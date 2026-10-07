'use client';

import React, { useEffect, useRef, useState } from 'react';
import { NDAPreview } from '@/components/nda/NDAPreview';
import { useDownload } from '@/hooks/useDownload';
import { apiClient } from '@/lib/api-client';
import { ChatMessage } from '@/lib/types';

interface NDAChatProps {
  template: string;
}

// Shown only if GET /greeting itself fails, so the panel is never empty.
const FALLBACK_GREETING =
  "Hi! I'll help you put together a Mutual NDA. What is the purpose of sharing confidential information between the parties?";

export function NDAChat({ template }: NDAChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [complete, setComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  // Gating flag: the input stays disabled until the greeting settles, so a
  // slow greeting can never interleave with (and clobber) the first turn.
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [input, setInput] = useState('');
  const { downloadPDF } = useDownload();
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getChatGreeting()
      .then((greeting) => {
        if (cancelled) return;
        setMessages([{ role: 'assistant', content: greeting.reply }]);
        setFields(greeting.fields);
        setComplete(greeting.complete);
      })
      .catch((err) => {
        if (cancelled) return;
        setMessages([{ role: 'assistant', content: FALLBACK_GREETING }]);
        setError(err?.error || 'Could not reach the AI service.');
      })
      .finally(() => {
        if (!cancelled) setIsReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [messages, isLoading]);

  const send = async () => {
    const text = input.trim();
    if (!text || isLoading || !isReady) return;
    const userMessage: ChatMessage = { role: 'user', content: text };
    const nextMessages = [...messages, userMessage];

    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.sendChatMessage(nextMessages, fields);
      setMessages([...nextMessages, { role: 'assistant', content: response.reply }]);
      // The server always returns every field fully merged — trust the
      // contract instead of re-implementing the merge here.
      setFields(response.fields);
      setComplete(response.complete);
      setInput(''); // only clear the input once the turn actually succeeded
    } catch (err: any) {
      // Keep `messages` untouched so the text still in the input can be
      // re-sent verbatim — nothing the user typed is lost on failure.
      setError(err?.error || 'The AI service is unavailable. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      setDownloadError(null);
      const response = await apiClient.generatePDF({
        template_name: 'Mutual-NDA',
        fields,
      });
      await downloadPDF(response.download_url, response.filename);
      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 5000);
    } catch (err: any) {
      setDownloadError(err?.error || 'Failed to generate PDF');
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Chat Section */}
      <div className="bg-white rounded-lg shadow p-6 flex flex-col">
        <h2 className="text-2xl font-bold mb-4 text-[#032147]">Chat with your AI paralegal</h2>

        <div
          ref={listRef}
          className="h-96 overflow-y-auto space-y-3 p-2 mb-4"
          aria-live="polite"
        >
          {!isReady && (
            <div className="flex items-center justify-center h-full">
              <div className="loading-spinner" style={{ width: '24px', height: '24px' }} />
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                  message.role === 'user'
                    ? 'bg-[#209dd7] text-white'
                    : 'bg-gray-100 text-[#032147]'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-3 flex items-center gap-2">
                <div className="loading-spinner" style={{ width: '14px', height: '14px' }} />
                <span className="text-sm text-[#888888]">Thinking...</span>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div
            role="alert"
            className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm flex items-center justify-between gap-3"
          >
            <span>{error}</span>
            {input.trim() && (
              <button
                type="button"
                onClick={() => void send()}
                disabled={isLoading || !isReady}
                className="px-3 py-1 rounded text-sm font-semibold bg-red-100 hover:bg-red-200 text-red-800 shrink-0 cursor-pointer border-0"
              >
                Retry
              </button>
            )}
          </div>
        )}

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void send();
          }}
          className="flex gap-2 mt-auto"
        >
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type your answer..."
            className="form-input flex-1"
            aria-label="Chat message"
            maxLength={8000}
            disabled={isLoading || !isReady}
          />
          <button
            type="submit"
            disabled={isLoading || !isReady || !input.trim()}
            className="px-4 py-2 rounded font-semibold text-sm bg-[#753991] hover:bg-[#5f2f7a] text-white cursor-pointer border-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>

      {/* Preview Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-[#032147]">Preview</h2>
          {complete && (
            <span className="text-sm font-semibold text-green-700">Ready to download</span>
          )}
        </div>

        <NDAPreview values={fields} template={template} />

        {complete && (
          <div className="mt-4">
            {downloadSuccess && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded text-green-800 text-sm">
                ✓ PDF downloaded successfully!
              </div>
            )}
            {downloadError && (
              <div role="alert" className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
                {downloadError}
              </div>
            )}
            <button
              type="button"
              onClick={() => void handleDownload()}
              disabled={isLoading}
              className="btn w-full bg-[#753991] hover:bg-[#5f2f7a] text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Download NDA as PDF
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
