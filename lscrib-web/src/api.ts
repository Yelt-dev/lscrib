/** Cliente HTTP tipado del backend lscrib-api. `/api` va proxied a :8000 (vite). */

import type {
  Job,
  JobDetail,
  JobPage,
  ModelsResponse,
  Segment,
  SystemInfo,
} from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  async health(): Promise<boolean> {
    try {
      const r = await fetch('/health')
      const d = await r.json()
      return d.status === 'ok'
    } catch {
      return false
    }
  },

  models(): Promise<ModelsResponse> {
    return fetch('/api/models').then((r) => parse<ModelsResponse>(r))
  },

  system(): Promise<SystemInfo> {
    return fetch('/api/system').then((r) => parse<SystemInfo>(r))
  },

  listJobs(limit = 30, offset = 0): Promise<JobPage> {
    return fetch(`/api/jobs?limit=${limit}&offset=${offset}`).then((r) =>
      parse<JobPage>(r),
    )
  },

  getJob(id: string): Promise<JobDetail> {
    return fetch(`/api/jobs/${id}`).then((r) => parse<JobDetail>(r))
  },

  /** Sube el archivo → crea Job en `uploaded`. `existing` indica si ya había un job con el mismo contenido (dedup por hash).
   *
   *  Usa XHR y no `fetch` porque `fetch` no reporta progreso de subida: con un
   *  audio de cientos de MB el usuario necesita ver que algo está pasando.
   *  `onProgress` recibe 0–1; llega a 1 cuando el archivo terminó de subir, y
   *  el servidor todavía tarda un poco más en hashearlo y responder. */
  createJob(
    file: File,
    model: string,
    language: string,
    onProgress?: (fraction: number) => void,
  ): Promise<{ job: Job; existing: boolean }> {
    const form = new FormData()
    form.append('file', file)
    form.append('model', model)
    form.append('language', language)

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/jobs')

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress?.(e.loaded / e.total)
      }

      xhr.onload = () => {
        let body: unknown = null
        try {
          body = JSON.parse(xhr.responseText)
        } catch {
          /* respuesta sin JSON */
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve({
            job: body as Job,
            existing: xhr.getResponseHeader('X-Existing-Job') === 'true',
          })
          return
        }
        const detail = (body as { detail?: string } | null)?.detail ?? xhr.statusText
        reject(new ApiError(xhr.status, detail))
      }

      // El backend puede morir a media subida (p. ej. lo mata el OOM killer):
      // eso llega aquí, no como respuesta HTTP.
      xhr.onerror = () => reject(new ApiError(0, 'network'))
      xhr.onabort = () => reject(new ApiError(0, 'aborted'))

      xhr.send(form)
    })
  },

  transcribe(
    id: string,
    opts?: { model?: string; language?: string; prompt?: string },
  ): Promise<Job> {
    const q = new URLSearchParams()
    if (opts?.model) q.set('model', opts.model)
    if (opts?.language) q.set('language', opts.language)
    if (opts?.prompt != null) q.set('prompt', opts.prompt)
    const qs = q.toString()
    return fetch(`/api/jobs/${id}/transcribe${qs ? `?${qs}` : ''}`, {
      method: 'POST',
    }).then((r) => parse<Job>(r))
  },

  cancel(id: string): Promise<Job> {
    return fetch(`/api/jobs/${id}/cancel`, { method: 'POST' }).then((r) => parse<Job>(r))
  },

  move(id: string, direction: 'up' | 'down'): Promise<Job[]> {
    return fetch(`/api/jobs/${id}/move?direction=${direction}`, {
      method: 'POST',
    }).then((r) => parse<Job[]>(r))
  },

  async remove(id: string): Promise<void> {
    const res = await fetch(`/api/jobs/${id}`, { method: 'DELETE' })
    if (!res.ok && res.status !== 204) {
      await parse<unknown>(res) // lanza ApiError con el detalle
    }
  },

  updateSegment(id: string, index: number, text: string): Promise<Segment> {
    return fetch(`/api/jobs/${id}/segments/${index}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).then((r) => parse<Segment>(r))
  },

  mediaUrl(id: string): string {
    return `/api/jobs/${id}/media`
  },

  exportUrl(id: string, format: string): string {
    return `/api/jobs/${id}/export?format=${format}`
  },
}
