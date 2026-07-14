import { Cpu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useI18n } from '@/i18n'
import type { CpuInfo } from '@/types'

/** El motor de transcripción (NumPy + CTranslate2) necesita SSE4.2. En una CPU
 *  anterior el backend moriría con SIGILL sin decir nada: aquí se explica que el
 *  problema es el hardware de esta máquina, no el archivo del usuario. */
export function CpuUnsupportedDialog({
  cpu,
  open,
  onOpenChange,
}: {
  cpu: CpuInfo
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { t } = useI18n()
  const missing = cpu.missing.map((f) => f.toUpperCase().replace('_', '.')).join(', ')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="mb-1 flex size-9 items-center justify-center rounded-full bg-danger/10">
            <Cpu className="size-5 text-danger-fg" />
          </div>
          <DialogTitle>{t('cpu.title')}</DialogTitle>
          <DialogDescription>
            {t('cpu.body', {
              model: cpu.cpu_model || t('cpu.unknownModel'),
              missing,
            })}
          </DialogDescription>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{t('cpu.hint')}</p>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>{t('common.gotIt')}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
