import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

interface ProgressProps extends ComponentProps<'div'> {
  /** 0–100. Si es null → barra indeterminada (animada). */
  value?: number | null
  indeterminate?: boolean
}

/** Barra de progreso accesible (role=progressbar). Soporta modo determinado e indeterminado. */
export function Progress({
  value,
  indeterminate = false,
  className,
  ...props
}: ProgressProps) {
  const pct = Math.min(100, Math.max(0, value ?? 0))
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={indeterminate ? undefined : Math.round(pct)}
      className={cn(
        'relative h-2 w-full overflow-hidden rounded-full bg-muted',
        className,
      )}
      {...props}
    >
      {indeterminate ? (
        <div className="absolute inset-y-0 w-1/3 animate-[shimmer_1.2s_ease-in-out_infinite] rounded-full bg-brand" />
      ) : (
        <div
          className="h-full rounded-full bg-brand transition-[width] duration-300 ease-out"
          style={{ width: `${pct}%` }}
        />
      )}
      <style>{`@keyframes shimmer{0%{left:-33%}100%{left:100%}}`}</style>
    </div>
  )
}
