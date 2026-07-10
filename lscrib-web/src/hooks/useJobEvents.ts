import { useEffect, useRef } from 'react'
import { isTerminal, type JobEvent } from '@/types'

/**
 * Se suscribe al SSE de progreso de un job (`/api/jobs/{id}/events`) mientras
 * está activo. Llama `onEvent` en cada actualización y cierra la conexión al
 * llegar a un estado terminal.
 */
export function useJobEvents(
  jobId: string | null,
  active: boolean,
  onEvent: (e: JobEvent) => void,
) {
  const cb = useRef(onEvent)
  cb.current = onEvent

  useEffect(() => {
    if (!jobId || !active) return
    const es = new EventSource(`/api/jobs/${jobId}/events`)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as JobEvent
        cb.current(data)
        if (isTerminal(data.status)) es.close()
      } catch {
        /* evento keep-alive (ping) o payload no-JSON: ignorar */
      }
    }
    es.onerror = () => es.close()
    return () => es.close()
  }, [jobId, active])
}
