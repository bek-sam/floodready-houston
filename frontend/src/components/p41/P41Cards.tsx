import { Phone } from 'lucide-react'
import { useApp } from '../../ctx'
import { Card, SourceLink } from '../ds'

const FEMA_APPEAL = 'https://www.fema.gov/fact-sheet/how-appeal-fema-decision-4'
const FEMA_FRAUD = 'https://www.fema.gov/press-release/20260403/protect-your-identity-be-alert-fraud-and-scams-after-disaster'
const CDC = 'https://www.cdc.gov/floods/safety/index.html'
const T211 = 'https://www.211texas.org/'
const CFTH = 'https://cfthhouston.org/severe-weather-resources'

function Call({ n, label }: { n: string; label: string }) {
  return (
    <a href={`tel:${n.replace(/[^\d+]/g, '')}`} className="flex min-h-11 items-center gap-3 rounded-md border border-ui bg-surface px-3 py-2 text-body-sm font-semibold text-ink">
      <Phone aria-hidden size={18} className="shrink-0" />{label}
    </a>
  )
}

function Steps({ id, n, calls, links }: { id: string; n: number; calls: [string, string][]; links: [string, string][] }) {
  const { t } = useApp()
  return (
    <Card title={t(`p41.${id}.t`)}>
      <ol className="list-decimal space-y-1 ps-5 text-body-sm text-ink">
        {Array.from({ length: n }, (_, i) => <li key={i}>{t(`p41.${id}.s${i + 1}`)}</li>)}
      </ol>
      <div className="mt-3 flex flex-col gap-2">{calls.map(([num, k]) => <Call key={num + k} n={num} label={t(k)} />)}</div>
      <div className="mt-2 flex flex-wrap gap-x-4">{links.map(([href, k]) => <SourceLink key={href} href={href} label={t(k)} />)}</div>
      <p className="mt-2 text-caption text-muted">{t('p41.note')}</p>
    </Card>
  )
}

/** Cycle 41: Recover-page cards. Facts from docs/cycles/cycle-41-research.md (verified). */
export function RecoverCards() {
  return (
    <>
      <Steps id="appeal" n={4} calls={[['18006213362', 'p41.call.helpline']]} links={[[FEMA_APPEAL, 'p41.src.appeal']]} />
      <Steps id="scam" n={4} calls={[['18667205721', 'p41.call.fraud'], ['18006213362', 'p41.call.helpline']]} links={[[FEMA_FRAUD, 'p41.src.fraud']]} />
      <Steps id="water" n={5} calls={[]} links={[[CDC, 'p41.src.cdc']]} />
    </>
  )
}

/** Cycle 41: Prepare-page card for people without housing. */
export function UnhousedCard() {
  return <Steps id="home" n={5} calls={[['18775417905', 'p41.call.211'], ['911', 'p41.call.911']]} links={[[T211, 'p41.src.211'], [CFTH, 'p41.src.cfth']]} />
}
