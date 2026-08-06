"use client"

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import Sidebar from '../../components/Sidebar'
import { Sparkles } from 'lucide-react'

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-dark-bg">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
            <Sparkles className="text-white" size={22} />
          </div>
          <div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
          <p className="text-sm font-medium text-slate-500 dark:text-dark-muted">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <Sidebar>{children}</Sidebar>
}