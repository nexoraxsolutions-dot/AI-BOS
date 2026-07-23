"use client"

import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'

export default function Navigation() {
  const router = useRouter()
  const { isAuthenticated, logout } = useAuth()

  if (!isAuthenticated) {
    return null
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  return (
    <nav className="border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto max-w-6xl px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-cyan-300 hover:text-cyan-400 transition font-semibold"
            >
              AI-BOS
            </button>
            <div className="flex gap-6">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-sm text-slate-300 hover:text-white transition"
              >
                Dashboard
              </button>
              <button
                onClick={() => router.push('/users')}
                className="text-sm text-slate-300 hover:text-white transition"
              >
                Users
              </button>
              <button
                onClick={() => router.push('/companies')}
                className="text-sm text-slate-300 hover:text-white transition"
              >
                Companies
              </button>
              <button
                onClick={() => router.push('/redis')}
                className="text-sm text-slate-300 hover:text-white transition"
              >
                Redis
              </button>
              <button
                onClick={() => router.push('/environment-variables')}
                className="text-sm text-slate-300 hover:text-white transition"
              >
                Environment Variables
              </button>
              <button
                onClick={() => router.push('/profile')}
                className="text-sm text-slate-300 hover:text-white transition"
              >
                Profile
              </button>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Sign Out
          </button>
        </div>
      </div>
    </nav>
  )
}