interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <p className="animate-pulse text-sm text-muted-foreground" role="status">
      {label}
    </p>
  )
}
