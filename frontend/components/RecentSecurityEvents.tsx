"use client"

import { motion } from 'framer-motion'
import { AlertTriangle, Shield, Key, UserCheck, Activity, Lock } from 'lucide-react'

interface SecurityEvent {
  id: number
  action: string
  user_id?: number
  ip_address?: string
  created_at: string
  details?: Record<string, unknown>
}

interface RecentSecurityEventsProps {
  events: SecurityEvent[]
}

export default function RecentSecurityEvents({ events }: RecentSecurityEventsProps) {
  const getEventIcon = (action: string) => {
    switch (action) {
      case 'login_failed':
        return <AlertTriangle className="w-5 h-5 text-red-400" />
      case 'account_locked':
        return <Lock className="w-5 h-5 text-red-400" />
      case 'password_changed':
        return <Key className="w-5 h-5 text-yellow-400" />
      case '2fa_enabled':
        return <Shield className="w-5 h-5 text-green-400" />
      case '2fa_disabled':
        return <Shield className="w-5 h-5 text-orange-400" />
      case 'suspicious_activity':
        return <Activity className="w-5 h-5 text-red-400" />
      default:
        return <Activity className="w-5 h-5 text-slate-400" />
    }
  }

  const getEventColor = (action: string) => {
    switch (action) {
      case 'login_failed':
      case 'account_locked':
      case 'suspicious_activity':
        return 'border-red-500/30 bg-red-500/5'
      case 'password_changed':
        return 'border-yellow-500/30 bg-yellow-500/5'
      case '2fa_enabled':
        return 'border-green-500/30 bg-green-500/5'
      case '2fa_disabled':
        return 'border-orange-500/30 bg-orange-500/5'
      default:
        return 'border-slate-500/30 bg-slate-500/5'
    }
  }

  const formatAction = (action: string) => {
    return action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)

    if (hours < 1) return 'Just now'
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString()
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <Activity className="text-cyan-400" size={24} />
        <h3 className="text-xl font-semibold">Recent Security Events</h3>
      </div>

      <div className="space-y-3">
        {events.length === 0 ? (
          <p className="text-slate-400 text-sm text-center py-8">No recent security events</p>
        ) : (
          events.map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`rounded-xl border p-4 ${getEventColor(event.action)}`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {getEventIcon(event.action)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-white truncate">
                      {formatAction(event.action)}
                    </h4>
                    <span className="text-xs text-slate-400 whitespace-nowrap ml-2">
                      {formatDate(event.created_at)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    {event.ip_address && (
                      <span className="font-mono">IP: {event.ip_address}</span>
                    )}
                    {event.user_id && (
                      <span>User ID: {event.user_id}</span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  )
}