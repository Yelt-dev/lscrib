import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Combina clases condicionales y resuelve conflictos de Tailwind (convención shadcn). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Segundos → "m:ss" (para duraciones y el reloj del reproductor). */
export function formatClock(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  const m = Math.floor(s / 60)
  const rem = s % 60
  return `${m}:${rem.toString().padStart(2, '0')}`
}

/** Segundos restantes → texto humano ("~2 min", "~15 s"). */
export function formatEta(seconds: number): string {
  if (!isFinite(seconds) || seconds <= 0) return ''
  if (seconds < 60) return `~${Math.ceil(seconds)} s`
  return `~${Math.ceil(seconds / 60)} min`
}
