/** Tipos espejo de los esquemas del backend (lscrib-api). */

export type JobStatus =
  | 'uploaded'
  | 'queued'
  | 'normalizing'
  | 'transcribing'
  | 'completed'
  | 'failed'
  | 'canceled'

export type MediaType = 'audio' | 'video'

export interface Word {
  w: string
  start_ms: number
  end_ms: number
  p?: number | null // confianza 0–1 del modelo (resaltado de dudosas)
}

export interface Segment {
  index: number
  start_ms: number
  end_ms: number
  text: string
  words: Word[] | null
}

export interface Job {
  id: string
  original_filename: string
  media_type: MediaType
  duration_sec: number | null
  language: string | null
  model: string
  prompt?: string | null
  status: JobStatus
  progress: number
  position: number
  error: string | null
}

export interface JobPage {
  items: Job[]
  total: number
}

export interface JobDetail extends Job {
  segments: Segment[]
}

export interface ModelStatus {
  name: string
  size_label: string
  speed: string
  quality: string
  note: string
  downloaded: boolean
}

export interface ModelsResponse {
  default: string
  models: ModelStatus[]
}

/** Evento SSE emitido por el worker (worker/events.py). */
export interface JobEvent {
  status: JobStatus
  progress: number
  language: string | null
  error: string | null
}

export const TERMINAL_STATES: JobStatus[] = ['completed', 'failed', 'canceled']

export function isTerminal(status: JobStatus): boolean {
  return TERMINAL_STATES.includes(status)
}
