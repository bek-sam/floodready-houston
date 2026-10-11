import { Mic, SendHorizontal } from 'lucide-react'
import { useApp } from '../../ctx'
import { IconButton, Input } from '../ds'

/** Sticky message composer: input + dictation mic + send. Counter shows after 400 of 500 characters. */
export function Composer({ value, onChange, onSend, busy, micSupported, micActive, micDisabled, onMic }: {
  value: string; onChange: (v: string) => void; onSend: () => void; busy: boolean
  micSupported: boolean; micActive: boolean; micDisabled: boolean; onMic: () => void
}) {
  const { t } = useApp()
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSend() }} className="sticky bottom-20 z-10 bg-bg py-2 md:bottom-0">
      {value.length > 400 && <p className="mb-1 text-end text-caption text-muted" aria-live="polite">{t('p4.count').replace('{n}', String(value.length))}</p>}
      <div className="flex items-center gap-2">
        <label htmlFor="q" className="sr-only">{t('ask.placeholder')}</label>
        <Input id="q" value={value} maxLength={500} onChange={(e) => onChange(e.target.value)} placeholder={t('ask.placeholder')} className="min-h-12 flex-1" />
        {micSupported && <IconButton icon={Mic} variant="secondary" label={t('p4.mic')} aria-pressed={micActive} disabled={micDisabled} onClick={onMic} className={micActive ? 'border-brand text-brand' : ''} />}
        <IconButton icon={SendHorizontal} label={t('p4.send')} disabled={busy || !value.trim()} onClick={onSend} type="submit" className="bg-brand text-brandink hover:bg-brand-strong" />
      </div>
    </form>
  )
}
