import { Ban, FileAudio, FileVideo, RotateCcw, Sparkles, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { LanguageSelect } from '@/components/LanguageSelect'
import { ModelSelect } from '@/components/ModelSelect'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { useI18n } from '@/i18n'
import { api, ApiError } from '@/api'
import { cn, formatClock, formatEta } from '@/lib/utils'
import type { Job, ModelStatus } from '@/types'

const ACTIVE = new Set(['queued', 'normalizing', 'transcribing'])

export function JobCard({
  job,
  models,
  selected,
  etaSec = 0,
  onSelect,
  onPatch,
  onDelete,
}: {
  job: Job
  models: ModelStatus[]
  selected: boolean
  etaSec?: number
  onSelect: () => void
  onPatch: (patch: Partial<Job>) => void
  onDelete: () => void
}) {
  const { t } = useI18n()
  const [model, setModel] = useState(job.model)
  const [language, setLanguage] = useState(job.language ?? 'auto')
  const [prompt, setPrompt] = useState(job.prompt ?? '')
  const [busy, setBusy] = useState(false)
  const [confirmDownload, setConfirmDownload] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const active = ACTIVE.has(job.status)
  const percent = Math.round(job.progress * 100)
  const FileIcon = job.media_type === 'video' ? FileVideo : FileAudio
  const selectedModel = models.find((m) => m.name === model)

  function onTranscribeClick() {
    // R2: si el modelo no está descargado, confirmar antes de bajar cientos de MB.
    if (selectedModel && !selectedModel.downloaded) setConfirmDownload(true)
    else void start()
  }

  async function start() {
    setBusy(true)
    try {
      const updated = await api.transcribe(job.id, { model, language, prompt })
      onPatch(updated)
      onSelect()
    } catch (err) {
      onPatch({
        status: 'failed',
        error: err instanceof ApiError ? err.message : t('error.generic'),
      })
    } finally {
      setBusy(false)
    }
  }

  async function cancel() {
    setBusy(true)
    try {
      onPatch(await api.cancel(job.id))
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    try {
      await api.remove(job.id)
      setConfirmDelete(false)
      onDelete()
    } catch {
      setBusy(false)
    }
  }

  const failedFfmpeg =
    job.status === 'failed' && /ffmpeg/i.test(job.error ?? '')

  return (
    <Card
      onClick={onSelect}
      className={cn(
        'cursor-pointer p-4 transition-shadow hover:shadow-md',
        selected && 'ring-2 ring-inset ring-brand',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <FileIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="min-w-0">
            <p className="truncate font-medium" title={job.original_filename}>
              {job.original_filename}
            </p>
            <p className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
              {job.duration_sec != null && (
                <span>
                  {t('job.duration')} {formatClock(job.duration_sec)}
                </span>
              )}
              <span>· {job.model}</span>
              {job.language && (
                <span>
                  · {job.language}
                  {job.status === 'completed' && ` (${t('job.detected')})`}
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <StatusBadge status={job.status} />
          {!active && (
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-muted-foreground hover:text-danger-fg"
              aria-label={t('job.delete')}
              title={t('job.delete')}
              onClick={(e) => {
                e.stopPropagation()
                setConfirmDelete(true)
              }}
            >
              <Trash2 className="size-4" />
            </Button>
          )}
        </div>
      </div>

      {/* `uploaded`: elegir modelo/idioma y transcribir (doc 07). */}
      {job.status === 'uploaded' && (
        <div className="mt-4 flex flex-col gap-3" onClick={(e) => e.stopPropagation()}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <ModelSelect models={models} value={model} onChange={setModel} disabled={busy} />
            <LanguageSelect value={language} onChange={setLanguage} disabled={busy} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              {t('vocab.label')}
            </label>
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={busy}
              placeholder={t('vocab.placeholder')}
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            />
            <p className="text-xs text-muted-foreground">{t('vocab.help')}</p>
          </div>
          <Button disabled={busy} onClick={onTranscribeClick}>
            <Sparkles className="size-4" />
            {t('job.transcribe')}
          </Button>
        </div>
      )}

      {/* Activo: barra de progreso en vivo + cancelar (R8). */}
      {active && (
        <div className="mt-4 flex flex-col gap-2" onClick={(e) => e.stopPropagation()}>
          <Progress
            value={job.status === 'transcribing' ? percent : null}
            indeterminate={job.status !== 'transcribing'}
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {job.status === 'queued' && t('progress.queued')}
              {job.status === 'normalizing' && t('progress.preparing')}
              {job.status === 'transcribing' && t('progress.transcribing', { percent })}
              {job.status === 'transcribing' && etaSec > 0 && (
                <> · {t('progress.eta', { eta: formatEta(etaSec) })}</>
              )}
            </span>
            <Button variant="ghost" size="sm" disabled={busy} onClick={cancel}>
              <Ban className="size-3.5" />
              {t('job.cancel')}
            </Button>
          </div>
        </div>
      )}

      {/* Fallo (R14) / cancelado: reintentar / reencolar. */}
      {(job.status === 'failed' || job.status === 'canceled') && (
        <div className="mt-4 flex flex-col gap-2" onClick={(e) => e.stopPropagation()}>
          {job.status === 'failed' && (
            <p className="text-sm text-danger-fg">
              {failedFfmpeg ? t('error.ffmpeg') : t('terminal.failed', { reason: job.error ?? '' })}
            </p>
          )}
          <Button
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={onTranscribeClick}
            className="self-start"
          >
            <RotateCcw className="size-3.5" />
            {job.status === 'failed' ? t('job.retry') : t('job.requeue')}
          </Button>
        </div>
      )}

      {/* R2: confirmar descarga de modelo no cacheado. */}
      <Dialog open={confirmDownload} onOpenChange={setConfirmDownload}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <DialogHeader>
            <DialogTitle>{t('dialog.download.title', { model })}</DialogTitle>
            <DialogDescription>
              {t('dialog.download.body', { model, size: selectedModel?.size_label ?? '' })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDownload(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              onClick={() => {
                setConfirmDownload(false)
                void start()
              }}
            >
              {t('dialog.download.confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* R3: confirmar borrado real. */}
      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <DialogHeader>
            <DialogTitle>{t('dialog.delete.title')}</DialogTitle>
            <DialogDescription>{t('dialog.delete.body')}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              {t('common.cancel')}
            </Button>
            <Button variant="destructive" disabled={busy} onClick={() => void remove()}>
              <Trash2 className="size-4" />
              {t('job.delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
