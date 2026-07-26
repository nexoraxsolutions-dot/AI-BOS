'use client'

import { useState, FormEvent } from 'react'
import Link from 'next/link'
import { forgotPassword } from '../../lib/api'

interface FormErrors {
  email?: string
}

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  function validateEmail(email: string): string | undefined {
    if (!email.trim()) {
      return 'Email is required'
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return 'Please enter a valid email address'
    }
    return undefined
  }

  function handleBlur(field: string) {
    setTouched(prev => ({ ...prev, [field]: true }))
    const error = validateEmail(email)
    setErrors(prev => ({ ...prev, email: error }))
  }

  function handleChange(value: string) {
    setEmail(value)
    if (touched.email) {
      const error = validateEmail(value)
      setErrors(prev => ({ ...prev, email: error }))
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setMessage(null)

    // Mark field as touched and validate
    setTouched(prev => ({ ...prev, email: true }))
    const emailError = validateEmail(email)
    setErrors(prev => ({ ...prev, email: emailError }))

    if (emailError) {
      return
    }

    setLoading(true)

    try {
      const response = await forgotPassword(email)
      setMessage(response.message)
      setEmail('')
      setTouched({})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto flex max-w-6xl items-center justify-center">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="mt-4 text-4xl font-semibold">Forgot Password</h1>
            <p className="mt-2 text-slate-400">
              Enter your email address and we'll send you a reset link
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl">
            {message && (
              <div className="mb-6 rounded-xl bg-emerald-900/50 border border-emerald-700 p-4 text-emerald-200" role="alert">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-emerald-100">Check your email</p>
                    <p className="mt-1 text-sm text-emerald-200">{message}</p>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 rounded-xl bg-red-900/50 border border-red-700 p-4 text-red-200" role="alert">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            )}

            {!message ? (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                    Email address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => handleChange(e.target.value)}
                    onBlur={() => handleBlur('email')}
                    required
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? 'email-error' : undefined}
                    className={`w-full rounded-2xl border bg-slate-950 px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500/20 ${
                      errors.email && touched.email
                        ? 'border-red-500 focus:border-red-400'
                        : 'border-slate-700 focus:border-cyan-400'
                    }`}
                    placeholder="you@example.com"
                    autoComplete="email"
                  />
                  {errors.email && touched.email && (
                    <p id="email-error" className="mt-1.5 text-sm text-red-400" role="alert">
                      {errors.email}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-950"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Sending...
                    </span>
                  ) : (
                    'Send Reset Link'
                  )}
                </button>
              </form>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-slate-400 mb-6">
                  Didn't receive the email? Check your spam folder or try again.
                </p>
                <button
                  onClick={() => {
                    setMessage(null)
                    setEmail('')
                    setTouched({})
                    setErrors({})
                  }}
                  className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition"
                >
                  Try another email
                </button>
              </div>
            )}
          </div>

          <p className="mt-6 text-center text-sm text-slate-400">
            Remember your password?{' '}
            <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-medium transition">
              Back to login
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}