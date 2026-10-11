import { useMemo, useState } from 'react'
import { CircleMarker, Popup } from 'react-leaflet'
import { Home, Info, LifeBuoy, Megaphone, ChevronRight } from 'lucide-react'
import { api } from '../api'
import { HOUSTON, useApp } from '../ctx'
import { usePlace, placeName } from '../state/place'
import { cssVar } from '../lib/levels'
import { RecoveryTracker, Share911 } from '../components/RecoverExtras'
import { Map } from '../components/maps'
import Report311 from '../components/civic311/Report311'
import ClaimsHelper from '../components/claims/ClaimsHelper'
import ReportSheet from '../components/ReportSheet'
import { useAsync, Warnings } from '../components/ui'
import { Card, Checkbox, Disclosure, EmptyState, ErrorBox, PageHeader, SkeletonCard, SourceLink } from '../components/ds'

type Step = { id: string; src?: string; label?: string }
const KB = {
  ksat: 'https://www.ksat.com/news/texas/2024/05/20/the-government-wants-to-buy-their-flood-prone-homes-but-these-texans-arent-moving/',
  hcd: 'https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/Involuntary-Buyout-Relocation-Program',
  pro: 'https://projects.propublica.org/graphics/harvey-reservoirs',
  imelda: 'https://en.wikipedia.org/wiki/Tropical_Storm_Imelda_(2019)',
}
// Steps use only facts and links from data/knowledge/renters-and-buyouts.md and fema-aid-and-recovery.md.
const LISTS: { id: string; steps: Step[] }[] = [
  { id: 'aid', steps: [
    { id: 'a1' }, { id: 'a2' }, { id: 'a3' },
    { id: 'a4', src: KB.imelda, label: 'Wikipedia: Imelda' },
  ] },
  { id: 'buyout', steps: [
    { id: 'b1', src: KB.pro, label: 'ProPublica' },
    { id: 'b2' },
    { id: 'b3', src: KB.hcd, label: 'Harris County HCD' },
    { id: 'b4', src: KB.hcd, label: 'Harris County HCD' },
    { id: 'b5', src: KB.ksat, label: 'KSAT' },
    { id: 'b6', src: KB.ksat, label: 'KSAT' },
  ] },
]
const loadDone = (): Record<string, boolean> => { try { return JSON.parse(localStorage.getItem('recoverDone') || '{}') } catch { return {} } }

function Checklists() {
  const { t } = useApp()
  const [done, setDone] = useState<Record<string, boolean>>(loadDone)
  const toggle = (id: string, v: boolean) => {
    const n = { ...done, [id]: v }
    setDone(n)
    try { localStorage.setItem('recoverDone', JSON.stringify(n)) } catch { /* ignore */ }
  }
  return (
    <>
      {LISTS.map((l, li) => {
        const n = l.steps.filter((s) => done[s.id]).length
        return (
          <Disclosure key={l.id} title={t(`rec.list.${l.id}`)} defaultOpen={li === 0}
            preview={t('rec.done').replace('{n}', String(n)).replace('{m}', String(l.steps.length))}>
            <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden>
              <div className="h-full rounded-full bg-normal transition-all" style={{ width: `${(n / l.steps.length) * 100}%` }} />
            </div>
            <ol>
              {l.steps.map((s, i) => (
                <li key={s.id}>
                  <Checkbox checked={!!done[s.id]} onChange={(v) => toggle(s.id, v)}
                    label={<span className={done[s.id] ? 'text-muted line-through' : ''}>{i + 1}. {t(`rec.${s.id}`)}</span>} />
                  {s.src && <div className="ps-9"><SourceLink href={s.src} label={s.label} /></div>}
                </li>
              ))}
            </ol>
          </Disclosure>
        )
      })}
    </>
  )
}

// Historical 2017 data only. Never presented as a live list.
function Shelters({ loc, name, hasPlace }: { loc: { lat: number; lon: number }; name: string; hasPlace: boolean }) {
  const { t } = useApp()
  const [pet, setPet] = useState(false)
  const sh = useAsync(() => api.shelters({ lat: loc.lat, lon: loc.lon }, pet, 10), [loc.lat, loc.lon, pet])
  const d = sh.data
  return (
    <div className="space-y-3">
      <div role="status" className="flex items-start gap-3 rounded-md border border-watch/40 bg-watch-tint p-3 text-body-sm text-ink">
        <Info aria-hidden size={20} className="mt-0.5 shrink-0 text-watch" />
        <div>
          <p className="font-semibold">{t('p5.rec.shelterWarn')}</p>
          <p className="mt-1">{t('rec.historical').replace('{asof}', d?.data_as_of ? ` (${d.data_as_of})` : '')}</p>
        </div>
      </div>
      <p className="text-caption text-muted">{hasPlace ? t('p5.rec.shelterFrom').replace('{name}', name) : t('p5.rec.shelterDowntown')}</p>
      <Checkbox label={t('rec.petOnly')} checked={pet} onChange={setPet} />
      {sh.loading && <SkeletonCard lines={3} />}
      {sh.error != null && <ErrorBox error={t('rec.shelterDown')} onRetry={sh.reload} />}
      {d && (
        <>
          <Warnings items={d.warnings} />
          {(d.shelters ?? []).length === 0 && <p className="text-body-sm text-muted">{t('rec.noShelters')}</p>}
          <ul className="divide-y divide-line">
            {(d.shelters ?? []).map((s, i) => (
              <li key={i} className="py-3 text-body-sm">
                <p className="flex flex-wrap items-center gap-2 font-semibold text-ink">
                  {cleanName(s.name ?? '')}
                  {s.pet_friendly && <span className="rounded-full border border-line px-2 text-caption font-medium">{t('rec.petsOk')}</span>}
                </p>
                <p className="text-muted">{[cleanAddr(s.address), s.county, typeof s.distance_mi === 'number' ? `${s.distance_mi.toFixed(1)} mi` : ''].filter(Boolean).join(' · ')}</p>
                {s.status_2017 && <p className="text-caption text-muted">{t('rec.status2017')}: {s.status_2017}</p>}
              </li>
            ))}
          </ul>
          {d.source && <SourceLink href={d.source} />}
        </>
      )}
    </div>
  )
}

