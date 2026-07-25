"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import { getMyProfile, updateMyProfile, changeMyPassword, User } from '../../lib/api'

export default function ProfilePage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [profile, setProfile] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Profile form
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    username: '',
    email: '',
  })
  const [profileLoading, setProfileLoading] = useState(false)

  // Password form
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [passwordLoading, setPasswordLoading] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchProfile()
  }, [isAuthenticated, router])

  async function fetchProfile() {
    try {
      setLoading(true)
      const data = await getMyProfile()
      setProfile(data)
      setProfileForm({
        full_name: data.full_name || '',
        username: '',
        email: data.email,
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const clearMessages = () => {
    setError(null)
    setSuccessMessage(null)
  }

  const handleProfileUpdate = async () => {
    clearMessages()
    setProfileLoading(true)
    try {
      const updated = await updateMyProfile({
        full_name: profileForm.full_name || undefined,
        username: profileForm.username || undefined,
        email: profileForm.email || undefined,
      })
      setProfile(updated)
      setSuccessMessage('Profile updated successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setProfileLoading(false)
    }
  }

  const handlePasswordChange = async () => {
    clearMessages()
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('New passwords do not match')
      return
    }
    if (passwordForm.new_password.length < 8) {
      setError('New password must be at least 8 characters long')
      return
    }
    setPasswordLoading(true)
    try {
      await changeMyPassword(passwordForm.current_password, passwordForm.new_password)
      setSuccessMessage('Password changed successfully')
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password')
    } finally {
      setPasswordLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-4xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading profile...</div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">My Profile</h1>
            <p className="text-slate-400 mt-1">Manage your account settings and password</p>
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

        {/* Messages */}
        {error && (
          <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
            {error}
          </div>
        )}
        {successMessage && (
          <div className="rounded-xl bg-green-500/10 border border-green-500/30 p-4 text-sm text-green-400">
            {successMessage}
          </div>
        )}

        {/* Profile Info */}
        {profile && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold">Account Information</h2>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">User ID</label>
                  <p className="text-lg font-medium">{profile.id}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Status</label>
                  <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                    profile.is_active
                      ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                      : 'bg-red-500/10 text-red-400 border border-red-500/30'
                  }`}>
                    {profile.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Role</label>
                  <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                    profile.is_superuser
                      ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                      : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
                  }`}>
                    {profile.is_superuser ? 'Admin' : 'User'}
                  </span>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Company ID</label>
                  <p className="text-lg font-medium">{profile.company_id || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Email Verified</label>
                  <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                    profile.is_email_verified
                      ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                      : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                  }`}>
                    {profile.is_email_verified ? 'Verified' : 'Not Verified'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Profile */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10">
            <h2 className="text-2xl font-semibold">Edit Profile</h2>
          </div>
          <div className="p-8 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Email</label>
                <input
                  type="email"
                  value={profileForm.email}
                  onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={profileForm.full_name}
                  onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Your full name"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Username</label>
                <input
                  type="text"
                  value={profileForm.username}
                  onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Choose a username"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleProfileUpdate}
                disabled={profileLoading}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {profileLoading ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          </div>
        </div>

        {/* Change Password */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10">
            <h2 className="text-2xl font-semibold">Change Password</h2>
          </div>
          <div className="p-8 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Current Password</label>
                <input
                  type="password"
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Current password"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">New Password</label>
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Min 8 characters"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Confirm New Password</label>
                <input
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Confirm new password"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={handlePasswordChange}
                disabled={passwordLoading || !passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {passwordLoading ? 'Changing...' : 'Change Password'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}