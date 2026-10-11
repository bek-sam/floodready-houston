import { Phone } from 'lucide-react'
import { useApp } from '../../ctx'
import { Card, SourceLink } from '../ds'

const R = 'https://www.readyhoustontx.gov/?p=600'
const CP = 'https://www.centerpointenergy.com/en-us/residential/services/electric-utility/outage-center'
const M = 'https://www.ridemetro.org'

function Call({ n, label }: { n: string; label: string }) {
  return (
    <a href={`tel:${n.replace(/-/g, '')}`} className="flex min-h-11 items-center gap-3 rounded-md border border-ui bg-surface px-3 py-2 text-body-sm font-semibold text-ink">
      <Phone aria-hidden size={18} className="shrink-0" />{label}
    </a>
  )
}
function Links({ items }: { items: [string, string][] }) {
  const { t } = useApp()
  return <p className="flex flex-wrap gap-x-4 gap-y-1 text-body-sm">{items.map(([href, k]) => <SourceLink key={href} href={href} label={t(k)} />)}</p>
}

/** Cycle 38: four link-out cards for when power or data is down. No live data. */
export default function StayInformed() {
  const { t } = useApp()
  return (
    <section className="space-y-3" aria-labelledby="p38-title">
      <div>
        <h2 id="p38-title" className="text-h3 font-semibold text-ink">{t('p38.title')}</h2>
        <p className="text-body-sm text-muted">{t('p38.intro')}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Card title={t('p38.a.t')} titleAs="h3">
          <div className="space-y-2">
            <p className="text-body-sm text-ink">{t('p38.a.reg')}</p>
            <p className="text-body-sm text-ink">{t('p38.a.radio')}</p>
            <Links items={[['https://houstonoem.org/', 'p38.a.l1'], [R, 'p38.a.l2']]} />
          </div>
        </Card>
        <Card title={t('p38.p.t')} titleAs="h3">
          <div className="space-y-2">
            <p className="text-body-sm text-ink">{t('p38.p.body')}</p>
            <Call n="713-207-2222" label={t('p38.p.call')} />
            <Links items={[['https://tracker.centerpointenergy.com/map/texas', 'p38.p.l1'], [CP, 'p38.p.l2']]} />
          </div>
        </Card>
        <Card title={t('p38.m.t')} titleAs="h3">
          <div className="space-y-2">
            <p className="text-body-sm text-ink">{t('p38.m.body')}</p>
            <Call n="713-635-4000" label={t('p38.m.call')} />
            <Links items={[
              [`${M}/alerts/service-alerts-and-detours`, 'p38.m.l1'],
              [`${M}/alerts/text-and-email-alerts-newsletters`, 'p38.m.l2'],
              [`${M}/riding-metro/transit-services/metrolift-paratransit`, 'p38.m.l3']]} />
          </div>
        </Card>
        <Card title={t('p38.w.t')} titleAs="h3">
          <div className="space-y-2">
            <p className="text-body-sm text-ink">{t('p38.w.intro')}</p>
            <ul className="list-disc space-y-1 ps-5 text-body-sm text-ink">
              {['s1', 's2', 's3', 's4'].map((s) => <li key={s}>{t('p38.w.' + s)}</li>)}
            </ul>
            <Links items={[['https://www.tceq.texas.gov/drinkingwater/notices/bwn/understanding-bwns', 'p38.w.l1']]} />
          </div>
        </Card>
      </div>
    </section>
  )
}
