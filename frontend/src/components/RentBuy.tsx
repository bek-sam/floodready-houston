import { api, type BuyoutArea, type ZipInsurance } from '../api'
import { useApp } from '../ctx'
import { useBk } from '../lib/bk'
import { Button, ErrorBox, LoadingText, SkeletonText, SourceLink } from './ds'
import { useAsync } from './ui'
import { useEffect, useState } from 'react'
import { BuyoutContact } from './p35/P35'

function TenantRights({ open }: { open: boolean }) {
  const { t } = useApp()
  const [copied, setCopied] = useState(false)
  const letter = t('p28.ten.l')
  const copy = async () => { try { await navigator.clipboard.writeText(letter); setCopied(true); setTimeout(() => setCopied(false), 2000) } catch { /* ignore */ } }
  return (
    <details className="rounded-md bg-surface-2 p-4" open={open}>
      <summary className="cursor-pointer text-h3">{open ? t('p28.ten.h') : t('p28.ten.sum')}</summary>
      <p className="mt-2">{t('p28.ten.body')}</p>
      <p className="mt-1">{t('p28.ten.keep')}</p>
      <p className="mt-2 font-semibold">{t('p28.ten.letter')}</p>
      <pre className="mt-1 whitespace-pre-wrap rounded-md border border-line p-3 text-caption">{letter}</pre>
      <button type="button" onClick={copy} className="mt-2 rounded-md border border-line px-3 py-1.5 text-body-sm font-semibold" aria-live="polite">{copied ? t('p28.ten.copied') : t('p28.ten.copy')}</button>
      <p className="mt-2"><SourceLink href="https://www.ecfr.gov/current/title-49/subtitle-A/part-24" label={t('p28.ten.ecfr')} /> <SourceLink href="https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/" label={t('p28.ten.county')} /></p>
    </details>
  )
}

function ClaimsBars({ rows, title }: { rows: { year: number; count: number }[]; title: string }) {
  const { t, lang } = useApp()
  const nf = (n: number) => n.toLocaleString(lang)
  const max = Math.max(1, ...rows.map((r) => r.count))
  const W = 300, H = 90, base = 72, gap = 2
  const bw = Math.max(4, (W - gap * (rows.length - 1)) / Math.max(1, rows.length))
  return (
    <figure className="mt-3">
      <figcaption className="text-body-sm font-semibold text-ink">{title} <span className="font-normal text-muted">({rows[0]?.year}–{rows[rows.length - 1]?.year})</span></figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-1 w-full max-w-md" role="img" aria-label={title}>
        <line x1="0" x2={W} y1={base} y2={base} stroke="var(--line)" strokeWidth="1" />
        {rows.map((r, i) => {
          const h = Math.max(r.count > 0 ? 2 : 0, (r.count / max) * (base - 14))
          const x = i * (bw + gap)
          return (
            <g key={r.year}>
              <rect x={x} y={base - h} width={bw} height={h} rx={Math.min(2, bw / 2)} fill="var(--water)">
                <title>{r.year}: {nf(r.count)}</title>
              </rect>
              {r.count === max && (
                <text x={Math.min(Math.max(x + bw / 2, 12), W - 12)} y={base - h - 3} textAnchor="middle" fontSize="10" fontWeight="600" fill="var(--ink)">{r.year}: {nf(r.count)}</text>
              )}
              {(i === 0 || i === rows.length - 1) && (
                <text x={x + bw / 2} y={base + 12} textAnchor={i === 0 ? 'start' : 'end'} fontSize="10" fill="var(--muted)" dx={i === 0 ? -bw / 2 : bw / 2}>{r.year}</text>
              )}
            </g>
          )
        })}
      </svg>
      <details className="text-caption text-muted">
        <summary className="flex min-h-11 cursor-pointer items-center font-semibold text-brand">{t('c5.table')}</summary>
        <div className="max-h-48 overflow-auto"><table className="mt-1 tabular-nums"><tbody>{rows.map((r) => <tr key={r.year}><td className="pe-3">{r.year}</td><td className="text-end">{nf(r.count)}</td></tr>)}</tbody></table></div>
      </details>
    </figure>
  )
}

