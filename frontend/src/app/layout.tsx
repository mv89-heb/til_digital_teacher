import type { Metadata } from 'next'
import '@fontsource-variable/heebo'
import './globals.css'
import QueryProvider from '@/lib/QueryProvider'

export const metadata: Metadata = {
  title: 'המורה הפרטי הדיגיטלי - הכנה למבחן תיל',
  description: 'פלטפורמת לימוד חכמה להכנה למבחנים פסיכוטכניים',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="he" dir="rtl">
      <body className="font-heebo bg-slate-50 text-slate-900 min-h-screen flex flex-col">
        <QueryProvider>
          <main className="flex-grow">
            {children}
          </main>
        </QueryProvider>
      </body>
    </html>
  )
}
