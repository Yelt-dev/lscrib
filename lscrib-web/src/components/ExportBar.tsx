import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useI18n } from '@/i18n'
import { api } from '@/api'

const FORMATS = ['srt', 'vtt', 'txt', 'md'] as const

export function ExportBar({ jobId }: { jobId: string }) {
  const { t } = useI18n()
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-muted-foreground">{t('export.as')}</span>
      {FORMATS.map((f) => (
        <Button key={f} asChild variant="outline" size="sm">
          {/* Descarga directa desde el backend, que genera el formato al vuelo. */}
          <a href={api.exportUrl(jobId, f)} download>
            <Download className="size-3.5" />
            {f.toUpperCase()}
          </a>
        </Button>
      ))}
    </div>
  )
}
