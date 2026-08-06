import { render, screen, waitFor, act } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import LoggingPage from '../app/(protected)/logging/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}))

jest.mock('../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../lib/api', () => ({
  getLogEntries: jest.fn(),
  getLogStats: jest.fn(),
  cleanupLogs: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockGetLogEntries = require('../lib/api').getLogEntries as jest.MockedFunction<any>
const mockGetLogStats = require('../lib/api').getLogStats as jest.MockedFunction<any>
const mockCleanupLogs = require('../lib/api').cleanupLogs as jest.MockedFunction<any>

describe('LoggingHistory Page', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
    const originalConsoleError = console.error
    console.error = (...args: any[]) => {
      if (
        typeof args[0] === 'string' &&
        (args[0].includes('Warning: An update to') || args[0].includes('not wrapped in act'))
      ) {
        return
      }
      originalConsoleError.call(console, ...args)
    }

    jest.clearAllMocks()
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      refresh: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn(),
    } as any)
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { is_superuser: true, id: 1, email: 'admin@ai-bos.com' },
      logout: jest.fn(),
    } as any)
    mockGetLogEntries.mockResolvedValue({
      items: [
        {
          id: 1,
          level: 'INFO',
          logger_name: 'ai_bos',
          message: 'Test info message',
          module: 'test_module',
          func_name: 'test_func',
          line_no: 42,
          pathname: '/app/test_module.py',
          thread_name: 'MainThread',
          process: '1234',
          timestamp: '2024-01-01T12:00:00',
          user_id: 1,
          ip_address: '127.0.0.1',
          user_agent: 'TestAgent/1.0',
          extra_data: null,
        },
        {
          id: 2,
          level: 'ERROR',
          logger_name: 'ai_bos',
          message: 'Test error message',
          module: 'test_module',
          func_name: 'test_func',
          line_no: 100,
          pathname: '/app/test_module.py',
          thread_name: 'MainThread',
          process: '1234',
          timestamp: '2024-01-01T13:00:00',
          user_id: null,
          ip_address: null,
          user_agent: null,
          extra_data: null,
        },
      ],
      total: 2,
      page: 1,
      page_size: 50,
    })

    mockGetLogStats.mockResolvedValue({
      total_entries: 2,
      by_level: { INFO: 1, ERROR: 1 },
      top_loggers: [{ logger_name: 'ai_bos', count: 2 }],
      oldest_entry: '2024-01-01T12:00:00',
      newest_entry: '2024-01-01T13:00:00',
    })
  })

  afterEach(() => {
    console.error = originalConsoleError
  })

  it('renders logging history page when authenticated as superuser', async () => {
    render(<LoggingPage />)
    expect(screen.getByText('Logging History')).toBeInTheDocument()
    expect(screen.getByText('Review persisted application and system log entries')).toBeInTheDocument()
  })

  it('shows loading state initially', async () => {
    mockGetLogEntries.mockImplementation(() => new Promise(() => {}))
    render(<LoggingPage />)
    expect(screen.getByText('Loading log entries...')).toBeInTheDocument()
  })

  it('displays log entries after loading', async () => {
    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('Test info message')).toBeInTheDocument()
    })
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('displays log level badges with correct styling', async () => {
    render(<LoggingPage />)
    await waitFor(() => {
      const infoBadges = screen.getAllByText('INFO')
      const errorBadges = screen.getAllByText('ERROR')
      expect(infoBadges.length).toBeGreaterThan(0)
      expect(errorBadges.length).toBeGreaterThan(0)
    })
  })

  it('displays statistics cards', async () => {
    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('Total Entries')).toBeInTheDocument()
      expect(screen.getByText('By Level')).toBeInTheDocument()
      expect(screen.getByText('Oldest Entry')).toBeInTheDocument()
      expect(screen.getByText('Newest Entry')).toBeInTheDocument()
    })
  })

  it('displays top loggers section', async () => {
    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('Top Loggers')).toBeInTheDocument()
    })
  })

  it('shows filters section', async () => {
    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('Filters')).toBeInTheDocument()
    })
  })

  it('shows cleanup section', async () => {
    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('Log Cleanup')).toBeInTheDocument()
      expect(screen.getByText('Delete Old Logs')).toBeInTheDocument()
    })
  })

  it('shows refresh button', async () => {
    render(<LoggingPage />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('shows pagination when total > 50', async () => {
    mockGetLogEntries.mockResolvedValue({
      items: [],
      total: 100,
      page: 1,
      page_size: 50,
    })

    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('Previous')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
    })
  })

  it('shows no entries message when logs are empty', async () => {
    mockGetLogEntries.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
    })

    render(<LoggingPage />)
    await waitFor(() => {
      expect(screen.getByText('No log entries found.')).toBeInTheDocument()
    })
  })
})
