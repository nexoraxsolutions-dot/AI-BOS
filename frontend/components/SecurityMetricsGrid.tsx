"use client"

import { motion } from 'framer-motion'
import { 
  Users, 
  ShieldCheck, 
  Lock, 
  AlertTriangle, 
  Monitor, 
  Activity,
  UserX,
  KeyRound
} from 'lucide-react'
import { SecurityDashboardData } from '../lib/api'

interface SecurityMetricsGridProps {
  data: SecurityDashboardData
}

export default function SecurityMetricsGrid({ data }: SecurityMetricsGridProps) {
  const metrics = [
    {
      title: 'Total Users',
      value: data.total_users.toLocaleString(),
      subtitle: `${data.users_with_2fa.toLocaleString()} with 2FA enabled`,
      icon: Users,
      color: 'cyan',
      trend: null
    },
    {
      title: '2FA Adoption',
      value: data.total_users > 0 ? `${Math.round((data.users_with_2fa / data.total_users) * 100)}%` : '0%',
      subtitle: `${data.users_with_2fa.toLocaleString()} users enabled`,
      icon: ShieldCheck,
      color: 'green',
      trend: data.two_fa_enabled_30d > 0 ? 'up' : null
    },
    {
      title: 'Locked Accounts',
      value: data.locked_accounts.toLocaleString(),
      subtitle: 'Currently locked',
      icon: Lock,
      color: data.locked_accounts > 0 ? 'red' : 'green',
      trend: data.account_lockouts_30d > 0 ? 'up' : null
    },
    {
      title: 'Failed Logins (24h)',
      value: data.failed_logins_24h.toLocaleString(),
      subtitle: `${data.failed_logins_7d.toLocaleString()} in last 7 days`,
      icon: AlertTriangle,
      color: data.failed_logins_24h > 10 ? 'orange' : 'green',
      trend: data.failed_logins_24h > 10 ? 'up' : null
    },
    {
      title: 'Active Sessions',
      value: data.active_sessions.toLocaleString(),
      subtitle: 'Currently active',
      icon: Monitor,
      color: 'cyan',
      trend: null
    },
    {
      title: 'Password Changes',
      value: data.password_changes_30d.toLocaleString(),
      subtitle: 'Last 30 days',
      icon: KeyRound,
      color: 'purple',
      trend: null
    },
    {
      title: 'Users with Failed Logins',
      value: data.users_with_failed_logins.toLocaleString(),
      subtitle: 'Have failed attempts',
      icon: UserX,
      color: data.users_with_failed_logins > 0 ? 'orange' : 'green',
      trend: null
    },
    {
      title: 'Suspicious IPs',
      value: data.suspicious_ips_count.toLocaleString(),
      subtitle: 'Flagged in last 24h',
      icon: Activity,
      color: data.suspicious_ips_count > 0 ? 'red' : 'green',
      trend: data.suspicious_ips_count > 0 ? 'up' : null
    }
  ]

  const getColorClasses = (color: string) => {
    const colors = {
      cyan: 'from-cyan-500/10 to-cyan-600/10 border-cyan-500/30 text-cyan-400',
      green: 'from-green-500/10 to-green-600/10 border-green-500/30 text-green-400',
      red: 'from-red-500/10 to-red-600/10 border-red-500/30 text-red-400',
      orange: 'from-orange-500/10 to-orange-600/10 border-orange-500/30 text-orange-400',
      purple: 'from-purple-500/10 to-purple-600/10 border-purple-500/30 text-purple-400',
    }
    return colors[color as keyof typeof colors] || colors.cyan
  }

  const getTrendIcon = (trend: string | null) => {
    if (!trend) return null
    return trend === 'up' ? (
      <span className="text-xs text-red-400 ml-2">↑ High</span>
    ) : (
      <span className="text-xs text-green-400 ml-2">↓ Low</span>
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric, index) => {
        const Icon = metric.icon
        return (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`rounded-2xl border bg-gradient-to-br ${getColorClasses(metric.color)} p-6 backdrop-blur-xl`}
          >
            <div className="flex items-start justify-between mb-4">
              <Icon size={24} className={getColorClasses(metric.color).split(' ')[3]} />
              {getTrendIcon(metric.trend)}
            </div>
            
            <div className="space-y-1">
              <h3 className="text-sm font-medium text-slate-400">{metric.title}</h3>
              <div className="text-3xl font-bold text-white">{metric.value}</div>
              <p className="text-xs text-slate-400">{metric.subtitle}</p>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}