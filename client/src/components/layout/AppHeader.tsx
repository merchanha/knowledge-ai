import { Link, NavLink } from 'react-router-dom'
import { UserRound } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/features/auth/hooks/use-auth'
import { cn } from '@/lib/utils'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'rounded-md px-2 py-1 text-sm transition-colors hover:bg-muted/70 hover:text-foreground',
    isActive
      ? 'bg-muted/80 font-medium text-foreground'
      : 'text-muted-foreground',
  )

export function AppHeader() {
  const { user, logout, isLoggingOut } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-[oklch(0.99_0.004_85_/_0.9)] backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3 sm:gap-5">
          <Link
            to="/projects"
            className="font-heading shrink-0 text-xl tracking-tight"
          >
            Knowledge-AI
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            <NavLink to="/projects" className={navLinkClass}>
              Projects
            </NavLink>
            <NavLink to="/knowledge" className={navLinkClass}>
              Knowledge
            </NavLink>
            <NavLink to="/commands" className={navLinkClass}>
              Commands
            </NavLink>
            <NavLink to="/account" className={navLinkClass}>
              Account
            </NavLink>
            {isAdmin ? (
              <NavLink to="/users" className={navLinkClass}>
                Users
              </NavLink>
            ) : null}
          </nav>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              aria-label="Account menu"
            >
              <UserRound className="size-4" />
              <span className="hidden max-w-[10rem] truncate sm:inline">
                {user?.email ?? 'Account'}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-52">
            {user ? (
              <>
                <DropdownMenuLabel className="font-normal">
                  <p className="truncate text-sm font-medium">{user.email}</p>
                  {isAdmin ? (
                    <p className="text-xs text-[oklch(0.5_0.08_65)]">admin</p>
                  ) : null}
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/account">Account settings</Link>
                </DropdownMenuItem>
                {isAdmin ? (
                  <DropdownMenuItem asChild>
                    <Link to="/users">Manage users</Link>
                  </DropdownMenuItem>
                ) : null}
                <DropdownMenuSeparator />
              </>
            ) : null}
            <DropdownMenuItem
              disabled={isLoggingOut}
              onClick={() => logout()}
            >
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-2 md:hidden sm:px-6">
        <NavLink to="/projects" className={navLinkClass}>
          Projects
        </NavLink>
        <NavLink to="/knowledge" className={navLinkClass}>
          Knowledge
        </NavLink>
        <NavLink to="/commands" className={navLinkClass}>
          Commands
        </NavLink>
        <NavLink to="/account" className={navLinkClass}>
          Account
        </NavLink>
        {isAdmin ? (
          <NavLink to="/users" className={navLinkClass}>
            Users
          </NavLink>
        ) : null}
      </nav>
    </header>
  )
}
