import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/features/auth/hooks/use-auth'

function parseHashParams(hash: string): URLSearchParams {
  const raw = hash.startsWith('#') ? hash.slice(1) : hash
  return new URLSearchParams(raw)
}

export function AuthCallbackPage() {
  const navigate = useNavigate()
  const { acceptFragmentToken } = useAuth()
  const [error, setError] = useState<string | null>(null)

  const params = useMemo(
    () => parseHashParams(window.location.hash),
    [],
  )

  useEffect(() => {
    const token = params.get('token')
    const authError = params.get('error')

    // Clear the fragment so the token is not left in history/URL bar.
    window.history.replaceState(null, '', window.location.pathname)

    if (authError) {
      setError(authError)
      return
    }
    if (!token) {
      setError('missing_token')
      return
    }

    acceptFragmentToken(token)
    navigate('/projects', { replace: true })
  }, [acceptFragmentToken, navigate, params])

  if (!error) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted-foreground">
        Signing you in…
      </div>
    )
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-4 px-6">
      <h1 className="font-heading text-3xl">Sign-in failed</h1>
      <p className="text-muted-foreground">
        Google OAuth returned <code className="text-foreground">{error}</code>.
        Try again from the login page.
      </p>
      <Button asChild>
        <Link to="/login">Back to login</Link>
      </Button>
    </main>
  )
}
