import {
  ChevronDown,
  ChevronUp,
  Crosshair,
  Highlighter,
  Pencil,
  Search,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ExportBar } from '@/components/ExportBar'
import { Button } from '@/components/ui/button'
import { useI18n } from '@/i18n'
import { api } from '@/api'
import { cn } from '@/lib/utils'
import type { Job, JobDetail, Segment } from '@/types'

const POLL_STATES = new Set(['queued', 'normalizing', 'transcribing'])

// Debajo de esta confianza, la palabra se marca como "dudosa" para revisión.
const LOW_CONF = 0.6

const reducedMotion = () =>
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const scrollBehavior = (): ScrollBehavior => (reducedMotion() ? 'auto' : 'smooth')

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
  const [playing, setPlaying] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [query, setQuery] = useState('')
  const [follow, setFollow] = useState(true)
  const [review, setReview] = useState(true)
  const [matchPos, setMatchPos] = useState(0)
  const mediaRef = useRef<HTMLMediaElement | null>(null)
  const segRefs = useRef(new Map<number, HTMLElement>())

  const segments = detail?.segments ?? []

  // Carga los segmentos; mientras el job está activo, refresca cada 1.5 s para
  // el efecto de "transcript apareciendo en streaming" (doc 09).
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

  // Segmento que suena ahora (para resaltar y auto-desplazar).
  const activeSeg = useMemo(() => {
    for (let i = 0; i < segments.length; i++) {
      if (currentMs >= segments[i].start_ms && currentMs < segments[i].end_ms) return i
    }
    return -1
  }, [segments, currentMs])

  // Coincidencias de búsqueda a nivel de palabra.
  const q = query.trim().toLowerCase()
  const matches = useMemo(() => {
    if (!q) return [] as { si: number; wi: number }[]
    const out: { si: number; wi: number }[] = []
    segments.forEach((s, si) => {
      if (s.words?.length) {
        s.words.forEach((w, wi) => {
          if (w.w.toLowerCase().includes(q)) out.push({ si, wi })
        })
      } else if (s.text.toLowerCase().includes(q)) {
        out.push({ si, wi: -1 })
      }
    })
    return out
  }, [segments, q])

  useEffect(() => setMatchPos(0), [q])

  const gotoMatch = useCallback(
    (pos: number) => {
      if (!matches.length) return
      const p = ((pos % matches.length) + matches.length) % matches.length
      setMatchPos(p)
      const seg = segments[matches[p].si]
      segRefs.current
        .get(seg.index)
        ?.scrollIntoView({ block: 'center', behavior: scrollBehavior() })
    },
    [matches, segments],
  )

  // Auto-scroll: sigue el segmento que suena mientras se reproduce (doc 09).
  useEffect(() => {
    if (!follow || !playing || activeSeg < 0) return
    segRefs.current
      .get(segments[activeSeg]?.index)
      ?.scrollIntoView({ block: 'center', behavior: scrollBehavior() })
  }, [activeSeg, follow, playing, segments])

  // Atajos: espacio = play/pausa, ←/→ = saltar segmento. Se ignoran al escribir.
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
        const starts = segments.map((s) => s.start_ms)
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
  }, [segments, seek])

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

  const isVideo = job.media_type === 'video'
  const hasMedia = job.duration_sec != null
  const currentMatch = matches[matchPos]

  return (
    <div className="flex flex-col gap-4">
      {/* Cabecera pegajosa: reproductor + controles siempre a mano (doc 09). */}
      <div className="sticky top-0 z-20 -mx-1 flex flex-col gap-3 bg-background/95 px-1 pb-3 pt-2 backdrop-blur">
        {hasMedia &&
          (isVideo ? (
            <video
              ref={(el) => {
                mediaRef.current = el
              }}
              src={api.mediaUrl(job.id)}
              controls
              onTimeUpdate={(e) => setCurrentMs(e.currentTarget.currentTime * 1000)}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
              className="max-h-[40vh] w-full rounded-lg bg-black"
            />
          ) : (
            <audio
              ref={(el) => {
                mediaRef.current = el
              }}
              src={api.mediaUrl(job.id)}
              controls
              onTimeUpdate={(e) => setCurrentMs(e.currentTarget.currentTime * 1000)}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
              className="w-full"
            />
          ))}

        <div className="flex flex-wrap items-center gap-2">
          <h2 className="mr-auto text-sm font-semibold text-muted-foreground">
            {t('editor.title')}
          </h2>

          {segments.length > 0 && (
            <>
              <div className="flex items-center gap-1 rounded-md border border-input px-2">
                <Search className="size-3.5 opacity-60" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      gotoMatch(e.shiftKey ? matchPos - 1 : matchPos + 1)
                    }
                  }}
                  placeholder={t('search.placeholder')}
                  className="h-8 w-40 bg-transparent text-sm focus:outline-none"
                />
                {q && (
                  <span className="whitespace-nowrap text-xs text-muted-foreground">
                    {matches.length
                      ? t('search.count', { current: matchPos + 1, total: matches.length })
                      : t('search.none')}
                  </span>
                )}
                <button
                  type="button"
                  disabled={!matches.length}
                  onClick={() => gotoMatch(matchPos - 1)}
                  className="text-muted-foreground hover:text-foreground disabled:opacity-30"
                >
                  <ChevronUp className="size-4" />
                </button>
                <button
                  type="button"
                  disabled={!matches.length}
                  onClick={() => gotoMatch(matchPos + 1)}
                  className="text-muted-foreground hover:text-foreground disabled:opacity-30"
                >
                  <ChevronDown className="size-4" />
                </button>
              </div>

              <Button
                variant={follow ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => setFollow((f) => !f)}
                title={t('follow.label')}
                aria-pressed={follow}
              >
                <Crosshair className="size-3.5" />
                {t('follow.label')}
              </Button>

              <Button
                variant={review ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => setReview((r) => !r)}
                title={t('review.title')}
                aria-pressed={review}
              >
                <Highlighter className="size-3.5" />
                {t('review.label')}
              </Button>
            </>
          )}

          {job.status === 'completed' && segments.length > 0 && <ExportBar jobId={job.id} />}
        </div>
      </div>

      {segments.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
          {t('editor.empty')}
        </p>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">{t('editor.hint')}</p>
          <div className="flex flex-col gap-3 font-serif text-[1.05rem] leading-relaxed">
            {segments.map((seg, si) => (
              <SegmentRow
                key={seg.index}
                seg={seg}
                currentMs={currentMs}
                isActive={si === activeSeg}
                query={q}
                review={review}
                curMatchWi={currentMatch?.si === si ? currentMatch.wi : null}
                editing={editing === seg.index}
                registerRef={(el) => {
                  if (el) segRefs.current.set(seg.index, el)
                  else segRefs.current.delete(seg.index)
                }}
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
  isActive,
  query,
  review,
  curMatchWi,
  editing,
  registerRef,
  onEdit,
  onSave,
  onCancel,
  onSeek,
}: {
  seg: Segment
  currentMs: number
  isActive: boolean
  query: string
  review: boolean
  curMatchWi: number | null
  editing: boolean
  registerRef: (el: HTMLElement | null) => void
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
        ref={registerRef}
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
    <p
      ref={registerRef}
      onDoubleClick={onEdit}
      className={cn(
        'group relative rounded-md px-2 py-0.5 transition-colors hover:bg-accent/40',
        isActive && 'bg-brand/5',
      )}
    >
      <button
        type="button"
        onClick={onEdit}
        aria-label="edit"
        className="absolute right-1 top-1 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-foreground focus:opacity-100 group-hover:opacity-100"
      >
        <Pencil className="size-3.5" />
      </button>
      {seg.words && seg.words.length > 0 ? (
        seg.words.map((w, i) => {
          let hl = ''
          if (i === curMatchWi) hl = 'bg-warning/60 ring-1 ring-warning'
          else if (query && w.w.toLowerCase().includes(query)) hl = 'bg-warning/30'
          else if (i === active) hl = 'bg-brand/25 text-foreground'
          // Subrayado (compone con el fondo) para palabras de baja confianza.
          const uncertain =
            review && w.p != null && w.p < LOW_CONF
              ? 'underline decoration-warning decoration-dotted underline-offset-4'
              : ''
          return (
            <span
              key={i}
              onClick={() => onSeek(w.start_ms)}
              className={cn(
                'cursor-pointer rounded transition-colors hover:bg-brand/20',
                hl,
                uncertain,
              )}
            >
              {w.w}
            </span>
          )
        })
      ) : (
        <span onClick={() => onSeek(seg.start_ms)} className="cursor-pointer">
          {seg.text}
        </span>
      )}
    </p>
  )
}