export default function RentBuy({ label, zone, sfha, lat, lon }: { label: string; zone?: string | null; sfha?: boolean | null; lat?: number; lon?: number }) {
  const { t, lang } = useApp()
  const bk = useBk()
  const nf = (n: number) => n.toLocaleString(lang)
  const labelZip = label.match(/,\s*[A-Za-z]{2}\s+(\d{5})(?:-\d{4})?\s*(?:,?\s*(?:USA|US))?\s*$/)?.[1] ?? label.match(/\b(\d{5})(?:-\d{4})?\s*$/)?.[1] ?? null
  const [manual, setManual] = useState<string>(() => { try { return localStorage.getItem('zip:' + lat?.toFixed(3) + ',' + lon?.toFixed(3)) ?? '' } catch { return '' } })
  const [rev, setRev] = useState<string | null>(null)
  useEffect(() => { try { setManual(localStorage.getItem('zip:' + lat?.toFixed(3) + ',' + lon?.toFixed(3)) ?? '') } catch { setManual('') } }, [lat, lon])
  useEffect(() => {
    setRev(null)
    if (labelZip || manual || lat == null || lon == null) return
    let live = true
    fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&zoom=18&lat=${lat}&lon=${lon}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => { const z = String(j?.address?.postcode ?? '').match(/^\d{5}/)?.[0]; if (live && z) setRev(z) })
      .catch(() => { /* fall back to the ZIP input */ })
    return () => { live = false }
  }, [labelZip, manual, lat, lon])
  const zip = labelZip ?? (/^\d{5}$/.test(manual) ? manual : null) ?? rev
  const [draft, setDraft] = useState('')
  const [bad, setBad] = useState(false)
  const saveZip = () => {
    if (!/^\d{5}$/.test(draft.trim())) { setBad(true); return }
    setBad(false); setManual(draft.trim())
    try { localStorage.setItem('zip:' + lat?.toFixed(3) + ',' + lon?.toFixed(3), draft.trim()) } catch { /* ignore */ }
  }
  const ins = useAsync<ZipInsurance>(() => api.zipInsurance(zip!), [zip], !!zip)
  const d = ins.data
  const hasLoc = lat != null && lon != null
  const buy = useAsync<BuyoutArea>(() => api.buyoutArea({ lat: lat!, lon: lon! }), [lat, lon], hasLoc)
  const b = buy.data
  const pr = d?.premiums
  const usd = (n?: number | null) => (n == null ? '—' : '$' + Math.round(n).toLocaleString(lang))
  const showDecision = !!d && (!!zone || !!pr || sfha != null)
  const total = d?.claims?.total ?? 0, since = d?.claims?.since_2017 ?? 0
  const rows = (Array.isArray(d?.claims?.by_year) ? d!.claims.by_year : []).filter((r) => r && typeof r.year === 'number').slice().sort((a, b) => a.year - b.year)
  return (
    <div className="space-y-3 text-body-sm text-ink">
      {!zip && (
        <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); saveZip() }}>
          <p className="text-muted">{t('p39.zip.help')}</p>
          <label className="block font-semibold" htmlFor="rb-zip">{t('p39.zip.label')}</label>
          <div className="flex gap-2">
            <input id="rb-zip" inputMode="numeric" pattern="\d{5}" maxLength={5} autoComplete="postal-code" value={draft} onChange={(e) => setDraft(e.target.value)}
              className="min-h-11 w-28 rounded-md border border-line bg-surface px-3 text-ink" aria-invalid={bad || undefined} />
            <Button type="submit" variant="secondary">{t('p39.zip.go')}</Button>
          </div>
          {bad && <p className="text-danger" role="alert">{t('p39.zip.bad')}</p>}
        </form>
      )}
      {ins.loading && <div aria-busy="true"><LoadingText /><SkeletonText lines={3} /></div>}
      {ins.error && <ErrorBox error={t('c5.rb.unavail')} onRetry={ins.reload} />}
      {d && (
        <>
          <p className="font-semibold">{t('c5.rb.claims').replace('{zip}', String(d.zip ?? zip ?? '')).replace('{n}', nf(total)).replace('{m}', nf(since))}</p>
          {typeof d.policies_in_force === 'number' && <p>{t('c5.rb.policies').replace('{n}', nf(d.policies_in_force))}</p>}
          {rows.length > 0 && <ClaimsBars rows={rows} title={t('c5.rb.byYear')} />}
          {(Array.isArray(d.warnings) ? d.warnings : []).map((w, i) => <p key={i} className="text-caption text-muted">{bk(d.warning_codes?.[i], {}, w)}</p>)}
          <p className="text-caption text-muted">{bk(d.note_code, {}, d.note)}{d.source && <SourceLink href={d.source} label="OpenFEMA NFIP" />}</p>
        </>
      )}
      {b && b.in_buyout_area === false && <p className="text-muted">{t('c11.buyout.out')}</p>}
      {b && b.in_buyout_area === true && (
        <p className="rounded-md bg-watch-tint px-3 py-2 font-semibold" role="status">
          {t('c11.buyout.in').replace('{name}', b.area_name ?? '')} {b.note && <span className="font-normal text-muted">{bk(b.note_code, b.params, b.note)}</span>}
          <SourceLink href={b.source} />
        </p>
      )}
      {hasLoc && <BuyoutContact />}
      <TenantRights open={b?.in_buyout_area === true} />
      {showDecision && (
        <div className="rounded-md bg-surface-2 p-4" role="note">
          <p className="text-h3">{t('c11.ins.title')}</p>
          <ul className="mt-1 list-disc space-y-1 ps-5">
            {zone && <li>{t('c11.ins.zone').replace('{zone}', zone)}{sfha ? ' ' + t('c11.ins.sfha') : ''}</li>}
            {d && !sfha && !!zone && since > 0 && <li className="font-semibold">{t('c11.ins.lowrisk').replace('{n}', nf(since))}</li>}
            {d && <li>{t('c11.ins.claims').replace('{zip}', String(d.zip ?? zip ?? '')).replace('{n}', nf(since))}</li>}
            {pr && pr.median_annual != null && (
              <li>{t('c11.ins.prem').replace('{med}', usd(pr.median_annual)).replace('{lo}', usd(pr.p25)).replace('{hi}', usd(pr.p75))}
                {pr.sample_size ? ' ' + t('c11.ins.sample').replace('{n}', nf(pr.sample_size)) : ''}</li>
            )}
            <li>{t('c5.rb.wait')}</li>
          </ul>
          <p className="mt-3 font-semibold">{t('c11.ins.verdict')}</p>
          {pr && <p className="mt-1 text-caption text-muted">{t('c11.ins.caveat')}{pr.as_of ? ` (${pr.as_of})` : ''}</p>}
          <SourceLink href={pr?.source || d?.source} label="OpenFEMA NFIP" />
        </div>
      )}
      <p className="text-h3">{t('c5.rb.ask')}</p>
      <ul className="list-disc space-y-1 ps-5">
        {['1', '2', '3', '4'].map((k) => <li key={k}>{t('c5.rb.q' + k)}</li>)}
        {['c3', 'c5'].map((k) => <li key={k}>{t('home.' + k)}</li>)}
      </ul>
      {!showDecision && <p role="note">{t('c5.rb.wait')}</p>}
    </div>
  )
}
