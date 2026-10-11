import { useState } from 'react'
import { Copy } from 'lucide-react'
import { useApp } from '../../ctx'
import { Button, Card, Field, Input, toast } from '../ds'

/** About page: copyable iframe snippet for the #widget route. */
export default function EmbedSnippet() {
  const { t, lang } = useApp()
  const [lat, setLat] = useState('29.7604'), [lon, setLon] = useState('-95.3698')
  const ok = Number.isFinite(+lat) && Number.isFinite(+lon) && lat.trim() !== '' && lon.trim() !== '' && Math.abs(+lat) <= 90 && Math.abs(+lon) <= 180
  const src = `${location.origin}/widget?lat=${ok ? +lat : ''}&lon=${ok ? +lon : ''}&lang=${lang}`
  const code = `<iframe src="${src}" width="360" height="300" loading="lazy" style="border:0" title="${t('p15.w.title')}"></iframe>`
  return (
    <Card title={t('p15.embed.title')} subtitle={t('p15.embed.body')}>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label={t('p15.embed.lat')}><Input inputMode="decimal" value={lat} onChange={(e) => setLat(e.target.value)} /></Field>
        <Field label={t('p15.embed.lon')}><Input inputMode="decimal" value={lon} onChange={(e) => setLon(e.target.value)} /></Field>
      </div>
      <textarea readOnly rows={4} value={ok ? code : ''} aria-label={t('p15.embed.copy')} onFocus={(e) => e.currentTarget.select()}
        className="mt-3 w-full break-all rounded-sm border border-ui bg-surface-2 p-2 font-mono text-caption text-ink" dir="ltr" />
      <Button className="mt-2" icon={Copy} disabled={!ok} onClick={async () => { try { await navigator.clipboard.writeText(code); toast(t('p15.embed.copied')) } catch { /* select manually */ } }}>{t('p15.embed.copy')}</Button>
      <p className="mt-2 text-caption text-muted">{t('p15.embed.note')}</p>
    </Card>
  )
}
