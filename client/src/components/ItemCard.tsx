import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

interface ItemCardProps {
  typeLabel: string
  title: string
  body?: string
  chips?: ReactNode
  menu?: ReactNode
  accent?: 'neuron' | 'command' | 'project' | 'neutral'
  className?: string
  children?: ReactNode
}

const accentBorder: Record<NonNullable<ItemCardProps['accent']>, string> = {
  neuron: 'border-l-[3px] border-l-[oklch(0.55_0.08_65)]',
  command: 'border-l-[3px] border-l-[oklch(0.4_0.05_250)]',
  project: 'border-l-[3px] border-l-[oklch(0.45_0.06_160)]',
  neutral: '',
}

export function ItemCard({
  typeLabel,
  title,
  body,
  chips,
  menu,
  accent = 'neutral',
  className,
  children,
}: ItemCardProps) {
  return (
    <article
      className={cn(
        'group relative flex h-full flex-col rounded-lg border border-border/80 bg-[oklch(0.995_0.003_85)] p-4 shadow-[0_1px_0_oklch(0.9_0.01_85)] transition-[transform,box-shadow,border-color] duration-200',
        'hover:-translate-y-0.5 hover:border-[oklch(0.75_0.06_65_/_0.55)] hover:shadow-md',
        accentBorder[accent],
        className,
      )}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <p className="text-[0.65rem] font-semibold tracking-[0.14em] text-muted-foreground uppercase">
          {typeLabel}
        </p>
        {menu ? <div className="shrink-0">{menu}</div> : null}
      </div>
      <h3 className="font-heading text-lg leading-snug tracking-tight">{title}</h3>
      {body ? (
        <p className="mt-2 line-clamp-3 flex-1 whitespace-pre-wrap text-sm text-muted-foreground">
          {body}
        </p>
      ) : null}
      {children}
      {chips ? (
        <div className="mt-3 flex flex-wrap gap-1.5">{chips}</div>
      ) : null}
    </article>
  )
}

interface StatusChipProps {
  children: ReactNode
  tone?: 'default' | 'success' | 'pending' | 'muted'
}

const chipTone: Record<NonNullable<StatusChipProps['tone']>, string> = {
  default:
    'bg-[oklch(0.94_0.02_65)] text-[oklch(0.38_0.06_65)] ring-1 ring-[oklch(0.8_0.05_65_/_0.5)]',
  success:
    'bg-[oklch(0.94_0.03_145)] text-[oklch(0.35_0.07_145)] ring-1 ring-[oklch(0.75_0.06_145_/_0.45)]',
  pending:
    'bg-[oklch(0.95_0.02_85)] text-muted-foreground ring-1 ring-border/70',
  muted: 'bg-muted text-muted-foreground ring-1 ring-border/60',
}

export function StatusChip({ children, tone = 'default' }: StatusChipProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-[0.7rem] font-medium',
        chipTone[tone],
      )}
    >
      {children}
    </span>
  )
}

interface CreateItemCardProps {
  label: string
  onClick: () => void
}

export function CreateItemCard({ label, onClick }: CreateItemCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex min-h-[10.5rem] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border/90 bg-[oklch(0.99_0.004_85_/_0.5)] px-4 py-6 text-sm text-muted-foreground transition-colors',
        'hover:border-[oklch(0.65_0.08_65)] hover:bg-[oklch(0.97_0.02_65_/_0.35)] hover:text-foreground',
        'focus-visible:ring-ring focus-visible:ring-2 focus-visible:outline-none',
      )}
    >
      <span className="flex size-9 items-center justify-center rounded-full border border-border/80 text-lg leading-none">
        +
      </span>
      <span className="font-medium">{label}</span>
    </button>
  )
}
