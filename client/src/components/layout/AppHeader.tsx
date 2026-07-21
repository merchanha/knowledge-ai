import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/features/auth/hooks/use-auth'

export function AppHeader() {
  const { user, logout, isLoggingOut } = useAuth()

  return (
    <header className="border-b border-border/80 bg-[oklch(0.99_0.004_85_/_0.85)] backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/projects" className="font-heading text-xl tracking-tight">
          Knowledge-AI
        </Link>
        <div className="flex items-center gap-3 text-sm">
          {user ? (
            <span className="hidden text-muted-foreground sm:inline">
              {user.email}
              {user.role === 'admin' ? (
                <span className="ml-2 text-xs text-[oklch(0.5_0.08_65)]">
                  admin
                </span>
              ) : null}
            </span>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            disabled={isLoggingOut}
            onClick={() => logout()}
          >
            Log out
          </Button>
        </div>
      </div>
    </header>
  )
}
