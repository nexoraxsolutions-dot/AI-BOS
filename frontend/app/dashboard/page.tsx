"use client"

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { getDashboardSummary, DashboardResponse } from '../../lib/api';
import DashboardCard from '../../components/DashboardCard';

export default function DashboardPage() {
  const { isAuthenticated, logout, token } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
      return;
    }

    async function fetchData() {
      try {
        setLoading(true);
        const result = await getDashboardSummary();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [isAuthenticated, router, token]);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading dashboard...</div>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Dashboard</h2>
            <p className="text-slate-300">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-6 rounded-xl bg-slate-800 px-6 py-3 text-white hover:bg-slate-700 transition"
            >
              Return to Home
            </button>
          </div>
        </div>
      </main>
    );
  }

  const summary = data?.summary;

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Dashboard</h1>
            {data?.message && (
              <p className="text-slate-400 mt-1">{data.message}</p>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Sign Out
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <DashboardCard
            title="Total Users"
            value={summary?.total_users?.toLocaleString() ?? '0'}
            description={`${summary?.active_users?.toLocaleString() ?? '0'} active`}
          />
          <DashboardCard
            title="Companies"
            value={summary?.total_companies?.toLocaleString() ?? '0'}
            description={`${summary?.recent_companies_count ?? 0} new this month`}
          />
          <DashboardCard
            title="Monthly Sales"
            value={summary ? `$${(summary.total_sales_monthly / 1000000).toFixed(1)}M` : '$0'}
            description="Revenue tracked this month"
          />
          <DashboardCard
            title="Tasks"
            value={summary?.total_tasks_pending?.toLocaleString() ?? '0'}
            description="Projects in progress"
          />
        </div>

        {/* Navigation Cards */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h3 className="text-xl font-semibold mb-4">Management</h3>
            <div className="space-y-3">
              <button
                onClick={() => router.push('/users')}
                className="w-full rounded-xl bg-cyan-500/10 border border-cyan-500/30 px-5 py-3 text-cyan-300 hover:bg-cyan-500/20 transition text-left"
              >
                View All Users
              </button>
              <button
                onClick={() => router.push('/companies')}
                className="w-full rounded-xl bg-green-500/10 border border-green-500/30 px-5 py-3 text-green-300 hover:bg-green-500/20 transition text-left"
              >
                Manage Companies
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full rounded-xl bg-purple-500/10 border border-purple-500/30 px-5 py-3 text-purple-300 hover:bg-purple-500/20 transition text-left">
                System Settings
              </button>
              <button className="w-full rounded-xl bg-orange-500/10 border border-orange-500/30 px-5 py-3 text-orange-300 hover:bg-orange-500/20 transition text-left">
                View Reports
              </button>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-sm">
                <div className="h-2 w-2 rounded-full bg-cyan-400" />
                <span className="text-slate-300">
                  {summary?.recent_users_count ?? 0} new users registered in the last 30 days
                </span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <div className="h-2 w-2 rounded-full bg-green-400" />
                <span className="text-slate-300">
                  {summary?.recent_companies_count ?? 0} new companies onboarded
                </span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <div className="h-2 w-2 rounded-full bg-purple-400" />
                <span className="text-slate-300">
                  {summary?.active_users ?? 0} active users on the platform
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full rounded-xl bg-cyan-500/10 border border-cyan-500/30 px-5 py-3 text-cyan-300 hover:bg-cyan-500/20 transition text-left">
                View All Users
              </button>
              <button className="w-full rounded-xl bg-green-500/10 border border-green-500/30 px-5 py-3 text-green-300 hover:bg-green-500/20 transition text-left">
                Manage Companies
              </button>
              <button className="w-full rounded-xl bg-purple-500/10 border border-purple-500/30 px-5 py-3 text-purple-300 hover:bg-purple-500/20 transition text-left">
                System Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}