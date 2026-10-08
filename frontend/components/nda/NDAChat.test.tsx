import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup, fireEvent } from '@testing-library/react';
import { NDAChat } from './NDAChat';
import { apiClient } from '@/lib/api-client';

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    getChatGreeting: vi.fn(),
    sendChatMessage: vi.fn(),
    generatePDF: vi.fn(),
    downloadPDF: vi.fn(),
  },
}));

const mockedClient = vi.mocked(apiClient);

const TEMPLATE =
  'Purpose is <span class="coverpage_link">Purpose</span>. ' +
  'Law is <span class="coverpage_link">Governing Law</span>.';

const GREETING = { reply: 'Welcome to the NDA chat!', fields: {}, complete: false };

function chatInput(): HTMLInputElement {
  return screen.getByLabelText('Chat message') as HTMLInputElement;
}

async function awaitGreeting() {
  // The input is gated on the greeting settling — tests must wait for it.
  await waitFor(() => expect(screen.getByText('Welcome to the NDA chat!')).toBeTruthy());
}

async function typeAndSend(text: string) {
  fireEvent.change(chatInput(), { target: { value: text } });
  fireEvent.click(screen.getByRole('button', { name: 'Send' }));
}

describe('NDAChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedClient.getChatGreeting.mockResolvedValue(GREETING);
  });

  afterEach(() => {
    cleanup();
  });

  it('renders the AI greeting after mount', async () => {
    render(<NDAChat template={TEMPLATE} />);
    await waitFor(() =>
      expect(screen.getByText('Welcome to the NDA chat!')).toBeTruthy(),
    );
    expect(mockedClient.getChatGreeting).toHaveBeenCalledTimes(1);
  });

  it('falls back to a local greeting when the greeting fetch fails', async () => {
    mockedClient.getChatGreeting.mockRejectedValue({ error: 'backend down' });
    render(<NDAChat template={TEMPLATE} />);
    await waitFor(() =>
      expect(screen.getByText(/I'll help you put together a Mutual NDA/)).toBeTruthy(),
    );
    expect(screen.getByText('backend down')).toBeTruthy();
    // Once the greeting settles (even in failure), the input unlocks.
    await waitFor(() => expect(chatInput().disabled).toBe(false));
  });

  it('keeps the input disabled until the greeting resolves', () => {
    mockedClient.getChatGreeting.mockReturnValue(new Promise(() => {}) as never);
    render(<NDAChat template={TEMPLATE} />);
    expect(chatInput().disabled).toBe(true);
    expect(screen.getByRole('button', { name: 'Send' }).disabled).toBe(true);
  });

  it('sends a message, shows the reply, and updates the live preview', async () => {
    mockedClient.sendChatMessage.mockResolvedValue({
      reply: 'When should the agreement take effect?',
      fields: { Purpose: 'Evaluating Acme partnership', 'Governing Law': '' },
      complete: false,
    });

    render(<NDAChat template={TEMPLATE} />);
    await awaitGreeting();

    await typeAndSend('We are evaluating a partnership with Acme.');

    await waitFor(() =>
      expect(screen.getByText('When should the agreement take effect?')).toBeTruthy(),
    );
    expect(screen.getByText('We are evaluating a partnership with Acme.')).toBeTruthy();
    expect(mockedClient.sendChatMessage).toHaveBeenCalledWith(
      [
        { role: 'assistant', content: 'Welcome to the NDA chat!' },
        { role: 'user', content: 'We are evaluating a partnership with Acme.' },
      ],
      {},
    );
    // Live preview: the template span is replaced with the extracted value.
    expect(
      screen.getByText(/Purpose is Evaluating Acme partnership\./),
    ).toBeTruthy();
    // Not complete yet → no download button.
    expect(screen.queryByRole('button', { name: /Download NDA as PDF/ })).toBeNull();
  });

  it('shows the download button when the turn completes, and downloads via the API', async () => {
    mockedClient.sendChatMessage.mockResolvedValue({
      reply: 'All done — your document is ready to download.',
      fields: { Purpose: 'Evaluation', 'Governing Law': 'California' },
      complete: true,
    });
    mockedClient.generatePDF.mockResolvedValue({
      document_id: 'doc-1',
      filename: 'Mutual-NDA.pdf',
      download_url: '/api/documents/download/doc-1',
      created_at: '2026-10-07T00:00:00',
    });
    mockedClient.downloadPDF.mockResolvedValue(undefined);

    render(<NDAChat template={TEMPLATE} />);
    await awaitGreeting();

    await typeAndSend('That is everything.');
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Download NDA as PDF/ })).toBeTruthy(),
    );

    fireEvent.click(screen.getByRole('button', { name: /Download NDA as PDF/ }));
    await waitFor(() =>
      expect(mockedClient.generatePDF).toHaveBeenCalledWith({
        template_name: 'Mutual-NDA',
        fields: expect.objectContaining({ Purpose: 'Evaluation' }),
      }),
    );
    expect(mockedClient.downloadPDF).toHaveBeenCalledWith(
      '/api/documents/download/doc-1',
      'Mutual-NDA.pdf',
    );
  });

  it('keeps the typed text on failure and retries successfully', async () => {
    mockedClient.sendChatMessage
      .mockRejectedValueOnce({ error: 'AI service temporarily unavailable' })
      .mockResolvedValueOnce({
        reply: 'Thanks — got it.',
        fields: { Purpose: 'Recovered value' },
        complete: false,
      });

    render(<NDAChat template={TEMPLATE} />);
    await awaitGreeting();

    await typeAndSend('My answer that will fail once.');

    await waitFor(() =>
      expect(screen.getByText('AI service temporarily unavailable')).toBeTruthy(),
    );
    // Text is preserved so nothing the user typed is lost.
    expect(chatInput().value).toBe('My answer that will fail once.');

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() =>
      expect(screen.getByText('Thanks — got it.')).toBeTruthy(),
    );
    expect(screen.queryByText('AI service temporarily unavailable')).toBeNull();
    expect(chatInput().value).toBe('');
  });
});
