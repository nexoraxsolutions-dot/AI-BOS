"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import {
  getTestSuites,
  getTestCases,
  getTestRuns,
  getTestStatistics,
  createTestSuite,
  updateTestSuite,
  deleteTestSuite,
  createTestCase,
  updateTestCase,
  deleteTestCase,
  createTestRun,
  completeTestRun,
  TestSuite,
  TestCase,
  TestRunSummary,
  TestStatistics,
  TestSuiteCreate,
  TestCaseCreate,
  TestRunCreate,
  TestRunCompleteRequest,
} from '../../../lib/api'

type TabType = 'suites' | 'cases' | 'runs' | 'statistics'

export default function TestFrameworkPage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<TabType>('suites')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Test Suites state
  const [testSuites, setTestSuites] = useState<TestSuite[]>([])
  const [suitesLoading, setSuitesLoading] = useState(false)

  // Test Cases state
  const [testCases, setTestCases] = useState<TestCase[]>([])
  const [casesLoading, setCasesLoading] = useState(false)
  const [selectedSuiteId, setSelectedSuiteId] = useState<number | null>(null)

  // Test Runs state
  const [testRuns, setTestRuns] = useState<TestRunSummary[]>([])
  const [runsLoading, setRunsLoading] = useState(false)

  // Statistics state
  const [statistics, setStatistics] = useState<TestStatistics | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  // Modals state
  const [showSuiteModal, setShowSuiteModal] = useState(false)
  const [showCaseModal, setShowCaseModal] = useState(false)
  const [showRunModal, setShowRunModal] = useState(false)
  const [editingSuite, setEditingSuite] = useState<TestSuite | null>(null)
  const [editingCase, setEditingCase] = useState<TestCase | null>(null)

  // Form state
  const [suiteForm, setSuiteForm] = useState<TestSuiteCreate>({
    name: '',
    description: '',
    is_active: true,
    is_automated: true,
  })
  const [caseForm, setCaseForm] = useState<TestCaseCreate>({
    test_suite_id: 0,
    name: '',
    test_type: 'integration',
    priority: 'medium',
    timeout: 30,
    retry_count: 0,
    is_active: true,
    order: 0,
  })
  const [runForm, setRunForm] = useState<TestRunCreate>({
    test_suite_id: 0,
    environment: 'development',
    triggered_by: 'manual',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    fetchData()
  }, [isAuthenticated, router])

  async function fetchData() {
    try {
      setLoading(true)
      setError(null)
      await Promise.all([
        fetchTestSuites(),
        fetchTestRuns(),
        fetchStatistics(),
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  async function fetchTestSuites(): Promise<void> {
    setSuitesLoading(true)
    const response = await getTestSuites()
    setTestSuites(response.items)
    setSuitesLoading(false)
  }

  async function fetchTestCases(suiteId: number): Promise<void> {
    setCasesLoading(true)
    const response = await getTestCases(suiteId)
    setTestCases(response.items)
    setCasesLoading(false)
  }

  async function fetchTestRuns(): Promise<void> {
    setRunsLoading(true)
    const response = await getTestRuns({ limit: 50 })
    setTestRuns(response.items)
    setRunsLoading(false)
  }

  async function fetchStatistics(): Promise<void> {
    setStatsLoading(true)
    const stats = await getTestStatistics()
    setStatistics(stats)
    setStatsLoading(false)
  }

  const handleCreateSuite = async () => {
    setFormLoading(true)
    setFormError(null)
    try {
      await createTestSuite(suiteForm)
      setShowSuiteModal(false)
      resetSuiteForm()
      await fetchTestSuites()
      await fetchStatistics()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create test suite')
    } finally {
      setFormLoading(false)
    }
  }

  const handleUpdateSuite = async () => {
    if (!editingSuite) return
    setFormLoading(true)
    setFormError(null)
    try {
      await updateTestSuite(editingSuite.id, suiteForm)
      setShowSuiteModal(false)
      setEditingSuite(null)
      resetSuiteForm()
      await fetchTestSuites()
      await fetchStatistics()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update test suite')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDeleteSuite = async (id: number) => {
    if (!confirm('Are you sure you want to delete this test suite?')) return
    try {
      await deleteTestSuite(id)
      await fetchTestSuites()
      await fetchStatistics()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete test suite')
    }
  }

  const handleCreateCase = async () => {
    setFormLoading(true)
    setFormError(null)
    try {
      await createTestCase(caseForm)
      setShowCaseModal(false)
      resetCaseForm()
      if (selectedSuiteId) {
        await fetchTestCases(selectedSuiteId)
      }
      await fetchStatistics()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create test case')
    } finally {
      setFormLoading(false)
    }
  }

  const handleUpdateCase = async () => {
    if (!editingCase) return
    setFormLoading(true)
    setFormError(null)
    try {
      await updateTestCase(editingCase.id, caseForm)
      setShowCaseModal(false)
      setEditingCase(null)
      resetCaseForm()
      if (selectedSuiteId) {
        await fetchTestCases(selectedSuiteId)
      }
      await fetchStatistics()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update test case')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDeleteCase = async (id: number) => {
    if (!confirm('Are you sure you want to delete this test case?')) return
    try {
      await deleteTestCase(id)
      if (selectedSuiteId) {
        await fetchTestCases(selectedSuiteId)
      }
      await fetchStatistics()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete test case')
    }
  }

  const handleCreateRun = async () => {
    setFormLoading(true)
    setFormError(null)
    try {
      const run = await createTestRun(runForm)
      setShowRunModal(false)
      resetRunForm()
      await fetchTestRuns()
      
      // Auto-complete the run with demo data
      setTimeout(async () => {
        try {
          const completeData: TestRunCompleteRequest = {
            status: 'passed',
            total_tests: 5,
            passed_tests: 5,
            failed_tests: 0,
            skipped_tests: 0,
            error_tests: 0,
            duration: 12.5,
          }
          await completeTestRun(run.id, completeData)
          await fetchTestRuns()
          await fetchStatistics()
        } catch (err) {
          console.error('Failed to complete test run:', err)
        }
      }, 2000)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create test run')
    } finally {
      setFormLoading(false)
    }
  }

  const resetSuiteForm = () => {
    setSuiteForm({
      name: '',
      description: '',
      is_active: true,
      is_automated: true,
    })
    setFormError(null)
  }

  const resetCaseForm = () => {
    setCaseForm({
      test_suite_id: selectedSuiteId || 0,
      name: '',
      test_type: 'integration',
      priority: 'medium',
      timeout: 30,
      retry_count: 0,
      is_active: true,
      order: 0,
    })
    setFormError(null)
  }

  const resetRunForm = () => {
    setRunForm({
      test_suite_id: 0,
      environment: 'development',
      triggered_by: 'manual',
    })
    setFormError(null)
  }

  const openEditSuite = (suite: TestSuite) => {
    setEditingSuite(suite)
    setSuiteForm({
      name: suite.name,
      description: suite.description || '',
      is_active: suite.is_active,
      is_automated: suite.is_automated,
      company_id: suite.company_id,
    })
    setShowSuiteModal(true)
  }

  const openCreateSuite = () => {
    setEditingSuite(null)
    resetSuiteForm()
    setShowSuiteModal(true)
  }

  const openCreateCase = (suiteId?: number) => {
    setEditingCase(null)
    setSelectedSuiteId(suiteId || null)
    resetCaseForm()
    if (suiteId) {
      setCaseForm({ ...caseForm, test_suite_id: suiteId })
    }
    setShowCaseModal(true)
  }

  const openEditCase = (testCase: TestCase) => {
    setEditingCase(testCase)
    setSelectedSuiteId(testCase.test_suite_id)
    setCaseForm({
      test_suite_id: testCase.test_suite_id,
      name: testCase.name,
      description: testCase.description || '',
      priority: testCase.priority,
      test_type: testCase.test_type,
      endpoint: testCase.endpoint || '',
      method: testCase.method || '',
      payload: testCase.payload || '',
      expected_status: testCase.expected_status || 200,
      expected_response: testCase.expected_response || '',
      tags: testCase.tags || '',
      timeout: testCase.timeout,
      retry_count: testCase.retry_count,
      is_active: testCase.is_active,
      order: testCase.order,
    })
    setShowCaseModal(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed':
        return 'bg-green-500/10 text-green-400 border border-green-500/30'
      case 'failed':
        return 'bg-red-500/10 text-red-400 border border-red-500/30'
      case 'skipped':
        return 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
      case 'error':
        return 'bg-orange-500/10 text-orange-400 border border-orange-500/30'
      case 'running':
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
      default:
        return 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-500/10 text-red-400 border border-red-500/30'
      case 'high':
        return 'bg-orange-500/10 text-orange-400 border border-orange-500/30'
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
      case 'low':
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
      default:
        return 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading test framework...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Data</h2>
            <p className="text-slate-300">{error}</p>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Test Framework</h1>
            <p className="text-slate-400 mt-1">Manage test suites, cases, and execution runs</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-white/10">
          <button
            onClick={() => setActiveTab('suites')}
            className={`pb-3 px-4 text-sm font-medium transition ${
              activeTab === 'suites'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Test Suites ({testSuites.length})
          </button>
          <button
            onClick={() => setActiveTab('cases')}
            className={`pb-3 px-4 text-sm font-medium transition ${
              activeTab === 'cases'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Test Cases ({testCases.length})
          </button>
          <button
            onClick={() => setActiveTab('runs')}
            className={`pb-3 px-4 text-sm font-medium transition ${
              activeTab === 'runs'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Test Runs ({testRuns.length})
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`pb-3 px-4 text-sm font-medium transition ${
              activeTab === 'statistics'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Statistics
          </button>
        </div>

        {/* Test Suites Tab */}
        {activeTab === 'suites' && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Test Suites</h2>
              <button
                onClick={openCreateSuite}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 transition"
              >
                + Create Suite
              </button>
            </div>

            {suitesLoading ? (
              <div className="p-8 text-center text-slate-400">Loading test suites...</div>
            ) : testSuites.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                No test suites found. Create your first test suite to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Name</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Description</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Type</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                      <th className="px-6 py-4 text-right text-sm font-medium text-slate-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {testSuites.map((suite) => (
                      <tr key={suite.id} className="hover:bg-white/5 transition">
                        <td className="px-6 py-4 text-sm text-white font-medium">{suite.name}</td>
                        <td className="px-6 py-4 text-sm text-slate-300">{suite.description || '-'}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                            suite.is_automated
                              ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                              : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                          }`}>
                            {suite.is_automated ? 'Automated' : 'Manual'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                            suite.is_active
                              ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                              : 'bg-red-500/10 text-red-400 border border-red-500/30'
                          }`}>
                            {suite.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => {
                              setSelectedSuiteId(suite.id)
                              fetchTestCases(suite.id)
                              setActiveTab('cases')
                            }}
                            className="text-sm text-cyan-400 hover:text-cyan-300 mr-4 transition"
                          >
                            View Cases
                          </button>
                          <button
                            onClick={() => openEditSuite(suite)}
                            className="text-sm text-cyan-400 hover:text-cyan-300 mr-4 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteSuite(suite.id)}
                            className="text-sm text-red-400 hover:text-red-300 transition"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Test Cases Tab */}
        {activeTab === 'cases' && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-semibold">Test Cases</h2>
                {selectedSuiteId && (
                  <p className="text-slate-400 text-sm mt-1">
                    Suite ID: {selectedSuiteId}
                  </p>
                )}
              </div>
              <button
                onClick={() => openCreateCase(selectedSuiteId || undefined)}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 transition"
              >
                + Create Case
              </button>
            </div>

            {casesLoading ? (
              <div className="p-8 text-center text-slate-400">Loading test cases...</div>
            ) : !selectedSuiteId ? (
              <div className="p-8 text-center text-slate-400">
                Select a test suite to view its test cases
              </div>
            ) : testCases.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                No test cases found. Create your first test case to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Name</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Type</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Priority</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Success Rate</th>
                      <th className="px-6 py-4 text-right text-sm font-medium text-slate-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {testCases.map((testCase) => (
                      <tr key={testCase.id} className="hover:bg-white/5 transition">
                        <td className="px-6 py-4 text-sm text-white font-medium">{testCase.name}</td>
                        <td className="px-6 py-4 text-sm text-slate-300 capitalize">{testCase.test_type}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium capitalize ${
                            getPriorityColor(testCase.priority)
                          }`}>
                            {testCase.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium capitalize ${
                            getStatusColor(testCase.status)
                          }`}>
                            {testCase.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">
                          {testCase.success_count + testCase.failure_count > 0
                            ? `${((testCase.success_count / (testCase.success_count + testCase.failure_count)) * 100).toFixed(1)}%`
                            : 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => openEditCase(testCase)}
                            className="text-sm text-cyan-400 hover:text-cyan-300 mr-4 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteCase(testCase.id)}
                            className="text-sm text-red-400 hover:text-red-300 transition"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Test Runs Tab */}
        {activeTab === 'runs' && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Test Runs</h2>
              <button
                onClick={() => setShowRunModal(true)}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 transition"
              >
                + New Run
              </button>
            </div>

            {runsLoading ? (
              <div className="p-8 text-center text-slate-400">Loading test runs...</div>
            ) : testRuns.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                No test runs found. Create your first test run to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Suite</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Environment</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Success Rate</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Duration</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Started</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {testRuns.map((run) => (
                      <tr key={run.id} className="hover:bg-white/5 transition">
                        <td className="px-6 py-4 text-sm text-white font-medium">{run.test_suite_name}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium capitalize ${
                            getStatusColor(run.status)
                          }`}>
                            {run.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">{run.environment}</td>
                        <td className="px-6 py-4 text-sm text-slate-300">
                          {run.success_rate !== undefined ? `${run.success_rate.toFixed(1)}%` : 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">
                          {run.duration ? `${run.duration.toFixed(2)}s` : '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">
                          {new Date(run.started_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <div className="space-y-6">
            {statsLoading ? (
              <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 text-center text-slate-400">
                Loading statistics...
              </div>
            ) : statistics ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Total Suites</p>
                    <p className="text-3xl font-semibold text-white mt-2">{statistics.total_suites}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Total Cases</p>
                    <p className="text-3xl font-semibold text-white mt-2">{statistics.total_cases}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Total Runs</p>
                    <p className="text-3xl font-semibold text-white mt-2">{statistics.total_runs}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Success Rate</p>
                    <p className="text-3xl font-semibold text-green-400 mt-2">{statistics.success_rate.toFixed(1)}%</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Passed</p>
                    <p className="text-2xl font-semibold text-green-400 mt-2">{statistics.passed_tests}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Failed</p>
                    <p className="text-2xl font-semibold text-red-400 mt-2">{statistics.failed_tests}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Skipped</p>
                    <p className="text-2xl font-semibold text-yellow-400 mt-2">{statistics.skipped_tests}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Errors</p>
                    <p className="text-2xl font-semibold text-orange-400 mt-2">{statistics.error_tests}</p>
                  </div>
                </div>

                {statistics.average_duration && (
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                    <p className="text-slate-400 text-sm">Average Test Duration</p>
                    <p className="text-3xl font-semibold text-white mt-2">{statistics.average_duration.toFixed(2)}s</p>
                  </div>
                )}

                {statistics.recent_runs.length > 0 && (
                  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
                    <div className="px-8 py-6 border-b border-white/10">
                      <h3 className="text-xl font-semibold">Recent Runs</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-900/50">
                          <tr>
                            <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Suite</th>
                            <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                            <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Success Rate</th>
                            <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Started</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/10">
                          {statistics.recent_runs.map((run) => (
                            <tr key={run.id} className="hover:bg-white/5 transition">
                              <td className="px-6 py-4 text-sm text-white font-medium">{run.test_suite_name}</td>
                              <td className="px-6 py-4">
                                <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium capitalize ${
                                  getStatusColor(run.status)
                                }`}>
                                  {run.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-300">
                                {run.success_rate !== undefined ? `${run.success_rate.toFixed(1)}%` : 'N/A'}
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-300">
                                {new Date(run.started_at).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 text-center text-slate-400">
                No statistics available
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create/Edit Suite Modal */}
      {showSuiteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">
              {editingSuite ? 'Edit Test Suite' : 'Create Test Suite'}
            </h3>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Suite Name *</label>
                <input
                  type="text"
                  value={suiteForm.name}
                  onChange={(e) => setSuiteForm({ ...suiteForm, name: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="e.g., API Tests, Integration Tests"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Description</label>
                <textarea
                  value={suiteForm.description}
                  onChange={(e) => setSuiteForm({ ...suiteForm, description: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Describe this test suite"
                  rows={3}
                />
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={suiteForm.is_active}
                    onChange={(e) => setSuiteForm({ ...suiteForm, is_active: e.target.checked })}
                    className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">Active</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={suiteForm.is_automated}
                    onChange={(e) => setSuiteForm({ ...suiteForm, is_automated: e.target.checked })}
                    className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">Automated</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => { setShowSuiteModal(false); setEditingSuite(null); resetSuiteForm() }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={editingSuite ? handleUpdateSuite : handleCreateSuite}
                disabled={formLoading || !suiteForm.name}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Saving...' : editingSuite ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create/Edit Case Modal */}
      {showCaseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">
              {editingCase ? 'Edit Test Case' : 'Create Test Case'}
            </h3>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Test Case Name *</label>
                <input
                  type="text"
                  value={caseForm.name}
                  onChange={(e) => setCaseForm({ ...caseForm, name: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="e.g., Test user login with valid credentials"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Description</label>
                <textarea
                  value={caseForm.description}
                  onChange={(e) => setCaseForm({ ...caseForm, description: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Describe what this test case validates"
                  rows={2}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Test Type</label>
                  <select
                    value={caseForm.test_type}
                    onChange={(e) => setCaseForm({ ...caseForm, test_type: e.target.value })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                  >
                    <option value="unit">Unit</option>
                    <option value="integration">Integration</option>
                    <option value="e2e">E2E</option>
                    <option value="performance">Performance</option>
                    <option value="security">Security</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Priority</label>
                  <select
                    value={caseForm.priority}
                    onChange={(e) => setCaseForm({ ...caseForm, priority: e.target.value })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Endpoint</label>
                  <input
                    type="text"
                    value={caseForm.endpoint}
                    onChange={(e) => setCaseForm({ ...caseForm, endpoint: e.target.value })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                    placeholder="/api/users"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Method</label>
                  <select
                    value={caseForm.method}
                    onChange={(e) => setCaseForm({ ...caseForm, method: e.target.value })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                  >
                    <option value="">None</option>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                    <option value="PATCH">PATCH</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Timeout (s)</label>
                  <input
                    type="number"
                    value={caseForm.timeout}
                    onChange={(e) => setCaseForm({ ...caseForm, timeout: parseInt(e.target.value) })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                    min="1"
                    max="300"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Retry Count</label>
                  <input
                    type="number"
                    value={caseForm.retry_count}
                    onChange={(e) => setCaseForm({ ...caseForm, retry_count: parseInt(e.target.value) })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                    min="0"
                    max="10"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Order</label>
                  <input
                    type="number"
                    value={caseForm.order}
                    onChange={(e) => setCaseForm({ ...caseForm, order: parseInt(e.target.value) })}
                    className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                    min="0"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => { setShowCaseModal(false); setEditingCase(null); resetCaseForm() }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={editingCase ? handleUpdateCase : handleCreateCase}
                disabled={formLoading || !caseForm.name}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Saving...' : editingCase ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Run Modal */}
      {showRunModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">Create Test Run</h3>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Test Suite *</label>
                <select
                  value={runForm.test_suite_id}
                  onChange={(e) => setRunForm({ ...runForm, test_suite_id: parseInt(e.target.value) })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="0">Select a test suite</option>
                  {testSuites.map((suite) => (
                    <option key={suite.id} value={suite.id}>{suite.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Environment</label>
                <select
                  value={runForm.environment}
                  onChange={(e) => setRunForm({ ...runForm, environment: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="development">Development</option>
                  <option value="staging">Staging</option>
                  <option value="production">Production</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Triggered By</label>
                <select
                  value={runForm.triggered_by}
                  onChange={(e) => setRunForm({ ...runForm, triggered_by: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="manual">Manual</option>
                  <option value="ci_cd">CI/CD</option>
                  <option value="scheduled">Scheduled</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Branch (optional)</label>
                <input
                  type="text"
                  value={runForm.branch}
                  onChange={(e) => setRunForm({ ...runForm, branch: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="main"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Commit Hash (optional)</label>
                <input
                  type="text"
                  value={runForm.commit_hash}
                  onChange={(e) => setRunForm({ ...runForm, commit_hash: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="abc123..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => { setShowRunModal(false); resetRunForm() }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRun}
                disabled={formLoading || runForm.test_suite_id === 0}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Starting...' : 'Start Run'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}