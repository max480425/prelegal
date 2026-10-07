'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signup, signin } = useAuth();

  const initialMode =
    searchParams.get('mode') === 'signup' ? 'signup' : 'signin';
  const [mode, setMode] = useState<'signin' | 'signup'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isSignup = mode === 'signup';

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      if (isSignup) {
        await signup(email, password);
      } else {
        await signin(email, password);
      }
      router.push('/nda-creator/');
    } catch (err: any) {
      setError(err?.error || 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8">
      <div className="bg-white rounded-lg shadow p-8">
        <h1 className="text-3xl font-bold text-[#032147] mb-2">
          {isSignup ? 'Create your account' : 'Welcome back'}
        </h1>
        <p className="text-gray-600 mb-6">
          {isSignup
            ? 'Sign up to start drafting legal agreements.'
            : 'Sign in to continue to the NDA Creator.'}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-field-wrapper">
            <label htmlFor="email" className="form-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-field-wrapper">
            <label htmlFor="password" className="form-label">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder={isSignup ? 'At least 8 characters' : 'Your password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={isSignup ? 8 : 1}
              autoComplete={isSignup ? 'new-password' : 'current-password'}
            />
            {isSignup && (
              <p className="form-description">Minimum 8 characters.</p>
            )}
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary w-full"
            style={{ backgroundColor: '#753991' }}
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Please wait…'
              : isSignup
                ? 'Create account'
                : 'Sign in'}
          </button>
        </form>

        <p className="text-sm text-gray-600 mt-6 text-center">
          {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            type="button"
            className="font-medium"
            style={{ color: '#209dd7' }}
            onClick={() => {
              setMode(isSignup ? 'signin' : 'signup');
              setError(null);
            }}
          >
            {isSignup ? 'Sign in' : 'Sign up'}
          </button>
        </p>
      </div>

      <p className="text-center mt-6">
        <Link href="/nda-creator/" className="text-sm text-gray-500 hover:text-gray-700">
          Continue without an account →
        </Link>
      </p>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-16"><div className="loading-spinner" /></div>}>
      <SignInForm />
    </Suspense>
  );
}
