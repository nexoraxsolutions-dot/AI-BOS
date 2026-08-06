"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import {
  getPasswordPolicy,
  validatePassword,
  getDefaultPasswordPolicy,
  updatePasswordPolicy,
  PasswordPolicyResponse,
  PasswordValidationResponse,
  PasswordPolicyUpdate
} from '../../../lib/api'

type TabType = 'policy' | 'validator'

export default function PasswordPolicyPage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('policy')
  const [isSuperuser, setIsSuperuser] = useState(false)

  const [policy, setPolicy] = useState<PasswordPolicyResponse | null>(null)
  const [formData, setFormData] = useState<PasswordPolicyUpdate>({})
  const [validationPassword, setValidationPassword] = useState('')
  const [validationResult, setValidationResult] = useState<PasswordValidationResponse | null>(null)
  const [validating, setValidating] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchPolicy()
  }, [isAuthenticated, router])

  const fetchPolicy = async () => {
    try {
      setLoading(true)
      const data = await getPasswordPolicy()
      setPolicy(data)
      setFormData({})
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load password policy')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!policy) return

    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const updated = await updatePasswordPolicy(formData)
      setPolicy(updated)
      setFormData({})
      setSuccess('Password policy updated successfully')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update password policy')
    } finally {
      setSaving(false)
    }
  }

  const handleResetToDefaults = async () => {
    try {
      setLoading(true)
      const defaults = await getDefaultPasswordPolicy()
      setFormData({
        min_length: defaults.min_length,
        require_uppercase: defaults.require_uppercase,
        require_lowercase: defaults.require_lowercase,
        require_numbers: defaults.require_numbers,
        require_special_chars: defaults.require_special_chars,
        expiry_days: defaults.expiry_days,
      })
      setError(null)
      setSuccess('Form reset to default values. Click Save to apply.')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load default policy')
    } finally {
      setLoading(false)
    }
  }

  const handleValidatePassword = async () => {
    if (!validationPassword) return

    setValidating(true)
    setValidationResult(null)

    try {
      const result = await validatePassword(validationPassword)
      setValidationResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate password')
    } finally {
      setValidating(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const updateField = <K extends keyof PasswordPolicyUpdate>(field: K, value: PasswordPolicyUpdate[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const hasChanges = Object.keys(formData).length > 0

  if (loading && !policy) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading password policy...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error && !policy) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Password Policy</h2>
            <p className="text-slate-300">{error}</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-6 rounded-xl bg-slate-800 px-6 py-3 text-white hover:bg-slate-700 transition"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Password Policy</h1>
            <p className="text-slate-400 mt-1">Manage password requirements and test password strength</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Dashboard
            </button>
            <button
              onClick={handleLogout}
              className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Sign Out
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-xl bg-green-500/10 border border-green-500/30 p-4 text-green-400 text-sm">
            {success}
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-white/10">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('policy')}
              className={`px-6 py-3 text-sm font-medium transition ${
                activeTab === 'policy'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span className="mr-2">🔒</span>
              Policy Settings
            </button>
            <button
              onClick={() => setActiveTab('validator')}
              className={`px-6 py-3 text-sm font-medium transition ${
                activeTab === 'validator'
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span className="mr-2">✓</span>
              Password Validator
            </button>
          </div>
        </div>

        {/* Policy Settings Tab */}
        {activeTab === 'policy' && policy && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8">
            <h2 className="text-2xl font-semibold mb-6">Password Policy Settings</h2>

            <div className="space-y-6">
              <div>
                <label className="block text-sm text-slate-300 mb-2">
                  Minimum Length: {formData.min_length ?? policy.min_length} characters
                </label>
                <input
                  type="range"
                  min="6"
                  max="128"
                  value={formData.min_length ?? policy.min_length}
                  onChange={(e) => updateField('min_length', parseInt(e.target.value))}
                  disabled={!isSuperuser}
                  className="w-full disabled:opacity-50"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Require Uppercase</p>
                    <p className="text-xs text-slate-400 mt-1">Password must contain uppercase letters (A-Z)</p>
                  </div>
                  <button
                    onClick={() => updateField('require_uppercase', !(formData.require_uppercase ?? policy.require_uppercase))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.require_uppercase ?? policy.require_uppercase) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.require_uppercase ?? policy.require_uppercase) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Require Lowercase</p>
                    <p className="text-xs text-slate-400 mt-1">Password must contain lowercase letters (a-z)</p>
                  </div>
                  <button
                    onClick={() => updateField('require_lowercase', !(formData.require_lowercase ?? policy.require_lowercase))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.require_lowercase ?? policy.require_lowercase) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.require_lowercase ?? policy.require_lowercase) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Require Numbers</p>
                    <p className="text-xs text-slate-400 mt-1">Password must contain numbers (0-9)</p>
                  </div>
                  <button
                    onClick={() => updateField('require_numbers', !(formData.require_numbers ?? policy.require_numbers))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.require_numbers ?? policy.require_numbers) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.require_numbers ?? policy.require_numbers) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Require Special Characters</p>
                    <p className="text-xs text-slate-400 mt-1">Password must contain special characters (!@#$%^&*)</p>
                  </div>
                  <button
                    onClick={() => updateField('require_special_chars', !(formData.require_special_chars ?? policy.require_special_chars))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.require_special_chars ?? policy.require_special_chars) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.require_special_chars ?? policy.require_special_chars) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-2">Password Expiry (days, 0 = never expires)</label>
                  <input
                    type="number"
                    min="0"
                    max="365"
                    value={formData.expiry_days ?? policy.expiry_days}
                    onChange={(e) => updateField('expiry_days', parseInt(e.target.value))}
                    disabled={!isSuperuser}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                  />
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex items-center justify-between border-t border-white/10 pt-6">
              <button
                onClick={handleResetToDefaults}
                disabled={saving}
                className="rounded-xl border border-slate-700 bg-slate-900 px-6 py-2.5 text-sm text-slate-300 hover:bg-slate-800 transition disabled:opacity-50"
              >
                Reset to Defaults
              </button>
              <div className="flex gap-3">
                <button
                  onClick={() => setFormData({})}
                  disabled={saving || !hasChanges}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-6 py-2.5 text-sm text-slate-300 hover:bg-slate-800 transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || !hasChanges}
                  className="rounded-xl bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Password Validator Tab */}
        {activeTab === 'validator' && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8">
            <h2 className="text-2xl font-semibold mb-6">Test Password Strength</h2>
            <p className="text-slate-400 mb-6">Enter a password to check if it meets the current organization policy requirements.</p>

            <div className="space-y-6">
              <div>
                <label className="block text-sm text-slate-300 mb-2">Enter Password</label>
                <input
                  type="text"
                  value={validationPassword}
                  onChange={(e) => setValidationPassword(e.target.value)}
                  placeholder="Type a password to validate..."
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                />
              </div>

              <button
                onClick={handleValidatePassword}
                disabled={validating || !validationPassword}
                className="rounded-xl bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {validating ? 'Validating...' : 'Validate Password'}
              </button>

              {validationResult && (
                <div className="space-y-4">
                  {/* Overall Status */}
                  <div className={`rounded-xl p-4 border ${
                    validationResult.valid
                      ? 'bg-green-500/10 border-green-500/30'
                      : 'bg-red-500/10 border-red-500/30'
                  }`}>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{validationResult.valid ? '✓' : '✗'}</span>
                      <div>
                        <p className={`font-semibold ${validationResult.valid ? 'text-green-400' : 'text-red-400'}`}>
                          {validationResult.valid ? 'Password is valid!' : 'Password does not meet requirements'}
                        </p>
                        {validationResult.errors.length > 0 && (
                          <ul className="mt-2 space-y-1">
                            {validationResult.errors.map((error, idx) => (
                              <li key={idx} className="text-sm text-red-300">• {error}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Requirements Checklist */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-slate-300">Requirements Checklist:</p>
                    {validationResult.requirements.map((req) => (
                      <div
                        key={req.id}
                        className={`flex items-center gap-3 p-3 rounded-lg border ${
                          req.met
                            ? 'bg-green-500/5 border-green-500/20'
                            : 'bg-red-500/5 border-red-500/20'
                        }`}
                      >
                        <span className={`text-lg ${req.met ? 'text-green-400' : 'text-red-400'}`}>
                          {req.met ? '✓' : '✗'}
                        </span>
                        <span className={`text-sm ${req.met ? 'text-slate-300' : 'text-slate-400'}`}>
                          {req.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}