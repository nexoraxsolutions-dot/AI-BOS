import './globals.css'
import type { Metadata } from 'next'
import { AuthProvider } from '../context/AuthContext'
import Navigation from '../components/Navigation'

export const metadata: Metadata = {
  title: 'AI-BOS',
  description: 'Enterprise AI Business Operating System',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Navigation />
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
