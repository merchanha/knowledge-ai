import { Outlet } from 'react-router-dom'

import { AppHeader } from '@/components/layout/AppHeader'

export function AppShell() {
  return (
    <div className="flex min-h-dvh flex-col">
      <AppHeader />
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6 sm:px-6">
        <Outlet />
      </div>
    </div>
  )
}
