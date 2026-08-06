"use client"

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '../context/AuthContext'
import { resendVerification } from '../lib/api'

interface FormErrors {
  email?: string
  password?: string
  fullName?: string
  username?: string
}

export default function RegisterForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [message, setMessage] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const { register, loading } = useAuth()

  // Post-registration "Please verify your email" state
  const [registered, setRegistered] = useState(false)
  const [resendStatus, setResendStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [resendMessage, setResendMessage] = useState('')

  async function handleResend() {
    setResendStatus('sending')
    setResendMessage('')
    try {
      const data = await resendVerification(email)
      setResendStatus('sent')
      setResendMessage(data.message || 'Verification email sent successfully')
    } catch (err) {
      setResendStatus('error')
      setResendMessage(err instanceof Error ? err.message : 'Failed to resend verification email')
    }
  }

  function validateField(field: string, value: string): string | undefined {
    if (field === 'email') {
      if (!value.trim()) {
        return 'Email is required'
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(value)) {
        return 'Please enter a valid email address'
      }
    }
    if (field === 'password') {
      if (!value) {
        return 'Password is required'
      }
      if (value.length < 8) {
        return 'Password must be at least 8 characters'
      }
      if (!/[A-Z]/.test(value)) {
        return 'Password must contain at least one uppercase letter'
      }
      if (!/[a-z]/.test(value)) {
        return 'Password must contain at least one lowercase letter'
      }
      if (!/\d/.test(value)) {
        return 'Password must contain at least one digit'
      }
    }
    if (field === 'username') {
      if (value && value.length > 0) {
        if (value.length < 3) {
          return 'Username must be at least 3 characters long'
        }
        if (value.length > 50) {
          return 'Username must be at most 50 characters long'
        }
        if (!/^[A-Za-z0-9_]+$/.test(value)) {
          return 'Username must contain only letters, numbers, and underscores'
        }
      }
    }
    return undefined
  }

  function validateForm(): FormErrors {
    const newErrors: FormErrors = {}
    const emailError = validateField('email', email)
    const passwordError = validateField('password', password)
    const usernameError = validateField('username', username)

    if (emailError) newErrors.email = emailError
    if (passwordError) newErrors.password = passwordError
    if (usernameError) newErrors.username = usernameError

    return newErrors
  }

  function handleBlur(field: string) {
    setTouched(prev => ({ ...prev, [field]: true }))
    const value = field === 'email' ? email : field === 'password' ? password : username
    const error = validateField(field, value)
    setErrors(prev => ({ ...prev, [field]: error }))
  }

  function handleChange(field: string, value: string) {
    if (field === 'email') setEmail(value)
    else if (field === 'password') setPassword(value)
    else if (field === 'fullName') setFullName(value)
    else setUsername(value)

    if (touched[field]) {
      const error = validateField(field, value)
      setErrors(prev => ({ ...prev, [field]: error }))
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')

    setTouched({ email: true, password: true, username: true })
    const formErrors = validateForm()
    setErrors(formErrors)

    if (Object.keys(formErrors).length > 0) {
      return
    }

    try {
      await register(email, password, fullName || undefined, username || undefined)
      // Do NOT redirect to the dashboard — the account email is not verified yet.
      setRegistered(true)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Registration failed.')
    }
  }

  if (registered) {
    return (
      <div className="space-y-6 rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl max-w-lg w-full text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/40">
          <svg className="h-7 w-7 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
        <h2 className="text-2xl font-semibold text-white">Please verify your email.</h2>
        <p className="text-sm text-slate-400">
          We sent a verification link to <span className="text-cyan-300">{email}</span>.
          Check your inbox to activate your account before signing in.
        </p>

        <button
          onClick={handleResend}
          disabled={resendStatus === 'sending'}
          className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {resendStatus === 'sending' ? 'Sending...' : 'Resend Verification'}
        </button>

        {resendMessage && (
          <div
            className={`rounded-xl border p-3 text-sm ${
              resendStatus === 'sent'
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : 'border-red-500/30 bg-red-500/10 text-red-400'
            }`}
          >
            {resendMessage}
          </div>
        )}

        <Link href="/" className="block text-sm text-cyan-400 hover:text-cyan-300">
          Back to Sign in
        </Link>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl max-w-lg w-full">
      <h2 className="text-3xl font-semibold text-white">Create account</h2>

      <div>
        <label htmlFor="fullName" className="block text-sm font-medium text-slate-300">
          Full name
        </label>
        <input
          id="fullName"
          type="text"
          value={fullName}
          onChange={(event) => handleChange('fullName', event.target.value)}
          onBlur={() => handleBlur('fullName')}
          className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20"
        />
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-300">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(event) => handleChange('email', event.target.value)}
          onBlur={() => handleBlur('email')}
          required
          className={`mt-2 w-full rounded-2xl border bg-slate-950 px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500/20 ${
            errors.email && touched.email
              ? 'border-red-500 focus:border-red-400'
              : 'border-slate-700 focus:border-cyan-400'
          }`}
        />
        {errors.email && touched.email && (
          <p className="mt-1 text-sm text-red-400">{errors.email}</p>
        )}
      </div>

      <div>
        <label htmlFor="username" className="block text-sm font-medium text-slate-300">
          Username <span className="text-slate-500">(optional)</span>
        </label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(event) => handleChange('username', event.target.value)}
          onBlur={() => handleBlur('username')}
          className={`mt-2 w-full rounded-2xl border bg-slate-950 px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500/20 ${
            errors.username && touched.username
              ? 'border-red-500 focus:border-red-400'
              : 'border-slate-700 focus:border-cyan-400'
          }`}
        />
        {errors.username && touched.username && (
          <p className="mt-1 text-sm text-red-400">{errors.username}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-slate-300">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => handleChange('password', event.target.value)}
          onBlur={() => handleBlur('password')}
          required
          className={`mt-2 w-full rounded-2xl border bg-slate-950 px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500/20 ${
            errors.password && touched.password
              ? 'border-red-500 focus:border-red-400'
              : 'border-slate-700 focus:border-cyan-400'
          }`}
        />
        {errors.password && touched.password && (
          <p className="mt-1 text-sm text-red-400">{errors.password}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating account...' : 'Create account'}
      </button>

      {message && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-3">
          <p className="text-sm text-red-400">{message}</p>
        </div>
      )}

      <p className="text-center text-sm text-slate-400">
        Already have an account?{' '}
        <Link href="/" className="text-cyan-400 hover:text-cyan-300">
          Sign in
        </Link>
      </p>
    </form>
  )
}
