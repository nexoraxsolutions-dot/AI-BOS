import { render, screen, waitFor, act } from '@testing-library/react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import TestFrameworkPage from '../app/(protected)/test-framework/page'

// Mock the modules
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}))

jest.mock('../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../lib/api', () => ({
  getTestSuites: jest.fn(),
  getTestCases: jest.fn(),
  getTestRuns: jest.fn(),
  getTestStatistics: jest.fn(),
  createTestSuite: jest.fn(),
  updateTestSuite: jest.fn(),
  deleteTestSuite: jest.fn(),
  createTestCase: jest.fn(),
  updateTestCase: jest.fn(),
  deleteTestCase: jest.fn(),
  createTestRun: jest.fn(),
  completeTestRun: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockUsePathname = usePathname as jest.MockedFunction<typeof usePathname>
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockGetTestSuites = require('../lib/api').getTestSuites as jest.MockedFunction<any>
const mockGetTestCases = require('../lib/api').getTestCases as jest.MockedFunction<any>
const mockGetTestRuns = require('../lib/api').getTestRuns as jest.MockedFunction<any>
const mockGetTestStatistics = require('../lib/api').getTestStatistics as jest.MockedFunction<any>

describe('TestFrameworkPage', () => {
  const mockPush = jest.fn()
  const mockRefresh = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      refresh: mockRefresh,
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn(),
    } as any)
    mockUsePathname.mockReturnValue('/test-framework')
    mockUseAuth.mockReturnValue({
      token: 'mock-token',
      isAuthenticated: true,
      user: {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        username: 'testuser',
        is_active: true,
        is_superuser: true,
      },
      loading: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })
  })

  it('renders loading state initially', () => {
    mockGetTestSuites.mockImplementation(() => new Promise(() => {}))
    mockGetTestRuns.mockImplementation(() => new Promise(() => {}))
    mockGetTestStatistics.mockImplementation(() => new Promise(() => {}))

    render(<TestFrameworkPage />)
    expect(screen.getByText('Loading test framework...')).toBeInTheDocument()
  })

  it('renders error state when data fetch fails', async () => {
    mockGetTestSuites.mockRejectedValue(new Error('API Error'))
    mockGetTestRuns.mockRejectedValue(new Error('API Error'))
    mockGetTestStatistics.mockRejectedValue(new Error('API Error'))

    render(<TestFrameworkPage />)

    await waitFor(() => {
      expect(screen.getByText('Error Loading Data')).toBeInTheDocument()
    })
  })

  it('renders test framework page with tabs', async () => {
    mockGetTestSuites.mockResolvedValue({
      items: [
        {
          id: 1,
          name: 'API Tests',
          description: 'API integration tests',
          is_active: true,
          is_automated: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    mockGetTestRuns.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })
    mockGetTestStatistics.mockResolvedValue({
      total_suites: 1,
      total_cases: 0,
      total_runs: 0,
      total_results: 0,
      passed_tests: 0,
      failed_tests: 0,
      skipped_tests: 0,
      error_tests: 0,
      success_rate: 0,
      average_duration: 0,
      most_failed_tests: [],
      recent_runs: [],
    })

    render(<TestFrameworkPage />)

    await waitFor(() => {
      expect(screen.getByText('Test Framework')).toBeInTheDocument()
      expect(screen.getByText('Test Suites (1)')).toBeInTheDocument()
      expect(screen.getByText('Test Cases (0)')).toBeInTheDocument()
      expect(screen.getByText('Test Runs (0)')).toBeInTheDocument()
      expect(screen.getByText('Statistics')).toBeInTheDocument()
    })
  })

  it('displays test suites in table', async () => {
    const mockSuites = [
      {
        id: 1,
        name: 'API Tests',
        description: 'API integration tests',
        is_active: true,
        is_automated: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: 'Unit Tests',
        description: 'Unit test suite',
        is_active: true,
        is_automated: true,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    mockGetTestSuites.mockResolvedValue({
      items: mockSuites,
      total: 2,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    mockGetTestRuns.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })
    mockGetTestStatistics.mockResolvedValue({
      total_suites: 2,
      total_cases: 0,
      total_runs: 0,
      total_results: 0,
      passed_tests: 0,
      failed_tests: 0,
      skipped_tests: 0,
      error_tests: 0,
      success_rate: 0,
      average_duration: 0,
      most_failed_tests: [],
      recent_runs: [],
    })

    render(<TestFrameworkPage />)

    await waitFor(() => {
      expect(screen.getByText('API Tests')).toBeInTheDocument()
      expect(screen.getByText('Unit Tests')).toBeInTheDocument()
      expect(screen.getByText('API integration tests')).toBeInTheDocument()
      expect(screen.getByText('Unit test suite')).toBeInTheDocument()
    })
  })

  it('shows create suite button', async () => {
    mockGetTestSuites.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    mockGetTestRuns.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })
    mockGetTestStatistics.mockResolvedValue({
      total_suites: 0,
      total_cases: 0,
      total_runs: 0,
      total_results: 0,
      passed_tests: 0,
      failed_tests: 0,
      skipped_tests: 0,
      error_tests: 0,
      success_rate: 0,
      average_duration: 0,
      most_failed_tests: [],
      recent_runs: [],
    })

    render(<TestFrameworkPage />)

    await waitFor(() => {
      expect(screen.getByText('+ Create Suite')).toBeInTheDocument()
    })
  })

  it('opens create suite modal when button is clicked', async () => {
    mockGetTestSuites.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    mockGetTestRuns.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })
    mockGetTestStatistics.mockResolvedValue({
      total_suites: 0,
      total_cases: 0,
      total_runs: 0,
      total_results: 0,
      passed_tests: 0,
      failed_tests: 0,
      skipped_tests: 0,
      error_tests: 0,
      success_rate: 0,
      average_duration: 0,
      most_failed_tests: [],
      recent_runs: [],
    })

    render(<TestFrameworkPage />)

    await waitFor(() => {
      expect(screen.getByText('+ Create Suite')).toBeInTheDocument()
    })

    act(() => {
      screen.getByText('+ Create Suite').click()
    })

    await waitFor(() => {
      expect(screen.getByText('Create Test Suite')).toBeInTheDocument()
    })
  })

  it('displays statistics when available', async () => {
    mockGetTestSuites.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    mockGetTestRuns.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })
    mockGetTestStatistics.mockResolvedValue({
      total_suites: 5,
      total_cases: 25,
      total_runs: 10,
      total_results: 50,
      passed_tests: 45,
      failed_tests: 3,
      skipped_tests: 2,
      error_tests: 0,
      success_rate: 90.0,
      average_duration: 12.5,
      most_failed_tests: [],
      recent_runs: [],
    })

    render(<TestFrameworkPage />)

    // Click on Statistics tab
    await waitFor(() => {
      expect(screen.getByText('Statistics')).toBeInTheDocument()
    })
    
    act(() => {
      screen.getByText('Statistics').click()
    })

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument() // Total Suites
      expect(screen.getByText('25')).toBeInTheDocument() // Total Cases
      expect(screen.getByText('10')).toBeInTheDocument() // Total Runs
      expect(screen.getByText('90.0%')).toBeInTheDocument() // Success Rate
    })
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      token: null,
      isAuthenticated: false,
      user: null,
      loading: false,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })

    render(<TestFrameworkPage />)

    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})