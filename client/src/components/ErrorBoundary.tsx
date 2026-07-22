import { Component, type ErrorInfo, type ReactNode } from 'react'

import * as Sentry from '@sentry/react'

import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  message: string
}

/** Catches render errors in the subtree and reports them to Sentry when DSN is set. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    Sentry.captureException(error, {
      extra: { componentStack: info.componentStack },
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="mx-auto max-w-lg space-y-4 px-4 py-16 text-center">
          <h1 className="font-heading text-2xl">
            {this.props.fallbackTitle ?? 'Something went wrong'}
          </h1>
          <p className="text-sm text-muted-foreground">{this.state.message}</p>
          <Button
            onClick={() => {
              this.setState({ hasError: false, message: '' })
              window.location.assign('/projects')
            }}
          >
            Back to projects
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}
