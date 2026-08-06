import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import DocumentationPage from '../app/(protected)/documentation/page'

// Mock the modules
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}))

jest.mock('../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../lib/api', () => ({
  getDocuments: jest.fn(),
  getDocumentStats: jest.fn(),
  getDocument: jest.fn(),
  createDocument: jest.fn(),
  updateDocument: jest.fn(),
  deleteDocument: jest.fn(),
  publishDocument: jest.fn(),
}))

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockGetDocuments = require('../lib/api').getDocuments as jest.MockedFunction<any>
const mockGetDocumentStats = require('../lib/api').getDocumentStats as jest.MockedFunction<any>

const mockStats = {
  total_documents: 8,
  published_documents: 4,
  draft_documents: 3,
  archived_documents: 1,
  total_companies_with_documents: 2,
  avg_documents_per_company: 4,
  documents_by_category: { general: 5, api: 3 },
  documents_by_status: { published: 4, draft: 3, archived: 1 },
}

const mockDocuments = [
  {
    id: 1,
    title: 'Welcome Guide',
    summary: 'Getting started with AI-BOS',
    category: 'guide',
    status: 'published',
    version: 2,
    author_name: 'Admin',
  },
  {
    id: 2,
    title: 'API Reference',
    summary: 'REST endpoints',
    category: 'api',
    status: 'draft',
    version: 1,
    author_name: 'Dev',
  },
]

describe('DocumentationPage', () => {
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
      user: {
        id: 1,
        email: 'admin@ai-bos.com',
        full_name: 'Admin',
        username: 'admin',
        is_active: true,
        is_superuser: true,
      },
      token: 'test-token',
      logout: jest.fn(),
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })
    mockGetDocumentStats.mockResolvedValue(mockStats)
  })

  it('renders loading state initially', () => {
    mockGetDocuments.mockImplementation(() => new Promise(() => {}))

    render(<DocumentationPage />)
    expect(screen.getByText('Loading documentation...')).toBeInTheDocument()
  })

  it('renders error state when data fetch fails', async () => {
    mockGetDocuments.mockRejectedValue(new Error('API Error'))

    render(<DocumentationPage />)

    await waitFor(() => {
      expect(screen.getByText('Error Loading Documentation')).toBeInTheDocument()
    })
  })

  it('renders statistics cards with correct counts', async () => {
    mockGetDocuments.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    })

    render(<DocumentationPage />)

    await waitFor(() => {
      expect(screen.getByText('Total Documents')).toBeInTheDocument()
      expect(screen.getByText('8')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  it('renders documents in the table', async () => {
    mockGetDocuments.mockResolvedValue({
      items: mockDocuments,
      total: 2,
      page: 1,
      page_size: 10,
    })

    render(<DocumentationPage />)

    await waitFor(() => {
      expect(screen.getByText('Welcome Guide')).toBeInTheDocument()
      expect(screen.getByText('API Reference')).toBeInTheDocument()
      expect(screen.getAllByText('Published').length).toBeGreaterThan(0)
    })
    expect(screen.getByText('All Documents (2)')).toBeInTheDocument()
  })

  it('shows empty state when there are no documents', async () => {
    mockGetDocuments.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    })

    render(<DocumentationPage />)

    await waitFor(() => {
      expect(screen.getByText('No documents found. Create your first document to get started.')).toBeInTheDocument()
    })
  })

  it('shows Create Document button for superusers', async () => {
    mockGetDocuments.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    })

    render(<DocumentationPage />)

    await waitFor(() => {
      expect(screen.getByText('+ Create Document')).toBeInTheDocument()
    })
  })

  it('hides Create Document button for non-superusers', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: {
        id: 2,
        email: 'user@ai-bos.com',
        full_name: 'User',
        username: 'user',
        is_active: true,
        is_superuser: false,
      },
      token: 'test-token',
      logout: jest.fn(),
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })
    mockGetDocuments.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    })

    render(<DocumentationPage />)

    await waitFor(() => {
      expect(screen.getByText('All Documents (0)')).toBeInTheDocument()
    })
    expect(screen.queryByText('+ Create Document')).not.toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      token: 'test-token',
      logout: jest.fn(),
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      refreshAccessToken: jest.fn(),
    })

    render(<DocumentationPage />)

    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})
