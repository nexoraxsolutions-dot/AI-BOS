"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import { 
  getSecurityDashboardSummary, 
  getSecurityScore,
  SecurityDashboardData 
} from '../../../lib/api'
import Sidebar from '../../../components/Sidebar'
import SecurityScoreCard from '../../../components/SecurityScoreCard'
import SecurityMetricsGrid from '../../../components/SecurityMetricsGrid'
import RecentSecurityEvents from '../../../components/RecentSecurityEvents'
import SecurityRecommendations from '../../../components/SecurityRecommendations'

export default function SecurityDashboardPage() {
  const { isAuthenticated, token } = useAuth()
  const router = useRouter()
  const [data, setData] = useState<SecurityDashboardData | null>(null)
  const [scoreData, setScoreData] = useState<{ security_score: number; recommendations: string[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }

    async function fetchData() {
      try {
        setLoading(true)
        const [dashboardData, scoreResult] = await Promise.all([
          getSecurityDashboardSummary(),
          getSecurityScore()
        ])
        setData(dashboardData)
        setScoreData(scoreResult)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load security dashboard')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [isAuthenticated, router, token])

  if (loading) {
    return (
      <Sidebar>
        <div className="flex items-center justify-center h-96">
          <div className="text-cyan-400 text-xl animate-pulse">Loading security dashboard...</div>
        </div>
      </Sidebar>
    )
  }

  if (error) {
    return (
      <Sidebar>
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
          <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Security Dashboard</h2>
          <p className="text-slate-300">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="mt-6 rounded-xl bg-slate-800 px-6 py-3 text-white hover:bg-slate-700 transition"
          >
            Return to Dashboard
          </button>
        </div>
      </Sidebar>
    )
  }

  if (!data) {
    return null
  }

  return (
    <Sidebar>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">Security</p>
          <h1 className="text-4xl font-semibold mt-2">Security Dashboard</h1>
          <p className="text-slate-400 mt-2">Monitor and manage your security posture</p>
        </div>

        {/* Security Score */}
        {scoreData && (
          <SecurityScoreCard 
            score={scoreData.security_score} 
            recommendations={scoreData.recommendations}
          />
        )}

        {/* Metrics Grid */}
        <SecurityMetricsGrid data={data} />

        {/* Recent Events and Recommendations */}
        <div className="grid gap-6 lg:grid-cols-2">
          <RecentSecurityEvents events={data.recent_events} />
          {scoreData && scoreData.recommendations.length > 0 && (
            <SecurityRecommendations recommendations={scoreData.recommendations} />
          )}
        </div>
      </div>
    </Sidebar>
  )
}