import { Link, useLocation } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/features/auth/hooks/use-auth'
import { clearAccessToken } from '@/features/auth/session'
import { getApiErrorMessage } from '@/lib/errors'

export function LoginPage() {
  const location = useLocation()
  const { login, user, isLoadingUser, token, userError } = useAuth()

  const sessionExpired =
    Boolean(
      (location.state as { sessionExpired?: boolean } | null)?.sessionExpired,
    ) || Boolean(token && userError)

  // Only treat the session as usable when /auth/me succeeded — a leftover
  // Bearer in memory is not enough (expired JWT still looks "authenticated").
  const canEnterApp = Boolean(user)

  return (
    <main className="relative flex min-h-dvh flex-col justify-end overflow-hidden px-6 pb-16 pt-10 sm:justify-center sm:px-12 lg:px-20">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(160deg,oklch(0.28_0.04_250)_0%,oklch(0.35_0.05_250)_42%,oklch(0.45_0.08_65)_100%)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-40 [background-image:radial-gradient(circle_at_1px_1px,oklch(1_0_0_/_0.18)_1px,transparent_0)] [background-size:28px_28px]"
      />
      <div
        aria-hidden
        className="animate-soft-pulse pointer-events-none absolute -right-24 top-16 size-72 rounded-full bg-[oklch(0.72_0.1_65_/_0.35)] blur-3xl"
      />

      <div className="relative z-10 max-w-xl text-[oklch(0.97_0.01_85)]">
        <p className="animate-fade-up font-heading text-5xl tracking-tight sm:text-7xl">
          Knowledge-AI
        </p>
        <h1 className="animate-fade-up-delay mt-5 max-w-md text-lg font-medium text-[oklch(0.92_0.02_85)] sm:text-xl">
          Project knowledge for coding agents — organized, searchable, scoped.
        </h1>

        {sessionExpired && !canEnterApp ? (
          <p
            className="animate-fade-up-delay mt-6 max-w-md text-sm text-[oklch(0.88_0.04_65)]"
            role="status"
          >
            Your session expired or the access token is no longer valid. Sign in
            again to continue
            {userError
              ? ` (${getApiErrorMessage(userError, 'Invalid or expired token')})`
              : ''}
            .
          </p>
        ) : null}

        <div className="animate-fade-up-delay mt-10 flex flex-wrap items-center gap-4">
          {canEnterApp ? (
            <Button asChild size="lg" variant="secondary">
              <Link to="/projects">Open projects</Link>
            </Button>
          ) : isLoadingUser && token ? (
            <p className="text-sm text-[oklch(0.9_0.02_85)]">
              Checking session…
            </p>
          ) : (
            <Button
              size="lg"
              variant="secondary"
              onClick={() => {
                clearAccessToken()
                login()
              }}
            >
              Continue with Google
            </Button>
          )}
        </div>
      </div>
    </main>
  )
}
