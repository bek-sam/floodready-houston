import { useCallback, useEffect, useRef, useState } from 'react'
import { Camera, Download, ImagePlus, Trash2 } from 'lucide-react'
import { useApp } from '../../ctx'
import { Button, Card, SourceLink } from '../ds'
import { addPhoto, clearPhotos, deletePhoto, listPhotos, shrink, toDataUrl, updatePhoto, type ClaimPhoto } from './db'

const ROOMS = ['living', 'kitchen', 'bedroom', 'bath', 'garage', 'vehicle', 'other']
const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!))

function Thumb({ p, onChange, onDelete }: { p: ClaimPhoto; onChange: (p: ClaimPhoto) => void; onDelete: () => void }) {
  const { t } = useApp()
  const [url, setUrl] = useState('')
  useEffect(() => { const u = URL.createObjectURL(p.blob); setUrl(u); return () => URL.revokeObjectURL(u) }, [p.blob])
  return (
    <li className="flex gap-3 py-3">
      {url && <img src={url} alt={t(`p11b.room.${p.room}`)} className="h-20 w-20 shrink-0 rounded-md object-cover" />}
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-caption text-muted">{new Date(p.ts).toLocaleString()}</p>
        <select aria-label={t('p11b.cl.room')} value={p.room} onChange={(e) => onChange({ ...p, room: e.target.value })}
          className="min-h-11 w-full rounded-md border border-ui bg-surface px-2 text-body-sm text-ink">
          {ROOMS.map((r) => <option key={r} value={r}>{t(`p11b.room.${r}`)}</option>)}
        </select>
        <input aria-label={t('p11b.cl.note')} placeholder={t('p11b.cl.note')} defaultValue={p.note} maxLength={300}
          onBlur={(e) => e.target.value !== p.note && onChange({ ...p, note: e.target.value })}
          className="min-h-11 w-full rounded-md border border-ui bg-surface px-2 text-body-sm text-ink" />
      </div>
      <button type="button" onClick={onDelete} aria-label={t('p11b.cl.remove')} className="grid min-h-11 min-w-11 place-items-center text-muted hover:text-danger"><Trash2 aria-hidden size={18} /></button>
    </li>
  )
}

