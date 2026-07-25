"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../context/AuthContext'

interface FormErrors {
  email?: string
  password?: string
}

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const { login, loading } = useAuth()
  const router = useRouter()

  // Validate individual field
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
    }
    return undefined
  }

  // Validate all fields
  function validateForm(): FormErrors {
    const newErrors: FormErrors = {}
    const emailError = validateField('email', email)
    const passwordError = validateField('password', password)
    
    if (emailError) newErrors.email = emailError
    if (passwordError) newErrors.password = passwordError
    
    return newErrors
  }

  // Handle field blur
  function handleBlur(field: string) {
    setTouched(prev => ({ ...prev, [field]: true }))
    const error = validateField(field, field === 'email' ? email : password)
    setErrors(prev => ({ ...prev, [field]: error }))
  }

  // Handle input change with real-time validation
  function handleChange(field: string, value: string) {
    if (field === 'email') {
      setEmail(value)
    } else {
      setPassword(value)
    }

    // Validate if field has been touched
    if (touched[field]) {
      const error = validateField(field, value)
      setErrors(prev => ({ ...prev, [field]: error }))
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')

    // Mark all fields as touched
    setTouched({ email: true, password: true })

    // Validate all fields
    const formErrors = validateForm()
    setErrors(formErrors)

    // If there are errors, don't submit
    if (Object.keys(formErrors).length > 0) {
      return
    }

    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Login failed.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl max-w-lg w-full">
      <h2 className="text-3xl font-semibold text-white">Sign in</h2>
      
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
        {loading ? 'Signing in...' : 'Sign in'}
      </button>
      
      {message && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-3">
          <p className="text-sm text-red-400">{message}</p>
        </div>
      )}

      <p className="text-center text-sm text-slate-400">
        Don't have an account?{' '}
        <Link href="/register" className="text-cyan-400 hover:text-cyan-300">
          Create account
        </Link>
      </p>
    </form>
  )
}
