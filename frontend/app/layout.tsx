import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '../components/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PDF 파서',
  description: 'PDF 문서를 파싱하고 변환하는 애플리케이션',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <main className="min-h-screen bg-background">
            <div className="container mx-auto px-4 py-8">
              {children}
            </div>
          </main>
        </Providers>
      </body>
    </html>
  )
}
