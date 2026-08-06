"use client"

import { motion } from 'framer-motion'
import { Shield, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react'

interface SecurityScoreCardProps {
  score: number
  recommendations: string[]
}

export default function SecurityScoreCard({ score, recommendations }: SecurityScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    if (score >= 40) return 'text-orange-400'
    return 'text-red-400'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'from-green-500/10 to-green-600/10 border-green-500/30'
    if (score >= 60) return 'from-yellow-500/10 to-yellow-600/10 border-yellow-500/30'
    if (score >= 40) return 'from-orange-500/10 to-orange-600/10 border-orange-500/30'
    return 'from-red-500/10 to-red-600/10 border-red-500/30'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-16 h-16 text-green-400" />
    if (score >= 60) return <Shield className="w-16 h-16 text-yellow-400" />
    if (score >= 40) return <AlertTriangle className="w-16 h-16 text-orange-400" />
    return <AlertTriangle className="w-16 h-16 text-red-400" />
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    return 'Needs Improvement'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border bg-gradient-to-br ${getScoreBgColor(score)} p-8 backdrop-blur-xl`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="text-cyan-400" size={24} />
            <h2 className="text-2xl font-semibold">Security Score</h2>
          </div>
          
          <div className="flex items-end gap-4 mb-4">
            <div className={`text-6xl font-bold ${getScoreColor(score)}`}>
              {score}
            </div>
            <div className="mb-2">
              <div className={`text-lg font-medium ${getScoreColor(score)}`}>
                {getScoreLabel(score)}
              </div>
              <div className="text-sm text-slate-400">out of 100</div>
            </div>
          </div>

          {recommendations.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Recommendations
              </h3>
              <ul className="space-y-2">
                {recommendations.slice(0, 3).map((rec, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-cyan-400 mt-0.5">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="hidden lg:block">
          {getScoreIcon(score)}
        </div>
      </div>
    </motion.div>
  )
}