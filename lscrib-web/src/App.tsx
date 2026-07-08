import { useCallback, useEffect, useRef, useState } from 'react'
import { Dropzone } from '@/components/Dropzone'
import { ThemeToggle, UiLangToggle } from '@/components/HeaderControls'
import { JobCard } from '@/components/JobCard'
import { JobsSidebar } from '@/components/JobsSidebar'
import { TranscriptView } from '@/components/TranscriptView'
import { useJobEvents } from '@/hooks/useJobEvents'
import { useI18n } from '@/i18n'
import { api, ApiError } from '@/api'
import type { Job, JobEvent, ModelStatus } from '@/types'

const ACTIVE = new Set(['queued', 'normalizing', 'transcribing'])

function App() {
  const { t } = useI18n()
  const [health, setHealth] = useState<boolean | null>(null)
  const [models, setModels] = useState<ModelStatus[]>([])
  const [defaultModel, setDefaultModel] = useState('small')
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [etaSec, setEtaSec] = useState(0)
  const rate = useRef<{ t0: number; p0: number } | null>(null)

  useEffect(() => {
    api.health().then(setHealth)
    api
      .models()
      .then((r) => {
        setModels(r.models)
        setDefaultModel(r.default)
      })
      .catch(() => {})
    api.listJobs().then(setJobs).catch(() => {})
  }, [])

  const patchJob = useCallback((id: string, patch: Partial<Job>) => {
    setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, ...patch } : j)))
  }, [])

  const removeJob = useCallback(
    (id: string) => {
      setJobs((prev) => prev.filter((j) => j.id !== id))
      setSelectedId((cur) => (cur === id ? null : cur))
    },
    [],
  )

  const moveJob = useCallback((id: string, direction: 'up' | 'down') => {
    api
      .move(id, direction)
      .then(setJobs)
      .catch(() => {})
  }, [])

  // Solo hay un job activo a la vez (R7): App mantiene la única suscripción SSE.
  const activeJob = jobs.find((j) => ACTIVE.has(j.status)) ?? null

  const onEvent = useCallback(
    (e: JobEvent) => {
      if (!activeJob) return
      if (e.status === 'transcribing' && e.progress > 0) {
        if (!rate.current) rate.current = { t0: Date.now(), p0: e.progress }
        else {
          const elapsed = (Date.now() - rate.current.t0) / 1000
          const done = e.progress - rate.current.p0
          if (done > 0.001) setEtaSec((elapsed / done) * (1 - e.progress))
        }
      } else {
        rate.current = null
        setEtaSec(0)
      }
      patchJob(activeJob.id, {
        status: e.status,
        progress: e.progress,
        language: e.language ?? activeJob.language,
        error: e.error,
      })
    },
    [activeJob, patchJob],
  )

  useJobEvents(activeJob?.id ?? null, !!activeJob, onEvent)

  async function handleFile(file: File) {
    setUploading(true)
    setNotice(null)
    try {
      const { job, existing } = await api.createJob(file, defaultModel, 'auto')
      setJobs((prev) =>
        prev.some((j) => j.id === job.id)
          ? prev.map((j) => (j.id === job.id ? job : j))
          : [job, ...prev],
      )
      setSelectedId(job.id)
      if (existing) setNotice(t('error.exists'))
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : t('error.generic'))
    } finally {
      setUploading(false)
    }
  }

  const selected = jobs.find((j) => j.id === selectedId) ?? null
  const showTranscript =
    selected && (selected.status === 'transcribing' || selected.status === 'completed')

  return (
    <div className="min-h-svh">
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        {/* Wordmark: Playwrite Indonesia (caligráfica) = la "tinta del escribano"
            (doc 10). Auto-hospedada, local (R1). */}
        <h1 className="select-none font-logo text-2xl leading-none">lscrib</h1>
        <div className="flex items-center gap-1">
          <UiLangToggle />
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="flex flex-col gap-8 lg:flex-row">
          <section className="flex min-w-0 flex-1 flex-col gap-6">
            <Dropzone onFile={handleFile} disabled={uploading} />

            {notice && (
              <div className="rounded-lg border border-warning/40 bg-warning/10 px-4 py-2 text-sm text-warning">
                {notice}
              </div>
            )}

            {selected && (
              <JobCard
                job={selected}
                models={models}
                selected
                etaSec={etaSec}
                onSelect={() => setSelectedId(selected.id)}
                onPatch={(patch) => patchJob(selected.id, patch)}
                onDelete={() => removeJob(selected.id)}
              />
            )}

            {showTranscript && <TranscriptView job={selected} />}
          </section>

          <JobsSidebar
            jobs={jobs}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onMove={moveJob}
          />
        </div>
      </main>

      <footer className="mx-auto max-w-6xl px-6 pb-8 text-xs text-muted-foreground">
        {health === null
          ? t('backend.checking')
          : health
            ? `● ${t('backend.connected')}`
            : `○ ${t('backend.offline')}`}
      </footer>
    </div>
  )
}

export default App
