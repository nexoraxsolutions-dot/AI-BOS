'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { verifyEmail, resendVerification } from '../../lib/api';
import Link from 'next/link';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'idle'>('idle');
  const [errorKind, setErrorKind] = useState<'invalid' | 'expired' | 'generic'>('invalid');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [resendStatus, setResendStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [resendMessage, setResendMessage] = useState('');

  function classifyError(err: unknown): 'invalid' | 'expired' | 'generic' {
    const msg = err instanceof Error ? err.message : '';
    if (/expired/i.test(msg)) return 'expired';
    if (/invalid/i.test(msg) || /not found/i.test(msg)) return 'invalid';
    return 'generic';
  }

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setStatus('loading');
      setMessage('');
      verifyEmail(token)
        .then((data: { message: string }) => {
          setStatus('success');
          setMessage(data.message);
          // Automatically redirect to Login after successful verification.
          const t = setTimeout(() => router.push('/login'), 2500);
          return () => clearTimeout(t);
        })
        .catch((err: unknown) => {
          setErrorKind(classifyError(err));
          setStatus('error');
          setMessage(err instanceof Error ? err.message : 'Verification failed');
        });
    } else {
      setStatus('idle');
    }
  }, [searchParams, router]);

  const handleResend = async () => {
    if (!email.trim()) {
      setResendMessage('Please enter your email address');
      return;
    }
    setResendStatus('sending');
    try {
      const data = await resendVerification(email);
      setResendStatus('sent');
      setResendMessage(data.message);
    } catch (err: unknown) {
      setResendStatus('error');
      setResendMessage(err instanceof Error ? err.message : 'Failed to resend verification email');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-slate-950/80 backdrop-blur-xl border border-white/10 p-10 rounded-3xl shadow-2xl">
        <div className="text-center">
          <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
          <h1 className="mt-2 text-3xl font-semibold text-white mb-2">Email Verification</h1>
          <p className="text-sm text-slate-400">
            Verify your email address to activate your account
          </p>
        </div>

        {status === 'loading' && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Verifying your email...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center py-8">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/40">
              <svg className="h-8 w-8 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-white mb-3">Verification Success</h2>
            <p className="text-sm text-slate-300">{message}</p>
            <p className="mt-3 text-sm text-slate-400">
              Your account is now active. Redirecting you to sign in...
            </p>
            <Link
              href="/login"
              className="mt-6 inline-flex items-center px-6 py-3 text-base font-medium rounded-2xl text-slate-950 bg-cyan-500 hover:bg-cyan-400 transition-colors"
            >
              Go to Login
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center py-8">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/40">
              <svg className="h-8 w-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-white mb-3">
              {errorKind === 'expired' ? 'Expired Link' : errorKind === 'invalid' ? 'Invalid Link' : 'Verification Failed'}
            </h2>
            <p className="text-sm text-slate-300">{message}</p>
            <p className="mt-3 text-sm text-slate-400">
              {errorKind === 'expired'
                ? 'This verification link has expired. Request a new one below to continue.'
                : 'This verification link is not valid. You can request a new verification email below.'}
            </p>
            <div className="mt-6 flex flex-col gap-3">
              <Link
                href="/login"
                className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-2xl border border-white/10 bg-white/5 text-slate-200 hover:bg-white/10 transition-colors"
              >
                Go to Login
              </Link>
              <button
                onClick={() => {
                  setStatus('idle');
                }}
                className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-2xl text-slate-950 bg-cyan-500 hover:bg-cyan-400 transition-colors"
              >
                Resend Verification
              </button>
            </div>
          </div>
        )}

        {status === 'idle' && (
          <div className="py-4">
            <p className="text-center text-slate-400 mb-6">
              Enter your email address to receive a new verification link.
            </p>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 block w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="your@email.com"
                  required
                />
              </div>
              <button
                onClick={handleResend}
                disabled={resendStatus === 'sending'}
                className="w-full flex justify-center py-3 px-4 rounded-2xl text-sm font-medium text-slate-950 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {resendStatus === 'sending' ? 'Sending...' : 'Send Verification Email'}
              </button>
              {resendMessage && (
                <div
                  className={`px-4 py-3 rounded-xl text-sm ${
                    resendStatus === 'sent'
                      ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
                      : 'bg-red-500/10 border border-red-500/30 text-red-400'
                  }`}
                >
                  {resendMessage}
                </div>
              )}
              <div className="text-center mt-4">
                <Link href="/login" className="text-sm text-cyan-400 hover:text-cyan-300">
                  Back to Login
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-cyan-500 border-t-transparent"></div>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}