import { useApp } from '../../ctx'
import { SourceLink } from '../ds'
import { zoneState } from '../evac/EvacSurgeCard'
import type { Col } from './useCompare'

const SRC = {
  fema: 'https://msc.fema.gov/portal/home',
  harvey: 'https://www.fema.gov/disaster/4332',
  evac: 'https://www.houstonoem.org/know-your-zone/',
  gauge: 'https://waterdata.usgs.gov/nwis',
  claims: 'https://www.fema.gov/openfema-data-page/fima-nfip-redacted-claims-v2',
  prem: 'https://www.fema.gov/openfema-data-page/fima-nfip-redacted-policies-v2',
  cross: 'https://www.harriscountyfws.org/',
}
export interface Named { name: string; col: Col | null; err?: boolean }

export default function CompareTable({ cols }: { cols: Named[] }) {
  const { t } = useApp()
  const na = t('p13.cmp.na')
  const rows: { key: string; src: string; cell: (c: Col) => string }[] = [
    { key: 'fema', src: SRC.fema, cell: (c) => c.risk?.fema_zone ? c.risk.fema_zone + (c.risk.sfha ? ' · ' + t('p13.cmp.sfha') : '') : na },
    { key: 'harvey', src: SRC.harvey, cell: (c) => { const h = c.risk?.harvey?.flooded ?? c.hist?.harvey?.flooded; return h == null ? na : h ? t('p13.cmp.yes') : t('p13.cmp.no') } },
    { key: 'evac', src: SRC.evac, cell: (c) => { if (!c.evac) return na; const s = zoneState(c.evac); return s === 'unavailable' ? na : s === 'in' ? t('p13.cmp.zone').replace('{z}', c.evac.zone ?? '?') : t('p13.cmp.noZone') } },
    { key: 'gauge', src: SRC.gauge, cell: (c) => { const g = c.hist?.events.find((e) => /harvey/i.test(e.name))?.nearest_gauge; return g?.peak_ft != null ? `${g.peak_ft} ft · ${g.name}` : na } },
    { key: 'claims', src: SRC.claims, cell: (c) => c.zip ? `${c.zip.claims.total.toLocaleString()} (${c.zip.zip})` : na },
    { key: 'prem', src: SRC.prem, cell: (c) => { const m = c.zip?.premiums?.median_annual; return m != null ? '$' + Math.round(m).toLocaleString() + '/yr' : na } },
    { key: 'cross', src: SRC.cross, cell: (c) => c.crossings == null ? na : String(c.crossings) },
  ]
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] border-collapse text-body-sm">
        <caption className="sr-only">{t('p13.cmp.title')}</caption>
        <thead><tr><th scope="col" className="p-2 text-start text-muted">{t('p13.cmp.metric')}</th>
          {cols.map((c, i) => <th key={i} scope="col" className="p-2 text-start font-semibold text-ink">{c.name}</th>)}</tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} className="border-t border-line align-top">
              <th scope="row" className="p-2 text-start font-medium text-ink">{t('p13.cmp.r.' + r.key)}<SourceLink href={r.src} /></th>
              {cols.map((c, i) => <td key={i} className="p-2 text-ink">{c.col ? r.cell(c.col) : c.err ? na : '…'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
