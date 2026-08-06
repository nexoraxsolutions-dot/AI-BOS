'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../../context/AuthContext'
import { setup2FA, verify2FA, get2FAStatus, regenerateBackupCodes, getBackupCodesRemaining, disable2FA } from '../../../lib/api'

type SetupStep = 'intro' | 'scan' | 'verify' | 'backup-codes' | 'complete'

export default function TwoFactorSetupPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  const [step, setStep] = useState<SetupStep>('intro')
  const [secret, setSecret] = useState('')
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [verifyToken, setVerifyToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [is2FAEnabled, setIs2FAEnabled] = useState(false)
  const [remainingCodes, setRemainingCodes] = useState(0)
  const [disablePassword, setDisablePassword] = useState('')
  const [showDisableConfirm, setShowDisableConfirm] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    loadStatus()
  }, [isAuthenticated, router])

  async function loadStatus() {
    try {
      const status = await get2FAStatus()
      setIs2FAEnabled(status.is_2fa_enabled)
      if (status.is_2fa_enabled) {
        const remaining = await getBackupCodesRemaining()
        setRemainingCodes(remaining.remaining)
      }
    } catch {
      // Not critical
    }
  }

  async function handleSetup() {
    setLoading(true)
    setError(null)
    try {
      const response = await setup2FA()
      setSecret(response.secret)
      setQrCodeUrl(response.qr_code_url)
      setBackupCodes(response.backup_codes)
      setStep('scan')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize 2FA setup')
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify() {
    setLoading(true)
    setError(null)
    try {
      const response = await verify2FA(verifyToken)
      setMessage(response.message)
      setStep('complete')
      setIs2FAEnabled(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid token. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegenerateCodes() {
    setLoading(true)
    setError(null)
    try {
      const response = await regenerateBackupCodes()
      setBackupCodes(response.backup_codes)
      setStep('backup-codes')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate backup codes')
    } finally {
      setLoading(false)
    }
  }

  async function handleDisable() {
    setLoading(true)
    setError(null)
    try {
      await disable2FA(disablePassword)
      setIs2FAEnabled(false)
      setShowDisableConfirm(false)
      setDisablePassword('')
      setMessage('Two-factor authentication has been disabled.')
      setStep('intro')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable 2FA')
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto flex max-w-6xl items-center justify-center">
        <div className="w-full max-w-2xl">
          <div className="mb-8 text-center">
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="mt-4 text-4xl font-semibold">Two-Factor Authentication</h1>
            <p className="mt-2 text-slate-400">
              Add an extra layer of security to your account
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl">
            {error && (
              <div className="mb-6 rounded-xl bg-red-900/50 border border-red-700 p-4 text-red-200" role="alert">
                <p className="text-sm">{error}</p>
              </div>
            )}

            {message && (
              <div className="mb-6 rounded-xl bg-emerald-900/50 border border-emerald-700 p-4 text-emerald-200" role="alert">
                <p className="text-sm">{message}</p>
              </div>
            )}

            {/* Intro Step */}
            {step === 'intro' && (
              <div className="space-y-6">
                {is2FAEnabled ? (
                  <div>
                    <div className="bg-emerald-900/50 border border-emerald-700 rounded-xl p-4 mb-6">
                      <p className="text-emerald-200 font-medium">2FA is currently enabled</p>
                      <p className="text-emerald-300 text-sm mt-1">
                        Remaining backup codes: {remainingCodes}
                      </p>
                    </div>

                    <div className="space-y-3">
                      <button
                        onClick={handleRegenerateCodes}
                        disabled={loading}
                        className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
                      >
                        {loading ? 'Regenerating...' : 'Regenerate Backup Codes'}
                      </button>

                      <button
                        onClick={() => setShowDisableConfirm(true)}
                        className="w-full rounded-2xl border border-red-700 bg-red-900/30 px-5 py-3 text-base font-semibold text-red-300 transition hover:bg-red-900/50"
                      >
                        Disable 2FA
                      </button>
                    </div>

                    {showDisableConfirm && (
                      <div className="mt-6 p-4 rounded-xl bg-slate-900 border border-slate-700">
                        <p className="text-sm text-slate-300 mb-4">
                          Enter your password to confirm disabling 2FA:
                        </p>
                        <input
                          type="password"
                          value={disablePassword}
                          onChange={(e) => setDisablePassword(e.target.value)}
                          className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 mb-3"
                          placeholder="Your password"
                        />
                        <div className="flex gap-3">
                          <button
                            onClick={handleDisable}
                            disabled={loading || !disablePassword}
                            className="flex-1 rounded-2xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50"
                          >
                            {loading ? 'Disabling...' : 'Confirm Disable'}
                          </button>
                          <button
                            onClick={() => setShowDisableConfirm(false)}
                            className="flex-1 rounded-2xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <div className="bg-blue-900/30 border border-blue-700 rounded-xl p-4 mb-6">
                      <p className="text-blue-200 text-sm">
                        Two-factor authentication adds an extra layer of security to your account.
                        You will need to enter a code from your authenticator app in addition to your password.
                      </p>
                    </div>

                    <button
                      onClick={handleSetup}
                      disabled={loading}
                      className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
                    >
                      {loading ? 'Setting up...' : 'Set Up Two-Factor Authentication'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Scan QR Code Step */}
            {step === 'scan' && (
              <div className="space-y-6">
                <div className="bg-blue-900/30 border border-blue-700 rounded-xl p-4">
                  <p className="text-blue-200 text-sm">
                    Scan the QR code below with your authenticator app (e.g., Google Authenticator, Authy).
                    If you cannot scan the code, enter the secret key manually.
                  </p>
                </div>

                <div className="flex justify-center">
                  <div className="bg-white p-4 rounded-xl">
                    <div className="w-48 h-48 bg-slate-200 flex items-center justify-center text-slate-500 text-sm text-center">
                      <div>
                        <p>QR Code URL:</p>
                        <p className="text-xs mt-2 break-all">{qrCodeUrl}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-xl p-4">
                  <p className="text-sm text-slate-300 mb-2">Secret Key (manual entry):</p>
                  <code className="text-cyan-300 text-sm break-all font-mono">{secret}</code>
                </div>

                <div className="border-t border-slate-700 pt-6">
                  <p className="text-sm text-slate-300 mb-4">
                    After scanning, enter the 6-digit code from your authenticator app:
                  </p>
                  <input
                    type="text"
                    value={verifyToken}
                    onChange={(e) => setVerifyToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    maxLength={6}
                    className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white text-center text-2xl tracking-[0.5em] outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 mb-4"
                    placeholder="000000"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                  />
                  <button
                    onClick={handleVerify}
                    disabled={loading || verifyToken.length !== 6}
                    className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
                  >
                    {loading ? 'Verifying...' : 'Verify & Enable'}
                  </button>
                </div>
              </div>
            )}

            {/* Backup Codes Step */}
            {step === 'backup-codes' && (
              <div className="space-y-6">
                <div className="bg-amber-900/30 border border-amber-700 rounded-xl p-4">
                  <p className="text-amber-200 text-sm font-medium mb-2">Save These Backup Codes</p>
                  <p className="text-amber-300 text-xs">
                    Each code can only be used once. Store them in a secure location.
                    You will need these if you lose access to your authenticator app.
                  </p>
                </div>

                <div className="bg-slate-900 border border-slate-700 rounded-xl p-6">
                  <div className="grid grid-cols-1 gap-3">
                    {backupCodes.map((code, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <span className="text-slate-500 text-sm w-8">{index + 1}.</span>
                        <code className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-cyan-300 font-mono text-sm text-center tracking-wider">
                          {code}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => setStep('complete')}
                  className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400"
                >
                  I've Saved My Backup Codes
                </button>
              </div>
            )}

            {/* Complete Step */}
            {step === 'complete' && (
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-emerald-900/50 border-2 border-emerald-500 rounded-full flex items-center justify-center mb-6">
                  <svg className="w-8 h-8 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-3">2FA Enabled Successfully</h2>
                <p className="text-slate-400 mb-8">
                  Your account is now protected with two-factor authentication.
                </p>
                <div className="space-y-3">
                  <button
                    onClick={() => setStep('backup-codes')}
                    className="w-full rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-base font-medium text-slate-300 hover:bg-slate-800"
                  >
                    View Backup Codes Again
                  </button>
                  <Link
                    href="/profile"
                    className="block w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 text-center hover:bg-cyan-400"
                  >
                    Back to Profile
                  </Link>
                </div>
              </div>
            )}
          </div>

          <p className="mt-6 text-center text-sm text-slate-400">
            <Link href="/profile" className="text-cyan-400 hover:text-cyan-300 font-medium transition">
              Back to Profile
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}