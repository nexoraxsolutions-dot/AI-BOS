import { render, screen, waitFor, act } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import LoggingConfigurationPage from '../app/(protected)/logging-configuration/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}))

jest.mock('../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../lib/api', () => ({
  getLoggingConfiguration: jest.fn(),
  updateLoggingConfiguration: jest.fn(),
  createLoggingConfiguration: jest.fn(),
  deleteLoggingConfiguration: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockGetLoggingConfiguration = require('../lib/api').getLoggingConfiguration as jest.MockedFunction<any>
const mockUpdateLoggingConfiguration = require('../lib/api').updateLoggingConfiguration as jest.MockedFunction<any>
const mockDeleteLoggingConfiguration = require('../lib/api').deleteLoggingConfiguration as jest.MockedFunction<any>

describe('LoggingConfiguration Page', () => {
  const mockPush = jest.fn()

  const mockConfig = {
    id: 1,
    company_id: 1,
    log_level: 'INFO',
    enable_database_logging: true,
    enable_console_logging: true,
    log_format: 'text',
    retention_days: 90,
    created_at: '2024-01-01T00:00:00',
    updated_at: '2024-01-01T00:00:00',
  }

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
      user: { is_superuser: true, id: 1, email: 'admin@ai-bos.com' },
      logout: jest.fn(),
    } as any)
    mockGetLoggingConfiguration.mockResolvedValue(mockConfig)
    mockUpdateLoggingConfiguration.mockResolvedValue({ ...mockConfig, log_level: 'DEBUG' })
    mockDeleteLoggingConfiguration.mockResolvedValue(undefined)
  })

  it('renders logging configuration page when authenticated', async () => {
    render(<LoggingConfigurationPage />)
    expect(screen.getByText('Logging Configuration')).toBeInTheDocument()
    expect(screen.getByText('Manage application logging settings')).toBeInTheDocument()
  })

  it('shows loading state initially', async () => {
    mockGetLoggingConfiguration.mockImplementation(() => new Promise(() => {}))
    render(<LoggingConfigurationPage />)
    expect(screen.getByText('Loading logging configuration...')).toBeInTheDocument()
  })

  it('displays form fields after loading', async () => {
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Log Level')).toBeInTheDocument()
    })
    expect(screen.getByText('Log Format')).toBeInTheDocument()
    expect(screen.getByText('Retention Days')).toBeInTheDocument()
    expect(screen.getByText('Database Logging')).toBeInTheDocument()
    expect(screen.getByText('Console Logging')).toBeInTheDocument()
  })

  it('displays current configuration values', async () => {
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByDisplayValue('90')).toBeInTheDocument()
    })
  })

  it('shows save and cancel buttons', async () => {
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument()
    })
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    expect(screen.getByText('Reset to Defaults')).toBeInTheDocument()
  })

  it('shows delete configuration button', async () => {
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Delete Configuration')).toBeInTheDocument()
    })
  })

  it('saves configuration when save button is clicked', async () => {
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument()
    })

    const saveButton = screen.getByText('Save Changes')
    act(() => {
      saveButton.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    await waitFor(() => {
      expect(mockUpdateLoggingConfiguration).toHaveBeenCalled()
    })
  })

  it('shows success message after saving', async () => {
    mockUpdateLoggingConfiguration.mockResolvedValue({ ...mockConfig, log_level: 'DEBUG' })
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument()
    })

    const saveButton = screen.getByText('Save Changes')
    act(() => {
      saveButton.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    await waitFor(() => {
      expect(screen.getByText('Logging configuration updated successfully')).toBeInTheDocument()
    })
  })

  it('handles error when loading configuration fails', async () => {
    mockGetLoggingConfiguration.mockRejectedValue(new Error('Network error'))
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('shows retry button when configuration fails to load', async () => {
    mockGetLoggingConfiguration.mockRejectedValue(new Error('Network error'))
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })
  })

  it('deletes configuration when delete button is clicked and confirmed', async () => {
    window.confirm = jest.fn(() => true)
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Delete Configuration')).toBeInTheDocument()
    })

    const deleteButton = screen.getByText('Delete Configuration')
    act(() => {
      deleteButton.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    await waitFor(() => {
      expect(mockDeleteLoggingConfiguration).toHaveBeenCalled()
    })
  })

  it('does not delete when confirmation is cancelled', async () => {
    window.confirm = jest.fn(() => false)
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(screen.getByText('Delete Configuration')).toBeInTheDocument()
    })

    const deleteButton = screen.getByText('Delete Configuration')
    act(() => {
      deleteButton.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(mockDeleteLoggingConfiguration).not.toHaveBeenCalled()
  })

  it('redirects to login when not authenticated', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: jest.fn(),
    } as any)
    render(<LoggingConfigurationPage />)
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })
})