// Raw 2017 shelter data has typos: close unbalanced parentheses, fix known misspellings.
const cleanName = (n: string) => n + ')'.repeat(Math.max(0, (n.match(/\(/g) || []).length - (n.match(/\)/g) || []).length))
const cleanAddr = (a?: string | null) => (a ? a.replace('Avanida De Las Americans', 'Avenida de las Americas') : a)
const miBetween = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const R = 3958.8, rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad, dLon = (b.lon - a.lon) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

export default function Recover() {
  const { t } = useApp()
  const { place } = usePlace()
  const loc = place ?? { ...HOUSTON, label: 'Houston' }
  const name = place ? placeName(place.nickname, t) : 'Houston'
  const kindLabel = (k?: string) => { const key = 'c6.kind.' + k; const v = t(key); return v === key ? String(k ?? '').replace(/_/g, ' ') : v }
  const reports = useAsync(() => api.reports(), [])
  const [reportOpen, setReportOpen] = useState(false)
  const near = useMemo(() => {
    const day = Date.now() - 24 * 3600 * 1000
    return (Array.isArray(reports.data) ? reports.data : [])
      .filter((r) => r && Number.isFinite(r.lat) && Number.isFinite(r.lon) && miBetween(loc, r) <= 10
        && r.created_at && Date.parse(r.created_at) >= day)
      .sort((a, b) => Date.parse(b.created_at!) - Date.parse(a.created_at!)).slice(0, 5)
  }, [reports.data, loc.lat, loc.lon]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <PageHeader title={t('rec.title')} subtitle={t('p5.rec.sub')} forPlace />

      <Share911 />
      <RecoveryTracker />
      <Checklists />

      <button type="button" onClick={() => setReportOpen(true)} aria-haspopup="dialog"
        className="flex min-h-14 w-full items-center gap-3 rounded-lg border border-line bg-surface px-4 py-2 text-start shadow-card hover:bg-surface-2/60">
        <Megaphone aria-hidden size={20} className="shrink-0 text-brand" />
        <span className="min-w-0 flex-1">
          <span className="block text-h3 text-ink">{t('p5.rec.reportRow')}</span>
          <span className="block text-caption text-muted">{t('p5.rec.reportSub')}</span>
        </span>
        <ChevronRight aria-hidden size={20} className="text-muted rtl:rotate-180" />
      </button>
      <ReportSheet open={reportOpen} onClose={() => setReportOpen(false)} onSent={reports.reload} />

      <Card title={t('p5.rec.recent').replace('{name}', name)} subtitle={t('p5.rec.unverified')}>
        {reports.loading && <SkeletonCard lines={2} />}
        {reports.error && <ErrorBox error={reports.error} onRetry={reports.reload} />}
        {!reports.loading && !reports.error && near.length === 0 && (
          <EmptyState icon={LifeBuoy} title={t('p5.rec.noReports').replace('{name}', name)} />
        )}
        {near.length > 0 && (
          <ul className="divide-y divide-line text-body-sm">
            {near.map((r, i) => (
              <li key={r.id ?? i} className="py-2">
                <span className="font-semibold text-ink">{kindLabel(r.kind)}</span>{r.depth_in != null && ` · ${r.depth_in} ${t('c6.in')}`}{r.note && ` · ${r.note}`}
                {r.created_at && !isNaN(Date.parse(r.created_at)) && <span className="block text-caption text-muted">{new Date(r.created_at).toLocaleString()}</span>}
              </li>
            ))}
          </ul>
        )}
        {near.length > 0 && (
          <div className="mt-3">
            <Disclosure title={t('p5.rec.showMap')}>
              <Map label={t('p5.rec.reportsMap')} center={[loc.lat, loc.lon]} height="h-64">
                {near.map((r, i) => (
                  <CircleMarker key={r.id ?? i} center={[r.lat, r.lon]} radius={8} pathOptions={{ color: '#fff', weight: 2, fillColor: cssVar('--danger'), fillOpacity: 0.9 }}>
                    <Popup><b>{kindLabel(r.kind)}</b>{r.depth_in != null && ` · ${r.depth_in} ${t('c6.in')}`}<br />{r.note}</Popup>
                  </CircleMarker>
                ))}
              </Map>
            </Disclosure>
          </div>
        )}
      </Card>

      <Report311 />

      <ClaimsHelper />

      <Disclosure title={t('p5.rec.shelterTitle')} preview={t('p5.rec.shelterPreview')} icon={<Home size={20} />}>
        <Shelters loc={loc} name={name} hasPlace={!!place} />
      </Disclosure>
    </div>
  )
}
