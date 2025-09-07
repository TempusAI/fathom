import type { Metadata } from 'next'
import { NuqsAdapter } from 'nuqs/adapters/next/app'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { geistSans, dmMono } from './fonts'
import './globals.css'

export const metadata: Metadata = {
  title: 'Agent UI',
  description:
    'A modern chat interface for AI agents built with Next.js, Tailwind CSS, and TypeScript. This template provides a ready-to-use UI for interacting with Agno agents.'
}

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${dmMono.variable} antialiased`}>
        <TooltipProvider>
          <NuqsAdapter>{children}</NuqsAdapter>
          <Toaster />
        </TooltipProvider>
      </body>
    </html>
  )
}
