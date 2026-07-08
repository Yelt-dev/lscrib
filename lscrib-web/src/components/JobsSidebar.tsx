import { ChevronDown, ChevronUp } from 'lucide-react'
import { StatusBadge } from '@/components/StatusBadge'
import { Progress } from '@/components/ui/progress'
import { useI18n } from '@/i18n'
import { cn } from '@/lib/utils'
import type { Job } from '@/types'

const ACTIVE = new Set(['queued', 'normalizing', 'transcribing'])

export function JobsSidebar({
  jobs,
  selectedId,
  onSelect,
  onMove,
}: {
  jobs: Job[]
  selectedId: string | null
  onSelect: (id: string) => void
  onMove: (id: string, direction: 'up' | 'down') => void
}) {
  const { t } = useI18n()
  const queuedIds = jobs.filter((j) => j.status === 'queued').map((j) => j.id)

  return (
    <aside className="flex w-full flex-col gap-2 lg:w-80">
      <h2 className="px-1 text-sm font-semibold text-muted-foreground">
        {t('sidebar.title')}
      </h2>
      {jobs.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
          {t('sidebar.empty')}
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {jobs.map((job) => {
            const qi = queuedIds.indexOf(job.id)
            const isQueued = qi !== -1
            return (
              <li key={job.id}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => onSelect(job.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') onSelect(job.id)
                  }}
                  className={cn(
                    'flex w-full cursor-pointer flex-col gap-1.5 rounded-lg border border-border bg-card p-3 text-left transition-colors hover:bg-accent/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    selectedId === job.id && 'ring-2 ring-brand',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className="truncate text-sm font-medium"
                      title={job.original_filename}
                    >
                      {job.original_filename}
                    </span>
                    <div className="flex shrink-0 items-center gap-1">
                      {isQueued && (
                        <span className="flex" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            aria-label={t('queue.moveUp')}
                            title={t('queue.moveUp')}
                            disabled={qi === 0}
                            onClick={() => onMove(job.id, 'up')}
                            className="rounded p-0.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                          >
                            <ChevronUp className="size-3.5" />
                          </button>
                          <button
                            type="button"
                            aria-label={t('queue.moveDown')}
                            title={t('queue.moveDown')}
                            disabled={qi === queuedIds.length - 1}
                            onClick={() => onMove(job.id, 'down')}
                            className="rounded p-0.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                          >
                            <ChevronDown className="size-3.5" />
                          </button>
                        </span>
                      )}
                      <StatusBadge status={job.status} />
                    </div>
                  </div>
                  {ACTIVE.has(job.status) && (
                    <Progress
                      value={job.status === 'transcribing' ? job.progress * 100 : null}
                      indeterminate={job.status !== 'transcribing'}
                      className="h-1.5"
                    />
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </aside>
  )
}
