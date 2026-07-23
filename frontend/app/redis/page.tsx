"use client"

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import {
  getRedisHealth,
  getCacheStats,
  flushCache,
  RedisHealth,
  CacheStats,
} from '../../lib/api';
import Navigation from '../../components/Navigation';

export default function RedisPage() {
  const { isAuthenticated, logout, token } = useAuth();
  const router = useRouter();
  const [health, setHealth] = useState<RedisHealth | null>(null);
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flushing, setFlushing] = useState(false);
  const [flushMessage, setFlushMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
      return;
    }

    fetchData();
  }, [isAuthenticated, router, token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [healthData, statsData] = await Promise.all([
        getRedisHealth(),
        getCacheStats(),
      ]);
      setHealth(healthData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Redis data');
    } finally {
      setLoading(false);
    }
  };

  const handleFlushCache = async () => {
    if (!confirm('Are you sure you want to flush all cache data? This action cannot be undone.')) {
      return;
    }

    try {
      setFlushing(true);
      setFlushMessage(null);
      const result = await flushCache();
      setFlushMessage(result.message);
      // Refresh stats after flush
      await fetchData();
    } catch (err) {
      setFlushMessage(err instanceof Error ? err.message : 'Failed to flush cache');
    } finally {
      setFlushing(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading Redis data...</div>
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
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Redis Data</h2>
            <p className="text-slate-300">{error}</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-6 rounded-xl bg-slate-800 px-6 py-3 text-white hover:bg-slate-700 transition"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Redis Cache Management</h1>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Sign Out
          </button>
        </div>

        {/* Health Status */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
          <h2 className="text-2xl font-semibold mb-6">Redis Health Status</h2>
          {health && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${health.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-lg font-medium">
                  Status: {health.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                </span>
              </div>
              {health.status === 'healthy' && (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-slate-400 text-sm">Version</p>
                    <p className="text-xl font-semibold text-cyan-300">{health.version}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-slate-400 text-sm">Connected Clients</p>
                    <p className="text-xl font-semibold text-green-300">{health.connected_clients}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-slate-400 text-sm">Memory Usage</p>
                    <p className="text-xl font-semibold text-purple-300">{health.used_memory_human}</p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-slate-400 text-sm">Uptime</p>
                    <p className="text-xl font-semibold text-orange-300">
                      {Math.floor((health.uptime_in_seconds || 0) / 3600)}h {(health.uptime_in_seconds || 0) % 3600}m
                    </p>
                  </div>
                </div>
              )}
              {health.status === 'unhealthy' && health.error && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                  <p className="text-red-400">Error: {health.error}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Cache Statistics */}
        {stats && !('error' in stats) && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h2 className="text-2xl font-semibold mb-6">Cache Statistics</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-slate-400 text-sm">Total Keys</p>
                <p className="text-2xl font-semibold text-cyan-300">{stats.total_keys}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-slate-400 text-sm">Memory Usage</p>
                <p className="text-2xl font-semibold text-purple-300">{stats.used_memory_human}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-slate-400 text-sm">Connected Clients</p>
                <p className="text-2xl font-semibold text-green-300">{stats.connected_clients}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-slate-400 text-sm">Cache Hits</p>
                <p className="text-2xl font-semibold text-cyan-300">{stats.hits}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-slate-400 text-sm">Cache Misses</p>
                <p className="text-2xl font-semibold text-orange-300">{stats.misses}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-slate-400 text-sm">Hit Rate</p>
                <p className="text-2xl font-semibold text-green-300">{stats.hit_rate}%</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
          <h2 className="text-2xl font-semibold mb-6">Cache Management</h2>
          <div className="space-y-4">
            <button
              onClick={handleFlushCache}
              disabled={flushing}
              className="rounded-xl bg-red-500/10 border border-red-500/30 px-6 py-3 text-red-300 hover:bg-red-500/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {flushing ? 'Flushing Cache...' : 'Flush All Cache'}
            </button>
            {flushMessage && (
              <div className={`rounded-xl border p-4 ${flushMessage.includes('successfully') ? 'border-green-500/30 bg-green-500/10 text-green-300' : 'border-red-500/30 bg-red-500/10 text-red-300'}`}>
                {flushMessage}
              </div>
            )}
            <p className="text-slate-400 text-sm">
              Warning: Flushing cache will remove all cached data. This may temporarily increase database load.
            </p>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex gap-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="rounded-xl bg-cyan-500/10 border border-cyan-500/30 px-6 py-3 text-cyan-300 hover:bg-cyan-500/20 transition"
          >
            Back to Dashboard
          </button>
          <button
            onClick={fetchData}
            className="rounded-xl bg-slate-800 border border-slate-700 px-6 py-3 text-slate-300 hover:bg-slate-700 hover:text-white transition"
          >
            Refresh Data
          </button>
        </div>
      </div>
    </main>
  );
}