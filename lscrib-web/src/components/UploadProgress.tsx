import { Loader2, UploadCloud } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { useI18n } from '@/i18n'

/** Ocupa el sitio de la Dropzone mientras el archivo sube.
 *
 *  `fraction` va de 0 a 1. Al llegar a 1 la subida terminó pero el servidor
 *  sigue trabajando (calcula el hash del archivo antes de responder), así que
 *  pasamos a indeterminado en vez de dejar un 100% congelado que parece colgado. */
export function UploadProgress({
  filename,
  fraction,
}: {
  filename: string
  fraction: number
}) {
  const { t } = useI18n()
  const percent = Math.round(fraction * 100)
  const hashing = fraction >= 1

  return (
    <div className="flex w-full flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-brand bg-brand/5 p-10 text-center">
      {hashing ? (
        <Loader2 className="size-9 animate-spin text-brand" />
      ) : (
        <UploadCloud className="size-9 text-brand" />
      )}
      <p className="max-w-full truncate text-lg font-medium" title={filename}>
        {filename}
      </p>
      <Progress value={hashing ? null : percent} indeterminate={hashing} />
      <p className="text-xs text-muted-foreground">
        {hashing ? t('upload.processing') : t('upload.uploading', { percent })}
      </p>
    </div>
  )
}
