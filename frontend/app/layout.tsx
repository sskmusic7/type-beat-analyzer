import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Type Beat Analyzer - Shazam for Type Beats',
  description: 'Analyze your beat and see which artist it sounds like + trending intelligence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
