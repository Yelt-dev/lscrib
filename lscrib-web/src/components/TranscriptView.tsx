import { Pencil } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { ExportBar } from '@/components/ExportBar'
import { useI18n } from '@/i18n'
import { api } from '@/api'
import { cn } from '@/lib/utils'
import type { Job, JobDetail, Segment } from '@/types'

const POLL_STATES = new Set(['queued', 'normalizing', 'transcribing'])

/** ¿Qué palabra suena ahora? (para el resaltado sincronizado, doc 09). */
function activeWordKey(seg: Segment, ms: number): number | null {
  if (!seg.words) return null
  for (let i = 0; i < seg.words.length; i++) {
    const w = seg.words[i]
    if (ms >= w.start_ms && ms < w.end_ms) return i
  }
  return null
}

export function TranscriptView({ job }: { job: Job }) {
  const { t } = useI18n()
  const [detail, setDetail] = useState<JobDetail | null>(null)
  const [currentMs, setCurrentMs] = useState(0)
  const [editing, setEditing] = useState<number | null>(null)
  const mediaRef = useRef<HTMLMediaElement | null>(null)

  // Carga los segmentos; mientras el job está activo, refresca cada 1.5 s para
  // el efecto de "transcript apareciendo en streaming" (deleite, doc 09).
  useEffect(() => {
    let stop = false
    const load = () =>
      api
        .getJob(job.id)
        .then((d) => !stop && setDetail(d))
        .catch(() => {})
    load()
    if (POLL_STATES.has(job.status)) {
      const iv = setInterval(load, 1500)
      return () => {
        stop = true
        clearInterval(iv)
      }
    }
    return () => {
      stop = true
    }
  }, [job.id, job.status])

  const seek = useCallback((ms: number) => {
    const el = mediaRef.current
    if (!el) return
    el.currentTime = ms / 1000
    void el.play()
  }, [])

  // Atajos (doc 09): espacio = play/pausa, ←/→ = saltar segmento. Se ignoran
  // mientras se edita un segmento o con modificadores.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const el = mediaRef.current
      if (!el || e.metaKey || e.ctrlKey || e.altKey) return
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'TEXTAREA' || tag === 'INPUT') return

      if (e.code === 'Space') {
        e.preventDefault()
        if (el.paused) void el.play()
        else el.pause()
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        const cur = el.currentTime * 1000
        const starts = (detail?.segments ?? []).map((s) => s.start_ms)
        let target: number | undefined
        if (e.key === 'ArrowRight') target = starts.find((s) => s > cur + 50)
        else {
          const before = starts.filter((s) => s < cur - 250)
          target = before.length ? before[before.length - 1] : 0
        }
        if (target != null) {
          e.preventDefault()
          seek(target)
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [detail, seek])

  async function saveEdit(index: number, text: string) {
    setEditing(null)
    try {
      await api.updateSegment(job.id, index, text)
      setDetail((d) =>
        d
          ? { ...d, segments: d.segments.map((s) => (s.index === index ? { ...s, text } : s)) }
          : d,
      )
    } catch {
      /* si falla, el próximo poll reconcilia */
    }
  }

  const segments = detail?.segments ?? []
  const isVideo = job.media_type === 'video'
  const hasMedia = job.duration_sec != null

  return (
    <div className="flex flex-col gap-4">
      {/* Reproductor sincronizado (clic-palabra → salta el audio, doc 09). */}
      {hasMedia &&
        (isVideo ? (
          <video
            ref={(el) => {
              mediaRef.current = el
            }}
            src={api.mediaUrl(job.id)}
            controls
            onTimeUpdate={(e) => setCurrentMs(e.currentTarget.currentTime * 1000)}
            className="max-h-72 w-full rounded-lg bg-black"
          />
        ) : (
          <audio
            ref={(el) => {
              mediaRef.current = el
            }}
            src={api.mediaUrl(job.id)}
            controls
            onTimeUpdate={(e) => setCurrentMs(e.currentTarget.currentTime * 1000)}
            className="w-full"
          />
        ))}

      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">{t('editor.title')}</h2>
        {job.status === 'completed' && segments.length > 0 && (
          <ExportBar jobId={job.id} />
        )}
      </div>

      {segments.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
          {t('editor.empty')}
        </p>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">{t('editor.hintClick')}</p>
          <div className="flex flex-col gap-3 font-serif text-[1.05rem] leading-relaxed">
            {segments.map((seg) => (
              <SegmentRow
                key={seg.index}
                seg={seg}
                currentMs={currentMs}
                editing={editing === seg.index}
                onEdit={() => setEditing(seg.index)}
                onSave={(text) => saveEdit(seg.index, text)}
                onCancel={() => setEditing(null)}
                onSeek={seek}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function SegmentRow({
  seg,
  currentMs,
  editing,
  onEdit,
  onSave,
  onCancel,
  onSeek,
}: {
  seg: Segment
  currentMs: number
  editing: boolean
  onEdit: () => void
  onSave: (text: string) => void
  onCancel: () => void
  onSeek: (ms: number) => void
}) {
  const [draft, setDraft] = useState(seg.text)
  useEffect(() => setDraft(seg.text), [seg.text, editing])

  if (editing) {
    return (
      <textarea
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => onSave(draft)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) onSave(draft)
          if (e.key === 'Escape') onCancel()
        }}
        rows={Math.max(1, Math.ceil(draft.length / 80))}
        className="w-full resize-y rounded-md border border-input bg-transparent p-2 font-serif text-[1.05rem] leading-relaxed focus:outline-none focus:ring-2 focus:ring-ring"
      />
    )
  }

  const active = activeWordKey(seg, currentMs)

  return (
    <p className="group relative rounded-md px-1 hover:bg-accent/40">
      <button
        type="button"
        onClick={onEdit}
        aria-label="edit"
        className="absolute -left-6 top-1 hidden text-muted-foreground hover:text-foreground group-hover:block"
      >
        <Pencil className="size-3.5" />
      </button>
      {seg.words && seg.words.length > 0 ? (
        seg.words.map((w, i) => (
          <span
            key={i}
            onClick={() => onSeek(w.start_ms)}
            className={cn(
              'cursor-pointer rounded transition-colors hover:bg-brand/20',
              i === active && 'bg-brand/25 text-foreground',
            )}
          >
            {w.w}
          </span>
        ))
      ) : (
        <span onClick={() => onSeek(seg.start_ms)} className="cursor-pointer">
          {seg.text}
        </span>
      )}
    </p>
  )
}
