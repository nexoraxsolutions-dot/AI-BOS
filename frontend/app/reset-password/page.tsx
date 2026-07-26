'use client'

import { useState, FormEvent, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { resetPassword } from '../../lib/api'

type ScreenState = 'form' | 'success' | 'error'

interface FormErrors {
  password?: string
  confirmPassword?: string
}

export default function ResetPasswordPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [screen, setScreen] = useState<ScreenState>('form')

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing reset token. Please request a new password reset link.')
      setScreen('error')
    }
  }, [token])

  function validatePassword(password: string): string | undefined {
    if (!password) {
      return 'Password is required'
    }
    if (password.length < 12) {
      return `Password must be at least 12 characters long (currently ${password.length})`
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter'
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter'
    }
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one digit'
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password)) {
      return 'Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:",./<>?)'
    }
    return undefined
  }

  function validateConfirmPassword(confirmPassword: string, password: string): string | undefined {
    if (!confirmPassword) {
      return 'Please confirm your password'
    }
    if (confirmPassword !== password) {
      return 'Passwords do not match'
    }
    return undefined
  }

  function handleBlur(field: string) {
    setTouched(prev => ({ ...prev, [field]: true }))
    
    if (field === 'password') {
      const error = validatePassword(password)
      setErrors(prev => ({ ...prev, password: error }))
    } else if (field === 'confirmPassword') {
      const error = validateConfirmPassword(confirmPassword, password)
      setErrors(prev => ({ ...prev, confirmPassword: error }))
    }
  }

  function handleChange(field: string, value: string) {
    if (field === 'password') {
      setPassword(value)
      // Also validate confirm password if it has been touched
      if (touched.confirmPassword && confirmPassword) {
        const error = validateConfirmPassword(confirmPassword, value)
        setErrors(prev => ({ ...prev, confirmPassword: error }))
      }
    } else {
      setConfirmPassword(value)
    }

    if (touched[field]) {
      const error = field === 'password' ? validatePassword(value) : validateConfirmPassword(value, password)
      setErrors(prev => ({ ...prev, [field]: error }))
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setMessage(null)

    // Mark all fields as touched
    setTouched({ password: true, confirmPassword: true })

    // Validate all fields
    const passwordError = validatePassword(password)
    const confirmPasswordError = validateConfirmPassword(confirmPassword, password)
    
    setErrors({
      password: passwordError,
      confirmPassword: confirmPasswordError,
    })

    if (passwordError || confirmPasswordError) {
      return
    }

    if (!token) {
      setError('Missing reset token. Please use the link from your email.')
      setScreen('error')
      return
    }

    setLoading(true)

    try {
      const response = await resetPassword(token, password, confirmPassword)
      setMessage(response.message)
      setScreen('success')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred. Please try again.'
      
      // Check if it's an expired/invalid token error
      if (errorMessage.toLowerCase().includes('invalid or expired') || 
          errorMessage.toLowerCase().includes('invalid token')) {
        setError('This password reset link has expired or is invalid. Please request a new one.')
      } else {
        setError(errorMessage)
      }
      setScreen('error')
    } finally {
      setLoading(false)
    }
  }

  const handleTryAnotherEmail = () => {
    router.push('/forgot-password')
  }

  // Success Screen
  if (screen === 'success' && message) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-center">
          <div className="w-full max-w-md">
            <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl">
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-emerald-900/50 border-2 border-emerald-500 rounded-full flex items-center justify-center mb-6">
                  <svg className="w-8 h-8 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                
                <h2 className="text-3xl font-semibold text-white mb-3">Password Reset Successful</h2>
                
                <div className="bg-emerald-900/50 border border-emerald-700 rounded-xl p-4 mb-6">
                  <p className="text-emerald-200">{message}</p>
                </div>

                <p className="text-sm text-slate-400 mb-8">
                  Redirecting to login in <span className="text-cyan-400 font-semibold">3 seconds</span>...
                </p>

                <button
                  onClick={() => router.push('/login')}
                  className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-950"
                >
                  Go to Login
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    )
  }

  // Error Screen (Invalid/Expired Token)
  if (screen === 'error' && error && !token) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-center">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center">
              <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
              <h1 className="mt-4 text-4xl font-semibold">Reset Password</h1>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl">
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-red-900/50 border-2 border-red-500 rounded-full flex items-center justify-center mb-6">
                  <svg className="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                
                <h2 className="text-2xl font-semibold text-white mb-3">Invalid or Expired Link</h2>
                
                <div className="bg-red-900/50 border border-red-700 rounded-xl p-4 mb-6">
                  <p className="text-red-200">{error}</p>
                </div>

                <p className="text-sm text-slate-400 mb-8">
                  This link may have expired or already been used. For security reasons, reset links are only valid for a limited time.
                </p>

                <div className="space-y-3">
                  <button
                    onClick={handleTryAnotherEmail}
                    className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-950"
                  >
                    Request New Link
                  </button>
                  
                  <Link
                    href="/login"
                    className="block w-full rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-base font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white text-center"
                  >
                    Back to Login
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    )
  }

  // Error Screen (Token exists but invalid/expired)
  if (screen === 'error' && error && token) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-center">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center">
              <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
              <h1 className="mt-4 text-4xl font-semibold">Reset Password</h1>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl">
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-red-900/50 border-2 border-red-500 rounded-full flex items-center justify-center mb-6">
                  <svg className="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                
                <h2 className="text-2xl font-semibold text-white mb-3">Link Expired or Invalid</h2>
                
                <div className="bg-red-900/50 border border-red-700 rounded-xl p-4 mb-6">
                  <p className="text-red-200">{error}</p>
                </div>

                <p className="text-sm text-slate-400 mb-8">
                  This password reset link has expired or has already been used. Please request a new one to continue.
                </p>

                <div className="space-y-3">
                  <button
                    onClick={handleTryAnotherEmail}
                    className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-950"
                  >
                    Request New Reset Link
                  </button>
                  
                  <Link
                    href="/login"
                    className="block w-full rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-base font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white text-center"
                  >
                    Back to Login
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    )
  }

  // Reset Password Form
  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto flex max-w-6xl items-center justify-center">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="mt-4 text-4xl font-semibold">Reset Password</h1>
            <p className="mt-2 text-slate-400">Enter your new password below</p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl">
            {message && screen === 'success' && (
              <div className="mb-6 rounded-xl bg-emerald-900/50 border border-emerald-700 p-4 text-emerald-200" role="alert">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-emerald-100">Success</p>
                    <p className="mt-1 text-sm text-emerald-200">{message}</p>
                  </div>
                </div>
              </div>
            )}

            {error && screen === 'error' && (
              <div className="mb-6 rounded-xl bg-red-900/50 border border-red-700 p-4 text-red-200" role="alert">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            )}

            {screen === 'form' && (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                    New Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => handleChange('password', e.target.value)}
                    onBlur={() => handleBlur('password')}
                    required
                    aria-invalid={!!errors.password}
                    aria-describedby={errors.password ? 'password-error' : 'password-requirements'}
                    className={`w-full rounded-2xl border bg-slate-950 px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500/20 ${
                      errors.password && touched.password
                        ? 'border-red-500 focus:border-red-400'
                        : 'border-slate-700 focus:border-cyan-400'
                    }`}
                    placeholder="Min. 12 characters"
                    autoComplete="new-password"
                  />
                  {errors.password && touched.password && (
                    <p id="password-error" className="mt-1.5 text-sm text-red-400" role="alert">
                      {errors.password}
                    </p>
                  )}
                  <p id="password-requirements" className="mt-1.5 text-xs text-slate-500">
                    Must be 12+ characters with uppercase, lowercase, number, and special character
                  </p>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
                    Confirm Password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => handleChange('confirmPassword', e.target.value)}
                    onBlur={() => handleBlur('confirmPassword')}
                    required
                    aria-invalid={!!errors.confirmPassword}
                    aria-describedby={errors.confirmPassword ? 'confirmPassword-error' : undefined}
                    className={`w-full rounded-2xl border bg-slate-950 px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500/20 ${
                      errors.confirmPassword && touched.confirmPassword
                        ? 'border-red-500 focus:border-red-400'
                        : 'border-slate-700 focus:border-cyan-400'
                    }`}
                    placeholder="Repeat your new password"
                    autoComplete="new-password"
                  />
                  {errors.confirmPassword && touched.confirmPassword && (
                    <p id="confirmPassword-error" className="mt-1.5 text-sm text-red-400" role="alert">
                      {errors.confirmPassword}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading || !token}
                  className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-950"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Resetting...
                    </span>
                  ) : (
                    'Reset Password'
                  )}
                </button>
              </form>
            )}

            {screen === 'success' && message && (
              <div className="text-center py-4">
                <p className="text-sm text-slate-400">
                  Redirecting to login...
                </p>
              </div>
            )}
          </div>

          <p className="mt-6 text-center text-sm text-slate-400">
            <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-medium transition">
              Back to login
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}