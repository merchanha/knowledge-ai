import { toast, useToasts, type ToastTone } from '@/lib/toast'
import { cn } from '@/lib/utils'

const toneClass: Record<ToastTone, string> = {
  success: 'border-[oklch(0.55_0.08_145)] bg-[oklch(0.97_0.02_145)]',
  error: 'border-destructive/40 bg-[oklch(0.97_0.02_25)] text-destructive',
  info: 'border-border bg-card',
}

export function ToastViewport() {
  const items = useToasts()

  if (items.length === 0) return null

  return (
    <div
      className="pointer-events-none fixed right-4 bottom-4 z-[100] flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      aria-live="polite"
    >
      {items.map((item) => (
        <div
          key={item.id}
          className={cn(
            'pointer-events-auto animate-fade-up rounded-md border px-3 py-2 text-sm shadow-sm',
            toneClass[item.tone],
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <p>{item.message}</p>
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={() => toast.dismiss(item.id)}
            >
              Dismiss
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
