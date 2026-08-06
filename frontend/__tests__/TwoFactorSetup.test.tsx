import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import TwoFactorSetupPage from '../app/(protected)/two-factor-setup/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}))

jest.mock('../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../lib/api', () => ({
  setup2FA: jest.fn(),
  verify2FA: jest.fn(),
  get2FAStatus: jest.fn(),
  getBackupCodesRemaining: jest.fn(),
  regenerateBackupCodes: jest.fn(),
  disable2FA: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockSetup2FA = require('../lib/api').setup2FA as jest.MockedFunction<any>
const mockVerify2FA = require('../lib/api').verify2FA as jest.MockedFunction<any>
const mockGet2FAStatus = require('../lib/api').get2FAStatus as jest.MockedFunction<any>
const mockGetBackupCodesRemaining = require('../lib/api').getBackupCodesRemaining as jest.MockedFunction<any>
const mockRegenerateBackupCodes = require('../lib/api').regenerateBackupCodes as jest.MockedFunction<any>
const mockDisable2FA = require('../lib/api').disable2FA as jest.MockedFunction<any>

describe('TwoFactorSetupPage', () => {
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
    mockGet2FAStatus.mockResolvedValue({ is_2fa_enabled: false })
  })

  it('renders two-factor setup page when authenticated', async () => {
    render(<TwoFactorSetupPage />)
    expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument()
  })

  it('shows intro step initially', () => {
    render(<TwoFactorSetupPage />)
    expect(screen.getByText('Add an extra layer of security to your account')).toBeInTheDocument()
    expect(screen.getByText('Get Started')).toBeInTheDocument()
  })

  it('navigates to scan step when Get Started is clicked', async () => {
    mockSetup2FA.mockResolvedValue({
      secret: 'JBSWY3DPEHPK3PXP',
      qr_code_url: 'https://example.com/qr',
      backup_codes: ['code1', 'code2', 'code3'],
    })
    render(<TwoFactorSetupPage />)
    const getStartedButton = screen.getByText('Get Started')
    getStartedButton.click()
    await waitFor(() => {
      expect(screen.getByText('Scan QR Code')).toBeInTheDocument()
    })
  })

  it('displays loading state during setup', async () => {
    mockSetup2FA.mockImplementation(() => new Promise(() => {}))
    render(<TwoFactorSetupPage />)
    const getStartedButton = screen.getByText('Get Started')
    getStartedButton.click()
    expect(screen.getByText('Initializing...')).toBeInTheDocument()
  })

  it('displays error when setup fails', async () => {
    mockSetup2FA.mockRejectedValue(new Error('Setup failed'))
    render(<TwoFactorSetupPage />)
    const getStartedButton = screen.getByText('Get Started')
    getStartedButton.click()
    await waitFor(() => {
      expect(screen.getByText('Failed to initialize 2FA setup')).toBeInTheDocument()
    })
  })

  it('shows already enabled state when 2FA is active', async () => {
    mockGet2FAStatus.mockResolvedValue({ is_2fa_enabled: true })
    mockGetBackupCodesRemaining.mockResolvedValue({ remaining: 3 })
    render(<TwoFactorSetupPage />)
    await waitFor(() => {
      expect(screen.getByText('Two-factor authentication is currently enabled')).toBeInTheDocument()
    })
  })

  it('redirects to login when not authenticated', () => {
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
    render(<TwoFactorSetupPage />)
    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})
