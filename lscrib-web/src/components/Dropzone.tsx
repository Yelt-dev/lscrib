import { UploadCloud } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'
import { useI18n } from '@/i18n'
import { cn } from '@/lib/utils'

export function Dropzone({
  onFile,
  disabled,
}: {
  onFile: (file: File) => void
  disabled?: boolean
}) {
  const { t } = useI18n()
  const inputRef = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)

  function handleDrop(e: DragEvent) {
    e.preventDefault()
    setOver(false)
    if (disabled) return
    const file = e.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) inputRef.current?.click()
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={handleDrop}
      className={cn(
        'group flex w-full cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        over
          ? 'border-brand bg-brand/5'
          : 'border-border hover:border-brand/60 hover:bg-accent/40',
        disabled && 'pointer-events-none opacity-50',
      )}
    >
      <UploadCloud
        className={cn(
          'size-9 transition-colors',
          over ? 'text-brand' : 'text-muted-foreground group-hover:text-brand/70',
        )}
      />
      <p className="text-lg font-medium">
        {over ? t('dropzone.drop') : t('dropzone.title')}
      </p>
      <p className="text-xs text-muted-foreground">{t('dropzone.hint')}</p>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*,video/*,.mp3,.wav,.m4a,.mp4,.mov,.mkv,.webm,.ogg,.flac"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onFile(file)
          e.target.value = '' // permite re-elegir el mismo archivo
        }}
      />
    </div>
  )
}