export default function ClaimsHelper() {
  const { t } = useApp()
  const [photos, setPhotos] = useState<ClaimPhoto[]>([])
  const [room, setRoom] = useState('living')
  const [err, setErr] = useState(false)
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const cam = useRef<HTMLInputElement>(null), up = useRef<HTMLInputElement>(null)

  const reload = useCallback(async () => { try { setPhotos(await listPhotos()); setErr(false) } catch { setErr(true) } }, [])
  useEffect(() => { void reload() }, [reload])

  const onFiles = async (files: FileList | null) => {
    if (!files?.length) return
    setBusy(true)
    try {
      for (const f of Array.from(files)) await addPhoto({ blob: await shrink(f, 1600), ts: Date.now(), room, note: '' })
      setErr(false)
    } catch { setErr(true) }
    await reload(); setBusy(false)
    if (cam.current) cam.current.value = ''
    if (up.current) up.current.value = ''
  }
  const change = async (p: ClaimPhoto) => { try { await updatePhoto(p) } catch { setErr(true) } await reload() }
  const remove = async (id?: number) => { if (id == null) return; try { await deletePhoto(id) } catch { setErr(true) } await reload() }
  const wipe = async () => { try { await clearPhotos() } catch { setErr(true) } setConfirm(false); await reload() }

  const exportHtml = async () => {
    setBusy(true)
    const rows = await Promise.all(photos.map(async (p) => ({ p, src: await toDataUrl(await shrink(p.blob, 640, 0.7)) })))
    const byRoom = ROOMS.map((r) => ({ r, n: photos.filter((p) => p.room === r).length })).filter((x) => x.n)
    const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(t('p11b.cl.rtitle'))}</title>
<style>body{font:16px/1.5 system-ui;max-width:860px;margin:2rem auto;padding:0 1rem;color:#111}figure{display:inline-block;width:260px;margin:.5rem;vertical-align:top}img{width:100%;border-radius:6px}figcaption{font-size:13px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ccc;padding:4px 8px;text-align:left;font-size:14px}</style></head><body>
<h1>${esc(t('p11b.cl.rtitle'))}</h1><p>${esc(t('p11b.cl.rgen'))} ${esc(new Date().toLocaleString())}. ${esc(t('p11b.cl.rcount').replace('{n}', String(photos.length)))}</p>
<h2>${esc(t('p11b.cl.rsum'))}</h2><ul>${byRoom.map((x) => `<li>${esc(t(`p11b.room.${x.r}`))}: ${x.n}</li>`).join('')}</ul>
<h2>${esc(t('p11b.cl.rphotos'))}</h2>${rows.map(({ p, src }) => `<figure><img src="${src}" alt=""><figcaption><b>${esc(t(`p11b.room.${p.room}`))}</b><br>${esc(new Date(p.ts).toLocaleString())}${p.note ? '<br>' + esc(p.note) : ''}</figcaption></figure>`).join('')}
<h2>${esc(t('p11b.cl.rtimes'))}</h2><table><tr><th>#</th><th>${esc(t('p11b.cl.room'))}</th><th>${esc(t('p11b.cl.rtime'))}</th><th>${esc(t('p11b.cl.note'))}</th></tr>${photos.map((p, i) => `<tr><td>${i + 1}</td><td>${esc(t(`p11b.room.${p.room}`))}</td><td>${esc(new Date(p.ts).toISOString())}</td><td>${esc(p.note)}</td></tr>`).join('')}</table>
<h2>${esc(t('p11b.cl.rpolicy'))}</h2><p>${esc(t('p11b.cl.rpolicyb'))}</p></body></html>`
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([html], { type: 'text/html' }))
    a.download = `flood-damage-report-${new Date().toISOString().slice(0, 10)}.html`
    document.body.appendChild(a); a.click(); a.remove()
    setTimeout(() => URL.revokeObjectURL(a.href), 4000)
    setBusy(false)
  }

  return (
    <Card title={t('p11b.cl.title')} subtitle={t('p11b.cl.sub')} titleAs="h2">
      <ul className="mb-3 list-disc space-y-1 ps-5 text-body-sm text-ink">
        <li>{t('p11b.cl.g1')}</li><li>{t('p11b.cl.g2')}</li><li>{t('p11b.cl.g3')}</li>
      </ul>
      <div className="mb-3 flex flex-wrap gap-x-4">
        <SourceLink href="https://www.disasterassistance.gov" label="DisasterAssistance.gov" />
        <SourceLink href="https://www.floodsmart.gov/get-insured/buy-a-policy" label="FloodSmart.gov" />
      </div>
      <p className="mb-1 text-body-sm font-semibold text-ink">{t('p11b.cl.checklist')}</p>
      <div className="mb-3 flex flex-wrap gap-2">
        {ROOMS.map((r) => {
          const n = photos.filter((p) => p.room === r).length
          return (
            <button key={r} type="button" aria-pressed={room === r} onClick={() => setRoom(r)}
              className={`min-h-11 rounded-full border px-3 text-body-sm ${room === r ? 'border-brand bg-brand-tint font-semibold text-ink' : 'border-line text-muted'}`}>
              {n > 0 ? '✓ ' : ''}{t(`p11b.room.${r}`)}{n > 0 ? ` (${n})` : ''}
            </button>
          )
        })}
      </div>
      <p className="mb-2 text-caption text-muted">{t('p11b.cl.addingTo').replace('{room}', t(`p11b.room.${room}`))}</p>
      <div className="flex flex-wrap gap-2">
        <input ref={cam} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => void onFiles(e.target.files)} />
        <input ref={up} type="file" accept="image/*" multiple className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => void onFiles(e.target.files)} />
        <Button icon={Camera} loading={busy} onClick={() => cam.current?.click()}>{t('p11b.cl.take')}</Button>
        <Button variant="secondary" icon={ImagePlus} disabled={busy} onClick={() => up.current?.click()}>{t('p11b.cl.upload')}</Button>
      </div>
      {err && <p role="alert" className="mt-3 text-body-sm text-danger">{t('p11b.cl.err')}</p>}
      {photos.length > 0 && <ul className="mt-3 divide-y divide-line">{photos.map((p) => <Thumb key={p.id} p={p} onChange={change} onDelete={() => void remove(p.id)} />)}</ul>}
      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="secondary" icon={Download} disabled={!photos.length || busy} onClick={() => void exportHtml()}>{t('p11b.cl.export')}</Button>
        {photos.length > 0 && !confirm && <Button variant="ghost" icon={Trash2} onClick={() => setConfirm(true)}>{t('p11b.cl.deleteAll')}</Button>}
      </div>
      {confirm && (
        <div role="alertdialog" aria-label={t('p11b.cl.deleteAll')} className="mt-3 rounded-md border border-danger/40 p-3 text-body-sm">
          <p className="mb-2 text-ink">{t('p11b.cl.confirm')}</p>
          <div className="flex gap-2"><Button variant="danger" onClick={() => void wipe()}>{t('p11b.cl.yes')}</Button><Button variant="secondary" onClick={() => setConfirm(false)}>{t('p11b.cl.cancel')}</Button></div>
        </div>
      )}
      <p className="mt-3 text-caption text-muted">{t('p11b.cl.privacy')}</p>
    </Card>
  )
}
