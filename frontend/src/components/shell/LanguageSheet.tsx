import { Check } from 'lucide-react'
import { useApp } from '../../ctx'
import { LANGS } from '../../i18n'
import { Sheet } from '../ds'

export function LanguageSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t, lang, setLang } = useApp()
  return (
    <Sheet open={open} onClose={onClose} title={t('language')}>
      <LanguageList value={lang} onChange={(c) => { setLang(c); onClose() }} />
    </Sheet>
  )
}

/** Radio list of languages, each label in its own language. */
export function LanguageList({ value, onChange, large = false }: { value: string; onChange: (code: string) => void; large?: boolean }) {
  const { t } = useApp()
  return (
    <div role="radiogroup" aria-label={t('language')} className="space-y-2">
      {LANGS.map((l) => {
        const sel = l.code === value
        return (
          <button key={l.code} type="button" role="radio" aria-checked={sel} lang={l.code} onClick={() => onChange(l.code)}
            className={`flex w-full items-center justify-between rounded-md border px-4 text-start text-base font-medium ${large ? 'min-h-14' : 'min-h-12'} ${sel ? 'border-2 border-brand bg-brand-tint text-ink' : 'border-line bg-surface text-ink hover:bg-surface-2'}`}>
            {l.label}
            {sel && <Check aria-hidden size={20} className="text-brand" />}
          </button>
        )
      })}
    </div>
  )
}
