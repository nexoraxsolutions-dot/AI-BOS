'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { verifyEmail, resendVerification } from '../../lib/api';
import Link from 'next/link';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'idle'>('idle');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [resendStatus, setResendStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setStatus('loading');
      verifyEmail(token)
         .then((data: { message: string }) => {
          setStatus('success');
          setMessage(data.message);
        })
         .catch((err: unknown) => {
          setStatus('error');
          setMessage(err instanceof Error ? err.message : 'Verification failed');
        });
    } else {
      setStatus('idle');
    }
  }, [searchParams]);

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Verification</h1>
          <p className="text-sm text-gray-600">
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
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
              <p className="font-medium">✓ {message}</p>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Your account is now active. You can log in and start using AI-BOS.
            </p>
            <Link
              href="/"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            >
              Go to Login
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center py-8">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
              <p className="font-medium">✗ {message}</p>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              You can request a new verification email below.
            </p>
            <Link
              href="/"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors mr-3"
            >
              Go to Login
            </Link>
            <button
              onClick={() => {
                setStatus('idle');
              }}
              className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            >
              Resend Verification
            </button>
          </div>
        )}

        {status === 'idle' && (
          <div className="py-4">
            <p className="text-center text-gray-600 mb-6">
              Enter your email address to receive a new verification link.
            </p>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
                  placeholder="your@email.com"
                  required
                />
              </div>
              <button
                onClick={handleResend}
                disabled={resendStatus === 'sending'}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {resendStatus === 'sending' ? 'Sending...' : 'Send Verification Email'}
              </button>
              {resendMessage && (
                <div
                  className={`px-4 py-3 rounded-lg text-sm ${
                    resendStatus === 'sent'
                      ? 'bg-green-100 border border-green-400 text-green-700'
                      : 'bg-red-100 border border-red-400 text-red-700'
                  }`}
                >
                  {resendMessage}
                </div>
              )}
              <div className="text-center mt-4">
                <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-500">
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
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}