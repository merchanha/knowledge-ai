import { Outlet, useLocation } from 'react-router-dom'

import { AppHeader } from '@/components/layout/AppHeader'
import { cn } from '@/lib/utils'

export function AppShell() {
  const { pathname } = useLocation()
  const wide =
    pathname.includes('/directories') ||
    pathname.startsWith('/knowledge') ||
    pathname.startsWith('/commands')

  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader />
      <div
        className={cn(
          'mx-auto flex w-full flex-1 flex-col px-4 py-6 sm:px-6',
          wide ? 'max-w-7xl' : 'max-w-6xl',
        )}
      >
        <Outlet />
      </div>
    </div>
  )
}
