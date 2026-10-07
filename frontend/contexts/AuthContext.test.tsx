import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { apiClient } from '@/lib/api-client';

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    me: vi.fn(),
    signup: vi.fn(),
    signin: vi.fn(),
    signout: vi.fn(),
  },
}));

const mockedClient = vi.mocked(apiClient);

function Probe() {
  const { user, isLoading, signup, signout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="user">{user?.email ?? 'anonymous'}</span>
      <button onClick={() => signup('new@example.com', 'password123')}>join</button>
      <button onClick={() => signout()}>leave</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('loads the signed-in user from the session cookie', async () => {
    mockedClient.me.mockResolvedValue({ id: 1, email: 'me@example.com' });

    renderProbe();
    expect(screen.getByTestId('loading').textContent).toBe('true');

    await waitFor(() =>
      expect(screen.getByTestId('user').textContent).toBe('me@example.com'),
    );
    expect(screen.getByTestId('loading').textContent).toBe('false');
  });

  it('stays anonymous when there is no session', async () => {
    mockedClient.me.mockResolvedValue(null);

    renderProbe();
    await waitFor(() =>
      expect(screen.getByTestId('loading').textContent).toBe('false'),
    );
    expect(screen.getByTestId('user').textContent).toBe('anonymous');
  });

  it('signup sets the user', async () => {
    mockedClient.me.mockResolvedValue(null);
    mockedClient.signup.mockResolvedValue({
      message: 'Account created',
      user: { id: 7, email: 'new@example.com' },
    });

    renderProbe();
    await waitFor(() =>
      expect(screen.getByTestId('loading').textContent).toBe('false'),
    );

    screen.getByText('join').click();
    await waitFor(() =>
      expect(screen.getByTestId('user').textContent).toBe('new@example.com'),
    );
  });

  it('signout clears the user', async () => {
    mockedClient.me.mockResolvedValue({ id: 1, email: 'me@example.com' });
    mockedClient.signout.mockResolvedValue(undefined);

    renderProbe();
    await waitFor(() =>
      expect(screen.getByTestId('user').textContent).toBe('me@example.com'),
    );

    screen.getByText('leave').click();
    await waitFor(() =>
      expect(screen.getByTestId('user').textContent).toBe('anonymous'),
    );
  });
});
