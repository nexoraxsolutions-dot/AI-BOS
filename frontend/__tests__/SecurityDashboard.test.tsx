import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import SecurityDashboardPage from '../app/(protected)/security/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}))

jest.mock('../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../lib/api', () => ({
  getSecurityDashboardSummary: jest.fn(),
  getSecurityScore: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockGetSecurityDashboardSummary = require('../lib/api').getSecurityDashboardSummary as jest.MockedFunction<any>
const mockGetSecurityScore = require('../lib/api').getSecurityScore as jest.MockedFunction<any>

const mockDashboardData = {
  security_score: 85,
  total_users: 100,
  users_with_2fa: 60,
  locked_accounts: 2,
  users_with_failed_logins: 10,
  active_sessions: 45,
  failed_logins_24h: 5,
  failed_logins_7d: 25,
  account_lockouts_30d: 3,
  password_changes_30d: 8,
  two_fa_enabled_30d: 5,
  suspicious_ips_count: 1,
  recent_events: [
    {
      id: 1,
      action: 'login_failed',
      user_id: 1,
      ip_address: '192.168.1.1',
      created_at: '2024-01-01T12:00:00',
      details: {},
    },
  ],
}

const mockScoreData = {
  security_score: 85,
  recommendations: ['Enable 2FA for all users', 'Review suspicious IPs'],
}

describe('SecurityDashboardPage', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
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
      token: 'test-token',
      user: { is_superuser: true, id: 1, email: 'admin@ai-bos.com' },
      logout: jest.fn(),
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })
    mockGetSecurityDashboardSummary.mockResolvedValue(mockDashboardData)
    mockGetSecurityScore.mockResolvedValue(mockScoreData)
  })

  it('renders loading state initially', () => {
    mockGetSecurityDashboardSummary.mockImplementation(() => new Promise(() => {}))
    render(<SecurityDashboardPage />)
    expect(screen.getByText('Loading security dashboard...')).toBeInTheDocument()
  })

  it('renders security dashboard when authenticated', async () => {
    render(<SecurityDashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument()
    })
    expect(screen.getByText('Monitor and manage your security posture')).toBeInTheDocument()
  })

  it('displays security score card', async () => {
    render(<SecurityDashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument()
    })
  })

  it('displays recommendations', async () => {
    render(<SecurityDashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Enable 2FA for all users')).toBeInTheDocument()
      expect(screen.getByText('Review suspicious IPs')).toBeInTheDocument()
    })
  })

  it('displays metrics grid with data', async () => {
    render(<SecurityDashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Total Users')).toBeInTheDocument()
      expect(screen.getByText('Locked Accounts')).toBeInTheDocument()
    })
  })

  it('redirects to home when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      token: null,
      user: null,
      logout: jest.fn(),
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })
    render(<SecurityDashboardPage />)
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('displays error state when data fetch fails', async () => {
    mockGetSecurityDashboardSummary.mockRejectedValue(new Error('API Error'))
    render(<SecurityDashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Error Loading Security Dashboard')).toBeInTheDocument()
    })
  })
})
