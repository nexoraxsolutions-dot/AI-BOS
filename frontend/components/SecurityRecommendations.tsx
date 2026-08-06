"use client"

import { motion } from 'framer-motion'
import { Lightbulb, AlertTriangle, CheckCircle, Shield } from 'lucide-react'

interface SecurityRecommendationsProps {
  recommendations: string[]
}

export default function SecurityRecommendations({ recommendations }: SecurityRecommendationsProps) {
  const getRecommendationIcon = (recommendation: string) => {
    if (recommendation.toLowerCase().includes('enable 2fa') || recommendation.toLowerCase().includes('2fa')) {
      return <Shield className="w-5 h-5 text-cyan-400" />
    }
    if (recommendation.toLowerCase().includes('lock') || recommendation.toLowerCase().includes('unlock')) {
      return <AlertTriangle className="w-5 h-5 text-yellow-400" />
    }
    if (recommendation.toLowerCase().includes('suspicious') || recommendation.toLowerCase().includes('investigate')) {
      return <AlertTriangle className="w-5 h-5 text-red-400" />
    }
    if (recommendation.toLowerCase().includes('failed') || recommendation.toLowerCase().includes('high')) {
      return <AlertTriangle className="w-5 h-5 text-orange-400" />
    }
    if (recommendation.toLowerCase().includes('good')) {
      return <CheckCircle className="w-5 h-5 text-green-400" />
    }
    return <Lightbulb className="w-5 h-5 text-cyan-400" />
  }

  const getRecommendationColor = (recommendation: string) => {
    if (recommendation.toLowerCase().includes('good')) {
      return 'border-green-500/30 bg-green-500/5'
    }
    if (recommendation.toLowerCase().includes('suspicious') || recommendation.toLowerCase().includes('investigate')) {
      return 'border-red-500/30 bg-red-500/5'
    }
    if (recommendation.toLowerCase().includes('failed') || recommendation.toLowerCase().includes('high')) {
      return 'border-orange-500/30 bg-orange-500/5'
    }
    return 'border-cyan-500/30 bg-cyan-500/5'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <Lightbulb className="text-cyan-400" size={24} />
        <h3 className="text-xl font-semibold">Security Recommendations</h3>
      </div>

      <div className="space-y-3">
        {recommendations.map((rec, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`rounded-xl border p-4 ${getRecommendationColor(rec)}`}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                {getRecommendationIcon(rec)}
              </div>
              <div className="flex-1">
                <p className="text-sm text-slate-300">{rec}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {recommendations.length === 0 && (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <p className="text-slate-400">No recommendations at this time</p>
        </div>
      )}
    </motion.div>
  )
}