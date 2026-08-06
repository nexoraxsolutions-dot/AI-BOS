"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import { 
  getOrganizationSettings, updateOrganizationSettings, getDefaultOrganizationSettings,
  OrganizationSettings, OrganizationSettingsUpdate 
} from '../../../lib/api'

type TabType = 'general' | 'security' | 'notifications' | 'branding' | 'features'

export default function OrganizationSettingsPage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('general')
  const [isSuperuser, setIsSuperuser] = useState(false)
  
  const [settings, setSettings] = useState<OrganizationSettings | null>(null)
  const [formData, setFormData] = useState<OrganizationSettingsUpdate>({})

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchSettings()
  }, [isAuthenticated, router])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const data = await getOrganizationSettings()
      setSettings(data)
      setFormData({})
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load organization settings')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!settings) return
    
    setSaving(true)
    setError(null)
    setSuccess(null)
    
    try {
      const updated = await updateOrganizationSettings(formData)
      setSettings(updated)
      setFormData({})
      setSuccess('Organization settings updated successfully')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update organization settings')
    } finally {
      setSaving(false)
    }
  }

  const handleResetToDefaults = async () => {
    try {
      setLoading(true)
      const defaults = await getDefaultOrganizationSettings()
      setFormData({
        timezone: defaults.timezone,
        date_format: defaults.date_format,
        time_format: defaults.time_format,
        language: defaults.language,
        currency: defaults.currency,
        password_min_length: defaults.password_min_length,
        password_require_uppercase: defaults.password_require_uppercase,
        password_require_lowercase: defaults.password_require_lowercase,
        password_require_numbers: defaults.password_require_numbers,
        password_require_special_chars: defaults.password_require_special_chars,
        password_expiry_days: defaults.password_expiry_days,
        session_timeout_minutes: defaults.session_timeout_minutes,
        enforce_2fa: defaults.enforce_2fa,
        max_login_attempts: defaults.max_login_attempts,
        email_notifications_enabled: defaults.email_notifications_enabled,
        notify_on_user_creation: defaults.notify_on_user_creation,
        notify_on_user_deletion: defaults.notify_on_user_deletion,
        notify_on_password_reset: defaults.notify_on_password_reset,
        notify_on_security_alerts: defaults.notify_on_security_alerts,
        notify_on_subscription_changes: defaults.notify_on_subscription_changes,
        primary_color: defaults.primary_color,
        logo_url: defaults.logo_url,
        custom_css: defaults.custom_css,
        enable_user_registration: defaults.enable_user_registration,
        enable_api_access: defaults.enable_api_access,
        enable_audit_logs: defaults.enable_audit_logs,
        enable_data_export: defaults.enable_data_export,
      })
      setError(null)
      setSuccess('Form reset to default values. Click Save to apply.')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load default settings')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const updateField = <K extends keyof OrganizationSettingsUpdate>(field: K, value: OrganizationSettingsUpdate[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const hasChanges = Object.keys(formData).length > 0

  if (loading && !settings) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading organization settings...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error && !settings) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Settings</h2>
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

  const tabs = [
    { id: 'general' as TabType, label: 'General', icon: '⚙️' },
    { id: 'security' as TabType, label: 'Security', icon: '🔒' },
    { id: 'notifications' as TabType, label: 'Notifications', icon: '🔔' },
    { id: 'branding' as TabType, label: 'Branding', icon: '🎨' },
    { id: 'features' as TabType, label: 'Features', icon: '🚀' },
  ]

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Organization Settings</h1>
            <p className="text-slate-400 mt-1">Configure your organization preferences and policies</p>
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
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 text-sm font-medium transition ${
                  activeTab === tab.id
                    ? 'text-cyan-400 border-b-2 border-cyan-400'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Settings Form */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8">
          {/* General Tab */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">General Settings</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-slate-300 mb-2">Timezone</label>
                  <select
                    value={formData.timezone ?? settings?.timezone ?? 'UTC'}
                    onChange={(e) => updateField('timezone', e.target.value)}
                    disabled={!isSuperuser}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time (ET)</option>
                    <option value="America/Chicago">Central Time (CT)</option>
                    <option value="America/Denver">Mountain Time (MT)</option>
                    <option value="America/Los_Angeles">Pacific Time (PT)</option>
                    <option value="Europe/London">London (GMT)</option>
                    <option value="Europe/Paris">Central European (CET)</option>
                    <option value="Asia/Tokyo">Tokyo (JST)</option>
                    <option value="Asia/Shanghai">China (CST)</option>
                    <option value="Asia/Karachi">Pakistan (PKT)</option>
                    <option value="Australia/Sydney">Sydney (AEST)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">Date Format</label>
                  <select
                    value={formData.date_format ?? settings?.date_format ?? 'YYYY-MM-DD'}
                    onChange={(e) => updateField('date_format', e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="DD-MM-YYYY">DD-MM-YYYY</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">Time Format</label>
                  <select
                    value={formData.time_format ?? settings?.time_format ?? '24h'}
                    onChange={(e) => updateField('time_format', e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="24h">24-hour</option>
                    <option value="12h">12-hour</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">Language</label>
                  <select
                    value={formData.language ?? settings?.language ?? 'en'}
                    onChange={(e) => updateField('language', e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                    <option value="pt">Portuguese</option>
                    <option value="zh">Chinese</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">Currency</label>
                  <select
                    value={formData.currency ?? settings?.currency ?? 'USD'}
                    onChange={(e) => updateField('currency', e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="JPY">JPY (¥)</option>
                    <option value="CAD">CAD ($)</option>
                    <option value="AUD">AUD ($)</option>
                    <option value="INR">INR (₹)</option>
                    <option value="BRL">BRL (R$)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Security Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Password Minimum Length: {formData.password_min_length ?? settings?.password_min_length ?? 8} characters
                  </label>
                  <input
                    type="range"
                    min="6"
                    max="128"
                    value={formData.password_min_length ?? settings?.password_min_length ?? 8}
                    onChange={(e) => updateField('password_min_length', parseInt(e.target.value))}
                    disabled={!isSuperuser}
                    className="w-full disabled:opacity-50"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                    <div>
                      <p className="text-white font-medium">Require Uppercase</p>
                      <p className="text-xs text-slate-400 mt-1">Password must contain uppercase letters</p>
                    </div>
                    <button
                      onClick={() => updateField('password_require_uppercase', !(formData.password_require_uppercase ?? settings?.password_require_uppercase ?? true))}
                      disabled={!isSuperuser}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                        (formData.password_require_uppercase ?? settings?.password_require_uppercase ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        (formData.password_require_uppercase ?? settings?.password_require_uppercase ?? true) ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                    <div>
                      <p className="text-white font-medium">Require Lowercase</p>
                      <p className="text-xs text-slate-400 mt-1">Password must contain lowercase letters</p>
                    </div>
                    <button
                      onClick={() => updateField('password_require_lowercase', !(formData.password_require_lowercase ?? settings?.password_require_lowercase ?? true))}
                      disabled={!isSuperuser}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                        (formData.password_require_lowercase ?? settings?.password_require_lowercase ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        (formData.password_require_lowercase ?? settings?.password_require_lowercase ?? true) ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                    <div>
                      <p className="text-white font-medium">Require Numbers</p>
                      <p className="text-xs text-slate-400 mt-1">Password must contain numbers</p>
                    </div>
                    <button
                      onClick={() => updateField('password_require_numbers', !(formData.password_require_numbers ?? settings?.password_require_numbers ?? true))}
                      disabled={!isSuperuser}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                        (formData.password_require_numbers ?? settings?.password_require_numbers ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        (formData.password_require_numbers ?? settings?.password_require_numbers ?? true) ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                    <div>
                      <p className="text-white font-medium">Require Special Characters</p>
                      <p className="text-xs text-slate-400 mt-1">Password must contain special characters</p>
                    </div>
                    <button
                      onClick={() => updateField('password_require_special_chars', !(formData.password_require_special_chars ?? settings?.password_require_special_chars ?? true))}
                      disabled={!isSuperuser}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                        (formData.password_require_special_chars ?? settings?.password_require_special_chars ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        (formData.password_require_special_chars ?? settings?.password_require_special_chars ?? true) ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm text-slate-300 mb-2">Password Expiry (days, 0 = never)</label>
                    <input
                      type="number"
                      min="0"
                      max="365"
                      value={formData.password_expiry_days ?? settings?.password_expiry_days ?? 90}
                      onChange={(e) => updateField('password_expiry_days', parseInt(e.target.value))}
                      disabled={!isSuperuser}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-slate-300 mb-2">Session Timeout (minutes)</label>
                    <input
                      type="number"
                      min="5"
                      max="1440"
                      value={formData.session_timeout_minutes ?? settings?.session_timeout_minutes ?? 60}
                      onChange={(e) => updateField('session_timeout_minutes', parseInt(e.target.value))}
                      disabled={!isSuperuser}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-slate-300 mb-2">Max Login Attempts</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={formData.max_login_attempts ?? settings?.max_login_attempts ?? 5}
                      onChange={(e) => updateField('max_login_attempts', parseInt(e.target.value))}
                      disabled={!isSuperuser}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                    <div>
                      <p className="text-white font-medium">Enforce 2FA</p>
                      <p className="text-xs text-slate-400 mt-1">Require two-factor authentication</p>
                    </div>
                    <button
                      onClick={() => updateField('enforce_2fa', !(formData.enforce_2fa ?? settings?.enforce_2fa ?? false))}
                      disabled={!isSuperuser}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                        (formData.enforce_2fa ?? settings?.enforce_2fa ?? false) ? 'bg-cyan-600' : 'bg-slate-700'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        (formData.enforce_2fa ?? settings?.enforce_2fa ?? false) ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Notification Settings</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Email Notifications</p>
                    <p className="text-xs text-slate-400 mt-1">Enable email notifications for the organization</p>
                  </div>
                  <button
                    onClick={() => updateField('email_notifications_enabled', !(formData.email_notifications_enabled ?? settings?.email_notifications_enabled ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.email_notifications_enabled ?? settings?.email_notifications_enabled ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.email_notifications_enabled ?? settings?.email_notifications_enabled ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">User Creation</p>
                    <p className="text-xs text-slate-400 mt-1">Notify when a new user is created</p>
                  </div>
                  <button
                    onClick={() => updateField('notify_on_user_creation', !(formData.notify_on_user_creation ?? settings?.notify_on_user_creation ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.notify_on_user_creation ?? settings?.notify_on_user_creation ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.notify_on_user_creation ?? settings?.notify_on_user_creation ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">User Deletion</p>
                    <p className="text-xs text-slate-400 mt-1">Notify when a user is deleted</p>
                  </div>
                  <button
                    onClick={() => updateField('notify_on_user_deletion', !(formData.notify_on_user_deletion ?? settings?.notify_on_user_deletion ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.notify_on_user_deletion ?? settings?.notify_on_user_deletion ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.notify_on_user_deletion ?? settings?.notify_on_user_deletion ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Password Reset</p>
                    <p className="text-xs text-slate-400 mt-1">Notify when a password is reset</p>
                  </div>
                  <button
                    onClick={() => updateField('notify_on_password_reset', !(formData.notify_on_password_reset ?? settings?.notify_on_password_reset ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.notify_on_password_reset ?? settings?.notify_on_password_reset ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.notify_on_password_reset ?? settings?.notify_on_password_reset ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Security Alerts</p>
                    <p className="text-xs text-slate-400 mt-1">Notify on security-related events</p>
                  </div>
                  <button
                    onClick={() => updateField('notify_on_security_alerts', !(formData.notify_on_security_alerts ?? settings?.notify_on_security_alerts ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.notify_on_security_alerts ?? settings?.notify_on_security_alerts ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.notify_on_security_alerts ?? settings?.notify_on_security_alerts ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Subscription Changes</p>
                    <p className="text-xs text-slate-400 mt-1">Notify on subscription plan changes</p>
                  </div>
                  <button
                    onClick={() => updateField('notify_on_subscription_changes', !(formData.notify_on_subscription_changes ?? settings?.notify_on_subscription_changes ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.notify_on_subscription_changes ?? settings?.notify_on_subscription_changes ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.notify_on_subscription_changes ?? settings?.notify_on_subscription_changes ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Branding Tab */}
          {activeTab === 'branding' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Branding Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm text-slate-300 mb-2">Primary Color</label>
                  <div className="flex gap-4 items-center">
                    <input
                      type="color"
                      value={formData.primary_color ?? settings?.primary_color ?? '#06b6d4'}
                      onChange={(e) => updateField('primary_color', e.target.value)}
                      className="h-12 w-20 rounded-lg border border-white/10 bg-white/5 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={formData.primary_color ?? settings?.primary_color ?? '#06b6d4'}
                      onChange={(e) => updateField('primary_color', e.target.value)}
                      placeholder="#06b6d4"
                      className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">Logo URL</label>
                  <input
                    type="text"
                    value={formData.logo_url ?? settings?.logo_url ?? ''}
                    onChange={(e) => updateField('logo_url', e.target.value || undefined)}
                    placeholder="https://example.com/logo.png"
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">Custom CSS</label>
                  <textarea
                    value={formData.custom_css ?? settings?.custom_css ?? ''}
                    onChange={(e) => updateField('custom_css', e.target.value || undefined)}
                    placeholder="/* Custom CSS styles */"
                    rows={8}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-mono"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Features Tab */}
          {activeTab === 'features' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Feature Flags</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">User Registration</p>
                    <p className="text-xs text-slate-400 mt-1">Allow new users to register</p>
                  </div>
                  <button
                    onClick={() => updateField('enable_user_registration', !(formData.enable_user_registration ?? settings?.enable_user_registration ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.enable_user_registration ?? settings?.enable_user_registration ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.enable_user_registration ?? settings?.enable_user_registration ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">API Access</p>
                    <p className="text-xs text-slate-400 mt-1">Enable API access for users</p>
                  </div>
                  <button
                    onClick={() => updateField('enable_api_access', !(formData.enable_api_access ?? settings?.enable_api_access ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.enable_api_access ?? settings?.enable_api_access ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.enable_api_access ?? settings?.enable_api_access ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Audit Logs</p>
                    <p className="text-xs text-slate-400 mt-1">Enable audit logging</p>
                  </div>
                  <button
                    onClick={() => updateField('enable_audit_logs', !(formData.enable_audit_logs ?? settings?.enable_audit_logs ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.enable_audit_logs ?? settings?.enable_audit_logs ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.enable_audit_logs ?? settings?.enable_audit_logs ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                  <div>
                    <p className="text-white font-medium">Data Export</p>
                    <p className="text-xs text-slate-400 mt-1">Allow users to export their data</p>
                  </div>
                  <button
                    onClick={() => updateField('enable_data_export', !(formData.enable_data_export ?? settings?.enable_data_export ?? true))}
                    disabled={!isSuperuser}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition disabled:opacity-50 ${
                      (formData.enable_data_export ?? settings?.enable_data_export ?? true) ? 'bg-cyan-600' : 'bg-slate-700'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      (formData.enable_data_export ?? settings?.enable_data_export ?? true) ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </div>
              </div>
            </div>
          )}

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
      </div>
    </main>
  )
}