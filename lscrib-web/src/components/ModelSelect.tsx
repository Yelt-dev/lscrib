import { Check, Download, Info } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useI18n } from '@/i18n'
import type { ModelStatus } from '@/types'

export function ModelSelect({
  models,
  value,
  onChange,
  disabled,
}: {
  models: ModelStatus[]
  value: string
  onChange: (name: string) => void
  disabled?: boolean
}) {
  const { t } = useI18n()
  const selected = models.find((m) => m.name === value)

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">
          {t('model.label')}
        </label>
        {selected && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                aria-label={`${selected.speed} · ${selected.quality}`}
                className="text-muted-foreground hover:text-foreground"
              >
                <Info className="size-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              {selected.size_label} · {selected.speed} · {selected.quality}
              {selected.note ? ` — ${selected.note}` : ''}
            </TooltipContent>
          </Tooltip>
        )}
      </div>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {models.map((m) => (
            <SelectItem key={m.name} value={m.name}>
              <span className="flex w-full items-center justify-between gap-4">
                <span className="font-medium">{m.name}</span>
                <span className="flex items-center gap-2 text-xs text-muted-foreground">
                  {m.size_label} · {m.quality}
                  {m.downloaded ? (
                    <Check className="size-3.5 text-success" />
                  ) : (
                    <Download className="size-3.5 opacity-60" />
                  )}
                </span>
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-xs text-muted-foreground">
        {t('model.help')}
        {selected && !selected.downloaded && (
          <>
            {' · '}
            <span className="text-warning-fg">
              {t('model.download', { size: selected.size_label })}
            </span>
          </>
        )}
      </p>
    </div>
  )
}
