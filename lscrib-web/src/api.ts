/** Cliente HTTP tipado del backend lscrib-api. `/api` va proxied a :8000 (vite). */

import type { Job, JobDetail, JobPage, ModelsResponse, Segment } from './types'

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

  listJobs(limit = 30, offset = 0): Promise<JobPage> {
    return fetch(`/api/jobs?limit=${limit}&offset=${offset}`).then((r) =>
      parse<JobPage>(r),
    )
  },

  getJob(id: string): Promise<JobDetail> {
    return fetch(`/api/jobs/${id}`).then((r) => parse<JobDetail>(r))
  },

  /** Sube el archivo → crea Job en `uploaded`. `existing` indica si ya había un job con el mismo contenido (dedup por hash). */
  async createJob(
    file: File,
    model: string,
    language: string,
  ): Promise<{ job: Job; existing: boolean }> {
    const form = new FormData()
    form.append('file', file)
    form.append('model', model)
    form.append('language', language)
    const res = await fetch('/api/jobs', { method: 'POST', body: form })
    const job = await parse<Job>(res)
    return { job, existing: res.headers.get('X-Existing-Job') === 'true' }
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
