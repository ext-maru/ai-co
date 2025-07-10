'use client'

import { useEffect } from 'react'
import { useSageStore } from '@/stores/sageStore'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useSageStore()

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
  }, [theme])

  return <>{children}</>
}