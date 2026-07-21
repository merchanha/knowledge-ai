import * as Sentry from '@sentry/react'

const dsn = import.meta.env.VITE_SENTRY_DSN

/** Stub-friendly Sentry init — empty DSN skips sending in local dev. */
export function initSentry(): void {
  if (!dsn) {
    return
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  })
}
