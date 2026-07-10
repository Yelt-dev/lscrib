import {
  AlertTriangle,
  Check,
  Clock,
  FileAudio,
  Loader2,
  Wand2,
  XCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useI18n } from '@/i18n'
import type { TKey } from '@/i18n/dictionaries'
import type { JobStatus } from '@/types'

// Estado → color + ícono; nunca solo color (accesibilidad).
const MAP: Record<
  JobStatus,
  {
    variant: 'muted' | 'warning' | 'brand' | 'success' | 'danger'
    Icon: typeof Check
    spin?: boolean
  }
> = {
  uploaded: { variant: 'muted', Icon: FileAudio },
  queued: { variant: 'warning', Icon: Clock },
  normalizing: { variant: 'brand', Icon: Loader2, spin: true },
  transcribing: { variant: 'brand', Icon: Wand2, spin: true },
  completed: { variant: 'success', Icon: Check },
  failed: { variant: 'danger', Icon: AlertTriangle },
  canceled: { variant: 'muted', Icon: XCircle },
}

export function StatusBadge({ status }: { status: JobStatus }) {
  const { t } = useI18n()
  const { variant, Icon, spin } = MAP[status]
  return (
    <Badge
      variant={variant}
      className={status === 'completed' ? 'animate-[celebrate_0.4s_ease-out]' : undefined}
    >
      <Icon className={spin ? 'size-3.5 animate-spin' : 'size-3.5'} />
      {t(`status.${status}` as TKey)}
    </Badge>
  )
}
