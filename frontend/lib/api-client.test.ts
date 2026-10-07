import { describe, it, expect, vi, afterEach } from 'vitest';
import { normalizeApiError, apiClient } from './api-client';

describe('normalizeApiError', () => {
  it('handles string detail (auth routes)', () => {
    expect(normalizeApiError(401, { detail: 'Invalid email or password' })).toEqual(
      { error: 'Invalid email or password' },
    );
  });

  it('handles object detail (document generate)', () => {
    const result = normalizeApiError(400, {
      detail: { error: 'Missing required fields: Purpose', missing_fields: ['Purpose'] },
    });
    expect(result.error).toBe('Missing required fields: Purpose');
    expect(result.missing_fields).toEqual(['Purpose']);
  });

  it('handles 422 validation array without spreading into index keys', () => {
    const result = normalizeApiError(422, {
      detail: [
        { loc: ['body', 'email'], msg: 'value is not a valid email address' },
        { loc: ['body', 'password'], msg: 'String should have at least 8 characters' },
      ],
    });
    expect(result.error).toContain('email: value is not a valid email address');
    expect(result.error).toContain('password: String should have at least 8 characters');
    expect((result as any)[0]).toBeUndefined();
  });

  it('falls back gracefully when body is missing', () => {
    expect(normalizeApiError(500, null)).toEqual({
      error: 'Request failed (500)',
    });
  });
});

describe('NDAApiClient', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('signup posts JSON with credentials included', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Account created', user: { id: 1, email: 'a@b.co' } }),
    } as Response);

    const result = await apiClient.signup('a@b.co', 'password123');

    expect(result.user.email).toBe('a@b.co');
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/signup',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
      }),
    );
  });

  it('me returns null when unauthenticated', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Not signed in' }),
    } as Response);

    expect(await apiClient.me()).toBeNull();
  });

  it('signin surfaces backend error message', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Invalid email or password' }),
    } as Response);

    await expect(apiClient.signin('a@b.co', 'wrong-pass')).rejects.toEqual({
      error: 'Invalid email or password',
    });
  });
});
