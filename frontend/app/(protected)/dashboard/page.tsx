"use client"

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';
import { getDashboardSummary, DashboardResponse, DashboardSummary } from '../../../lib/api';
import { listUserCompanies, switchCompany, UserCompanyOut } from '../../../lib/api';
import StatCard from '../../../components/StatCard';
import { ChartContainer, AreaChart, DonutChart } from '../../../components/ChartContainer';
import StatusBadge from '../../../components/StatusBadge';
import {
  DollarSign, Users, Ticket, Briefcase, Sparkles, ArrowRight,
  CheckCircle2, UserPlus, FileText, TrendingUp, ChevronDown, Building2,
} from 'lucide-react';

const DEMO_SUMMARY: DashboardSummary = {
  total_users: 248,
  active_users: 186,
  total_companies: 12,
  total_sales_monthly: 1840000,
  total_tasks_pending: 84,
  recent_users_count: 32,
  recent_companies_count: 3,
};

const fmtMoney = (n: number) =>
  n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(2)}M` : `$${(n / 1_000).toFixed(1)}k`;

const salesSeries = [
  { name: 'Revenue', color: '#8B5CF6', values: [42, 48, 45, 52, 58, 65] },
  { name: 'Deals', color: '#3B82F6', values: [120, 135, 128, 150, 162, 178] },
];
const salesLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

const revenueSources = [
  { label: 'Direct', value: 45, color: '#635BFF' },
  { label: 'Referral', value: 25, color: '#8B5CF6' },
  { label: 'Social Media', value: 15, color: '#3B82F6' },
  { label: 'Others', value: 15, color: '#94A3B8' },
];

const projects = [
  { name: 'Website Redesign', progress: 78, status: 'On Track', variant: 'ontrack' as const },
  { name: 'Mobile App Launch', progress: 45, status: 'In Progress', variant: 'progress' as const },
  { name: 'Q4 Marketing Campaign', progress: 30, status: 'At Risk', variant: 'risk' as const },
  { name: 'API Integration', progress: 92, status: 'Completed', variant: 'completed' as const },
  { name: 'Customer Portal', progress: 60, status: 'In Progress', variant: 'progress' as const },
];

const tasks = [
  { text: 'Review Q3 financial report', time: '10:00 AM', done: false },
  { text: 'Call with Acme Corp', time: '11:30 AM', done: false },
  { text: 'Approve marketing budget', time: '01:00 PM', done: true },
  { text: 'Update sales pipeline', time: '03:00 PM', done: false },
];

const activities = [
  { icon: UserPlus, text: 'Sarah Chen added a new lead', time: '2 min ago', color: 'bg-emerald-500' },
  { icon: FileText, text: 'Invoice #1024 was generated', time: '1 hour ago', color: 'bg-blue-500' },
  { icon: TrendingUp, text: 'Revenue target 92% achieved', time: '3 hours ago', color: 'bg-brand-600' },
  { icon: CheckCircle2, text: 'Project "API Integration" completed', time: '5 hours ago', color: 'bg-emerald-500' },
];

export default function DashboardPage() {
  const { isAuthenticated, token, user, refreshUser } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [companies, setCompanies] = useState<UserCompanyOut[]>([]);
  const [switching, setSwitching] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
      return;
    }

    async function fetchData() {
      try {
        setLoading(true);
        const [summaryResult, companiesResult] = await Promise.all([
          getDashboardSummary(),
          listUserCompanies(),
        ]);
        setData(summaryResult);
        setCompanies(companiesResult.items);
      } catch {
        setData({ summary: DEMO_SUMMARY, message: 'Showing sample data' });
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [isAuthenticated, router, token]);

  const activeCompany = companies.find((c) => c.is_current) ?? companies[0] ?? null;

  async function handleSwitch(companyId: number) {
    setSwitching(true);
    setWorkspaceOpen(false);
    try {
      await switchCompany(companyId);
      await refreshUser();
      router.refresh();
    } catch (err) {
      // eslint-disable-next-line no-alert
      alert(err instanceof Error ? err.message : 'Failed to switch workspace');
    } finally {
      setSwitching(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-dark-bg">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  const summary = data?.summary ?? DEMO_SUMMARY;

  return (
    <div className="min-h-screen bg-slate-50 py-6 dark:bg-dark-bg">
      <div className="mx-auto max-w-7xl space-y-6 px-4 sm:px-6">
        {/* Page header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-dark-text">
              Dashboard
            </h1>
            <p className="text-sm text-slate-500 dark:text-dark-muted">
              {activeCompany
                ? `${activeCompany.name} — here is your business at a glance.`
                : data?.message ?? 'Welcome back — here is your business at a glance.'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {companies.length > 1 && (
              <div className="relative">
                <button
                  onClick={() => setWorkspaceOpen((v) => !v)}
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-dark-border dark:bg-white/5 dark:text-dark-text dark:hover:bg-white/10"
                >
                  <Building2 size={16} />
                  {activeCompany?.name ?? 'Switch workspace'}
                  <ChevronDown size={16} />
                </button>
                {workspaceOpen && (
                  <div className="absolute right-0 z-20 mt-2 w-72 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl dark:border-dark-border dark:bg-dark-surface">
                    <div className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-dark-muted">
                      Switch workspace
                    </div>
                    {companies.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => handleSwitch(c.id)}
                        disabled={switching}
                        className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition hover:bg-slate-50 dark:hover:bg-white/5 ${
                          c.is_current ? 'bg-cyan-500/5' : ''
                        }`}
                      >
                        <span className="flex flex-col">
                          <span className={`font-medium ${c.is_current ? 'text-cyan-600 dark:text-cyan-300' : 'text-slate-700 dark:text-dark-text'}`}>
                            {c.name}
                          </span>
                          <span className="text-xs text-slate-500 dark:text-dark-muted">
                            {c.domain} · {c.role ?? 'member'}
                          </span>
                        </span>
                        {c.is_current && <span className="text-xs text-cyan-600 dark:text-cyan-300">Current</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            <button className="btn-brand self-start sm:self-auto">
              <Sparkles size={16} /> Generate Report
            </button>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Total Revenue"
            value={fmtMoney(summary.total_sales_monthly)}
            accent="brand"
            icon={<DollarSign size={20} />}
            trend={{ value: '12.5%', direction: 'up', label: 'vs last month' }}
          />
          <StatCard
            label="New Leads"
            value={String(summary.recent_users_count)}
            accent="blue"
            icon={<Users size={20} />}
            trend={{ value: '8.2%', direction: 'up', label: 'vs last month' }}
          />
          <StatCard
            label="Open Tickets"
            value={String(summary.total_tasks_pending)}
            accent="amber"
            icon={<Ticket size={20} />}
            trend={{ value: '5.2%', direction: 'down', label: 'vs last month' }}
          />
          <StatCard
            label="Active Projects"
            value="24"
            accent="violet"
            icon={<Briefcase size={20} />}
            trend={{ value: '3.1%', direction: 'up', label: 'vs last month' }}
          />
        </div>

        {/* Analytics: Sales Overview (2/3) + Revenue by Source (1/3) */}
        <div className="grid gap-4 lg:grid-cols-3">
          <ChartContainer
            title="Sales Overview"
            subtitle="Revenue vs Deals — last 6 months"
            className="lg:col-span-2"
          >
            <AreaChart labels={salesLabels} series={salesSeries} height={220} />
          </ChartContainer>

          <ChartContainer title="Revenue by Source" subtitle="This month">
            <DonutChart
              data={revenueSources}
              centerLabel="Total"
              centerValue={fmtMoney(summary.total_sales_monthly)}
            />
          </ChartContainer>
        </div>

        {/* AI Insights */}
        <div className="overflow-hidden rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 to-violet-100 p-6 dark:border-brand-500/20 dark:from-brand-600/10 dark:to-violet-600/10">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-4">
              <div className="glow-ring flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-gradient">
                <Sparkles className="text-white" size={22} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900 dark:text-dark-text">AI Insights</h3>
                <p className="mt-1 max-w-xl text-sm text-slate-600 dark:text-dark-muted">
                  Revenue is up by <span className="font-semibold text-brand-600">12.5% this month</span>. Deal velocity improved across the Referral channel — consider reallocating budget from Social Media to Direct.
                </p>
              </div>
            </div>
            <button className="btn-brand shrink-0">
              View Full Insights <ArrowRight size={16} />
            </button>
          </div>
        </div>

        {/* Projects overview + side widgets */}
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="card p-5 sm:p-6 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900 dark:text-dark-text">Projects Overview</h3>
              <button className="text-sm font-medium text-brand-600 hover:text-brand-700">View all</button>
            </div>
            <div className="space-y-4">
              {projects.map((p) => (
                <div key={p.name} className="flex items-center gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium text-slate-700 dark:text-dark-text">{p.name}</p>
                      <span className="text-xs font-medium text-slate-500 dark:text-dark-muted">{p.progress}%</span>
                    </div>
                    <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
                      <div className="h-full rounded-full bg-brand-600" style={{ width: `${p.progress}%` }} />
                    </div>
                  </div>
                  <StatusBadge status={p.status} variant={p.variant} />
                </div>
              ))}
            </div>
          </div>
          <div className="card p-5 sm:p-6">
            <h3 className="mb-3 text-base font-semibold text-slate-900 dark:text-dark-text">Today's Tasks</h3>
            <div className="space-y-3">
              {tasks.map((t, i) => (
                <label key={i} className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    defaultChecked={t.done}
                    className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span className={`text-sm ${t.done ? 'text-slate-400 line-through dark:text-dark-muted' : 'text-slate-700 dark:text-dark-text'}`}>
                    {t.text}
                  </span>
                  <span className="ml-auto text-xs text-slate-400 dark:text-dark-muted">{t.time}</span>
                </label>
              ))}
            </div>

            <h3 className="mb-3 mt-6 text-base font-semibold text-slate-900 dark:text-dark-text">Recent Activity</h3>
            <div className="space-y-4">
              {activities.map((a, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${a.color}`}>
                    <a.icon size={14} className="text-white" />
                  </span>
                  <div>
                    <p className="text-sm text-slate-700 dark:text-dark-text">{a.text}</p>
                    <p className="text-xs text-slate-400 dark:text-dark-muted">{a.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}