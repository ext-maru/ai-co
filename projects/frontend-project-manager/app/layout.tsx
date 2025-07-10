import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Elders Guild Project Portal',
  description: 'RAGエルダー推奨による高度なプロジェクト管理・自動資料生成システム',
  keywords: ['project management', 'documentation', 'RAG', 'AI', 'automation'],
  authors: [{ name: 'Claude Elder', url: 'https://eldersguild.ai' }],
  creator: 'Elders Guild',
  publisher: 'Elders Guild',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'ja_JP',
    url: 'https://eldersguild.ai',
    title: 'Elders Guild Project Portal',
    description: 'RAGエルダー推奨による高度なプロジェクト管理・自動資料生成システム',
    siteName: 'Elders Guild',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Elders Guild Project Portal',
    description: 'RAGエルダー推奨による高度なプロジェクト管理・自動資料生成システム',
    creator: '@eldersguild',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#0ea5e9' },
    { media: '(prefers-color-scheme: dark)', color: '#1e293b' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 antialiased`}>
        <div className="min-h-full">
          {children}
        </div>
      </body>
    </html>
  )
}
