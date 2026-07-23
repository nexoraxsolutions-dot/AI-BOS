import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import Navigation from '../components/Navigation'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  })),
}))

// Mock AuthContext
const mockLogout = jest.fn()
jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    logout: mockLogout,
  }),
}))

describe('Navigation', () => {
  beforeEach(() => {
    mockPush.mockClear()
    mockLogout.mockClear()
  })

  it('renders navigation when authenticated', () => {
    render(<Navigation />)

    expect(screen.getByText('AI-BOS')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Users')).toBeInTheDocument()
    expect(screen.getByText('Companies')).toBeInTheDocument()
    expect(screen.getByText('Sign Out')).toBeInTheDocument()
  })

  it('navigates to dashboard when AI-BOS logo is clicked', () => {
    render(<Navigation />)

    const logoButton = screen.getByText('AI-BOS')
    fireEvent.click(logoButton)

    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('navigates to users page when Users is clicked', () => {
    render(<Navigation />)

    const usersButton = screen.getByText('Users')
    fireEvent.click(usersButton)

    expect(mockPush).toHaveBeenCalledWith('/users')
  })

  it('navigates to companies page when Companies is clicked', () => {
    render(<Navigation />)

    const companiesButton = screen.getByText('Companies')
    fireEvent.click(companiesButton)

    expect(mockPush).toHaveBeenCalledWith('/companies')
  })

  it('navigates to profile page when Profile is clicked', () => {
    render(<Navigation />)

    const profileButton = screen.getByText('Profile')
    fireEvent.click(profileButton)

    expect(mockPush).toHaveBeenCalledWith('/profile')
  })

  it('navigates to Redis page when Redis is clicked', () => {
    render(<Navigation />)

    const redisButton = screen.getByText('Redis')
    fireEvent.click(redisButton)

    expect(mockPush).toHaveBeenCalledWith('/redis')
  })

  it('navigates to Environment Variables page when clicked', () => {
    render(<Navigation />)

    const envVarButton = screen.getByText('Environment Variables')
    fireEvent.click(envVarButton)

    expect(mockPush).toHaveBeenCalledWith('/environment-variables')
  })

  it('calls logout and navigates when Sign Out is clicked', () => {
    render(<Navigation />)

    const signOutButton = screen.getByText('Sign Out')
    fireEvent.click(signOutButton)

    expect(mockLogout).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/')
  })
})
