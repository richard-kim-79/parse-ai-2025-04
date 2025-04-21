'use client'

import { ThemeProvider } from 'next-themes'
import Navbar from '@/components/Navbar'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <Navbar />
      {children}
    </ThemeProvider>
  )
} 