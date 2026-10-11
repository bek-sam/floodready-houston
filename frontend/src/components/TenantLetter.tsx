import { useState } from 'react'
import { useApp } from '../ctx'
import { Button, Card, Checkbox, Field, Input, Select } from './ds'
import { Copy, Download, Printer } from 'lucide-react'
import template from '../../../data/tenant_letter_template.md?raw'

const todayStr = () => new Date().toISOString().slice(0, 10)

// Split the template file into letters by "## Template" headings; drop the disclaimer header and trailing tips.
function splitLetters(tpl: string): string[] {
  return tpl.split(/^##\s+Template\s+\w+:.*$/m).slice(1).map((x) => x.split(/^Tips:/m)[0].trim())
}

function fill(tpl: string, v: Record<string, string>, noNotice: boolean): string {
  let out = tpl.replace(/ ?\[fill in only if true\]/g, '')
  if (!noNotice) out = out.replace(/ ?I did not receive the flood notices[^.]*\./, '')
  const map: Record<string, string> = {
    landlord_name: v.landlord, address: v.address, name: v.name, date: v.date,
    phone: v.phone, flood_date: v.floodDate, move_out_date: v.moveOut,
  }
  out = out.replace(/\{\s*(\w+)\s*\}/g, (_m, k) => (map[k] ? map[k] : '________'))
  // Drop lines that are only an unfilled phone placeholder
  return out.split('\n').filter((l) => l.trim() !== '{phone}').join('\n')
}

export default function TenantLetter() {
  const { t, place } = useApp()
  const [v, setV] = useState({ landlord: '', address: place?.label ?? '', name: '', date: todayStr(), phone: '', floodDate: '', moveOut: '' })
  const [pick, setPick] = useState(0)
  const [noNotice, setNoNotice] = useState(false)
  const [copied, setCopied] = useState(false)
  const [err, setErr] = useState(false)
  const letters = typeof template === 'string' ? splitLetters(template) : []
  const body = letters.length ? fill(letters[Math.min(pick, letters.length - 1)], v, noNotice) : ''
  const isB = pick === 1
  const ready = !!(v.landlord.trim() && v.name.trim() && v.address.trim())
  const set = (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) => { setCopied(false); setV({ ...v, [k]: e.target.value }) }
  const copy = async () => {
    setErr(false)
    try { await navigator.clipboard.writeText(body); setCopied(true) } catch { setErr(true) }
  }
  const download = () => {
    const url = URL.createObjectURL(new Blob([body], { type: 'text/plain' }))
    const a = document.createElement('a'); a.href = url; a.download = 'flood-letter.txt'; a.click(); URL.revokeObjectURL(url)
  }
  return (
    <Card id="tenant-letter" title={t('c11.tl.title')}>
      <p className="text-body-sm text-muted">{t('c11.tl.intro')}</p>
      {!body ? <p className="mt-2 text-body-sm text-muted">{t('c11.tl.unavail')}</p> : (
        <>
          <Field label={t('c11.tl.pick')}>
            <Select value={pick} onChange={(e) => { setCopied(false); setPick(Number(e.target.value)) }}>
              <option value={0}>{t('c11.tl.a')}</option>
              {letters.length > 1 && <option value={1}>{t('c11.tl.b')}</option>}
            </Select>
          </Field>
          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            <Field label={t('c11.tl.landlord')}><Input  value={v.landlord} onChange={set('landlord')} /></Field>
            <Field label={t('c11.tl.name')}><Input  value={v.name} onChange={set('name')} /></Field>
            <Field label={t('c11.tl.address')}><Input  value={v.address} onChange={set('address')} /></Field>
            <Field label={t('c11.tl.date')}><Input type="date"  value={v.date} onChange={set('date')} /></Field>
            <Field label={t('c11.tl.phone')}><Input  value={v.phone} onChange={set('phone')} /></Field>
            {isB && <Field label={t('c11.tl.floodDate')}><Input type="date"  value={v.floodDate} onChange={set('floodDate')} /></Field>}
            {isB && <Field label={t('c11.tl.moveOut')}><Input type="date"  value={v.moveOut} onChange={set('moveOut')} /></Field>}
          </div>
          {isB && <Checkbox className="mt-2" label={t('c11.tl.noNotice')} checked={noNotice} onChange={setNoNotice} />}
          <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border border-line bg-surface-2 p-3 text-body-sm">{body}</pre>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button variant="secondary" icon={Copy} onClick={copy} disabled={!ready}>{copied ? t('c11.tl.copied') : t('c11.tl.copy')}</Button>
            <Button variant="secondary" icon={Download} onClick={download}>{t('c11.tl.download')}</Button>
            <Button variant="secondary" icon={Printer} onClick={() => window.print()}>{t('c11.tl.print')}</Button>
          </div>
          {!ready && <p className="mt-1 text-body-sm text-muted">{t('c11.tl.fillBlanks')}</p>}
          {err && <p className="mt-1 text-body-sm text-danger" role="alert">{t('c11.tl.copyFail')}</p>}
        </>
      )}
    </Card>
  )
}
