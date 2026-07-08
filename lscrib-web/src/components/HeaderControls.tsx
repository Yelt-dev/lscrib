import { Languages, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useI18n } from '@/i18n'
import { useTheme } from '@/lib/theme'

export function ThemeToggle() {
  const { t } = useI18n()
  const { resolved, setTheme } = useTheme()
  const next = resolved === 'dark' ? 'light' : 'dark'
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={t('theme.toggle')}
      title={t('theme.toggle')}
      onClick={() => setTheme(next)}
    >
      {resolved === 'dark' ? <Moon className="size-4" /> : <Sun className="size-4" />}
    </Button>
  )
}

export function UiLangToggle() {
  const { lang, setLang, t } = useI18n()
  return (
    <Button
      variant="ghost"
      size="sm"
      aria-label={t('uilang.toggle')}
      title={t('uilang.toggle')}
      onClick={() => setLang(lang === 'es' ? 'en' : 'es')}
      className="gap-1.5"
    >
      <Languages className="size-4" />
      <span className="uppercase">{lang}</span>
    </Button>
  )
}
