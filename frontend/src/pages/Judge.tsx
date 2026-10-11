import { useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { ArrowRight, RotateCcw } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../ctx'
import { Button, Card, Checkbox, PageHeader, Switch, toast } from '../components/ds'
import SmsSimulator from '../components/SmsSimulator'
import Evidence from '../components/JudgeEvidence'
import { DEFAULT_HOUSEHOLD, KEYS, store, usePlace, useSimStorm, type Household } from '../state/place'

const DEMO_ADDR = '5300 N Braeswood Blvd, Houston, TX 77096'
const DEMO_FALLBACK = { lat: 29.6847, lon: -95.4698, label: DEMO_ADDR }
const CHECK_KEY = 'floodready.judgeChecked'
const GO_KEY = 'floodready.demoGo' // read by Drive/Replay/Ask/Alerts to preload the demo step (sessionStorage)
type Go = { hash: string; lang?: string; household?: Household; place?: boolean; storm?: boolean }
const STEPS: Go[] = [
  { hash: '#home', place: true, household: { ...DEFAULT_HOUSEHOLD, renter: false, hasCar: true } },
  { hash: '#drive', storm: true },
  { hash: '#replay' },
  { hash: '#ask', lang: 'es' },
  { hash: '#alerts', storm: true },
]

export default function Judge() {
  const { t, setLang } = useApp()
  const { demo, setDemo, setPlace, setHousehold } = usePlace()
  const { setSim } = useSimStorm()
  const [nCross, setNCross] = useState<number | null>(null)
  useEffect(() => { api.crossings().then((c) => setNCross(c.features.length)).catch(() => setNCross(null)) }, [])
  const url = location.origin + '/'
  const [svg, setSvg] = useState('')
  const [checked, setChecked] = useState<boolean[]>(() => { try { const v = JSON.parse(sessionStorage.getItem(CHECK_KEY) || '[]'); return [0, 1, 2, 3, 4].map((i) => !!v[i]) } catch { return [false, false, false, false, false] } })
  const [busy, setBusy] = useState<number | 'reset' | null>(null)
  useEffect(() => {
    QRCode.toString(url, { type: 'svg', margin: 1, color: { dark: '#000000', light: '#ffffff' } }).then(setSvg).catch(() => setSvg(''))
  }, [url])
  const mark = (i: number, v: boolean) => {
    const n = checked.map((c, j) => (j === i ? v : c)); setChecked(n)
    try { sessionStorage.setItem(CHECK_KEY, JSON.stringify(n)) } catch { /* ignore */ }
  }
  const demoPlace = async () => {
    try { const g = await api.geocode(DEMO_ADDR); setPlace({ lat: g.lat, lon: g.lon, label: g.matched_address || DEMO_ADDR }) } catch { setPlace(DEMO_FALLBACK) }
  }
  const go = async (i: number) => {
    const s = STEPS[i]
    setBusy(i)
    if (s.place) await demoPlace()
    if (s.household) setHousehold(s.household)
    if (s.lang) setLang(s.lang)
    if (s.storm) { setDemo(true); setSim(true) }
    store.set(GO_KEY, String(i + 1), true)
    setBusy(null)
    location.hash = s.hash
  }
  const reset = async () => {
    setBusy('reset')
    setHousehold(DEFAULT_HOUSEHOLD); store.set(KEYS.actionsDone, null); store.set('lastPlan', null); store.set('floodready.planDone.v1', null)
    store.set(GO_KEY, null, true); setChecked([false, false, false, false, false])
    try { sessionStorage.removeItem(CHECK_KEY) } catch { /* ignore */ }
    await demoPlace()
    setBusy(null)
    toast(t('p5a.j.resetDone'))
  }

  return (
    <div>
      <PageHeader title={t('p5a.j.title')} subtitle={t('p5a.j.sub')} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,360px)_1fr]">
        <div className="space-y-4">
          <Card title={t('p5a.j.qr')}>
            <div role="img" aria-label={t('p5a.j.qrAlt').replace('{url}', url)} className="mx-auto w-56 rounded-lg bg-white p-2" dangerouslySetInnerHTML={{ __html: svg }} />
            <p className="mt-2 break-all text-center text-body-sm"><a className="text-brand underline underline-offset-2" href={url}>{t('judge.open')}: {url}</a></p>
          </Card>
          <Card>
            {!demo && <Button full className="mb-3" onClick={() => { setDemo(true); location.hash = '#drive' }}>{t('p29.demo.btn')}</Button>}
            <Switch label={t('p5a.j.demoOn')} description={t('p5a.j.demoOnD')} checked={demo} onChange={setDemo} />
            <div className="mt-3 border-t border-line pt-3">
              <Button variant="secondary" icon={RotateCcw} loading={busy === 'reset'} onClick={reset}>{t('p5a.j.reset')}</Button>
              <p className="mt-2 text-caption text-muted">{t('p5a.j.resetD')}</p>
            </div>
          </Card>
        </div>
        <div className="space-y-4">
          <h2 className="text-h2 text-ink">{t('p5a.j.script')}</h2>
          <ol className="space-y-3">
            {[1, 2, 3, 4, 5].map((n) => (
              <li key={n}>
                <Card padding="md">
                  <div className="flex items-start gap-3">
                    <span aria-hidden className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand-tint text-body-sm font-bold text-brand">{n}</span>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-h3 text-ink"><span className="sr-only">{t('p5a.j.step').replace('{n}', String(n))}: </span>{t(`p5a.j.s${n}.t`)}</h3>
                      <p className="mt-1 text-body-sm text-muted"><b className="font-semibold text-ink">{t('p5a.j.look')}:</b> {t(`p5a.j.s${n}.l`)}</p>
                      <div className="mt-3 flex flex-wrap items-center gap-3">
                        <Button iconEnd={ArrowRight} loading={busy === n - 1} onClick={() => go(n - 1)}>{t('p5a.j.go')}</Button>
                        <Checkbox label={t('ds.markDone')} checked={checked[n - 1]} onChange={(v) => mark(n - 1, v)} />
                      </div>
                    </div>
                  </div>
                </Card>
              </li>
            ))}
          </ol>
          {demo && (
            <Card title={t('p36.sms.title')}>
              <p className="mb-3 text-body-sm text-muted">{t('p36.sms.blurb')}</p>
              <SmsSimulator />
            </Card>
          )}
          <Evidence />
          <Card tone="inset" title={t('p5a.j.limits')}>
            <ul className="list-disc space-y-1 ps-5 text-body-sm text-ink">{[1, 2, 3, 4, 5].map((n) => <li key={n}>{n === 2 ? (nCross ? t('p5a.j.lim2').replace('{n}', String(nCross)) : t('p36.lim2n')) : t('p5a.j.lim' + n)}</li>)}</ul>
          </Card>
        </div>
      </div>
    </div>
  )
}
