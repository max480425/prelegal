import { DocumentResponse, ApiError, AuthResponse, AuthUser } from './types';

// Empty string => same-origin relative URLs. When the static export is served
// by FastAPI at localhost:8000 the API is on the same origin, so cookies flow
// without CORS. During `next dev` on :3000, set NEXT_PUBLIC_API_URL in
// frontend/.env.local to http://localhost:8000 (cross-origin; backend CORS
// allows it with credentials).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

/**
 * Turn a FastAPI error body into a user-facing ApiError.
 * `detail` may be a string, an object ({error, missing_fields}), or an
 * array of field errors (FastAPI 422 validation).
 */
export function normalizeApiError(status: number, body: any): ApiError {
  const detail = body?.detail;

  if (typeof detail === 'string') {
    return { error: detail };
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: any) => `${(item?.loc ?? []).slice(1).join('.')}: ${item?.msg}`)
      .filter(Boolean)
      .join('; ');
    return { error: messages || `Validation failed (${status})` };
  }
  if (detail && typeof detail === 'object') {
    return { error: detail.error ?? `Request failed (${status})`, ...detail };
  }
  return { error: `Request failed (${status})` };
}

export class NDAApiClient {
  private baseUrl: string;

  constructor(baseUrl = API_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      // Always send the HttpOnly session cookie.
      credentials: 'include',
      ...init,
    });

    if (!response.ok) {
      let body: any;
      try {
        body = await response.json();
      } catch {
        body = null;
      }
      throw normalizeApiError(response.status, body);
    }

    return response.json();
  }

  private postAuth(path: string, email: string, password: string) {
    return this.request<AuthResponse>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  }

  // ---- Documents ----

  async generatePDF(data: {
    template_name: string;
    fields: Record<string, string>;
  }): Promise<DocumentResponse> {
    return this.request<DocumentResponse>('/api/documents/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  async downloadPDF(downloadUrl: string, filename: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}${downloadUrl}`, {
      credentials: 'include',
    });
    if (!response.ok) {
      throw new Error('Download failed');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  async getTemplateSchema(templateName: string) {
    return this.request(`/api/templates/${templateName}/schema`);
  }

  // ---- Auth ----

  async signup(email: string, password: string): Promise<AuthResponse> {
    return this.postAuth('/api/auth/signup', email, password);
  }

  async signin(email: string, password: string): Promise<AuthResponse> {
    return this.postAuth('/api/auth/signin', email, password);
  }

  async signout(): Promise<void> {
    await this.request('/api/auth/signout', { method: 'POST' });
  }

  async me(): Promise<AuthUser | null> {
    try {
      return await this.request<AuthUser>('/api/auth/me');
    } catch {
      return null;
    }
  }
}

export const apiClient = new NDAApiClient();
