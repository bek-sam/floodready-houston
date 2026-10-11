import { useEffect, useState } from 'react'
import { CalendarPlus, Check, ChevronLeft, ChevronRight, ExternalLink, Pencil } from 'lucide-react'
import TenantLetter from '../components/TenantLetter'
import MedicalAccess from '../components/MedicalAccess'
import PowerDependentCard from '../components/prepare/PowerDependentCard'
import PetsCard from '../components/pets/PetsCard'
import SharePlanCard from '../components/share/SharePlanCard'
import { PayLess } from '../components/p35/P35'
import GoBag from '../components/gobag/GoBag'
import SeasonReminders from '../components/season/SeasonReminders'
import StayInformed from '../components/p38/StayInformed'
import EvacuationHelp from '../components/prepare/EvacuationHelp'
import { ApiError, api, errText, type Countdown, type Plan, type When } from '../api'
import { useApp } from '../ctx'
import { PLAN_AT, fmtAt, useOnline } from '../lib/offline'
import { useBk } from '../lib/bk'
import { Button, Card, Checkbox, ErrorBox, Field, Input, PageHeader, SkeletonText, SourceLink, StatTile, Stepper, Tabs } from '../components/ds'
import { Warnings } from '../components/ui'
import { parseHash } from '../components/shell/nav'
import { useShell } from '../components/shell/ShellContext'
import { householdChips, store, toProfile, usePlace, useDemoMode } from '../state/place'

const today = () => new Date().toISOString().slice(0, 10)
const WHEN: When[] = ['now', 'storm_watch', 'storm', 'after']
const TABS = ['plan', 'insurance', 'medical', 'renters', 'evacuate', 'gobag', 'pets', 'season'] as const
type Tab = (typeof TABS)[number]
const DONE_KEY = 'floodready.planDone.v1'

function downloadIcs(cd: Countdown) {
  if (!cd.effective_date) return
  const d = cd.effective_date.replace(/-/g, '')
  const next = new Date(Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8) + 1)).toISOString().slice(0, 10).replace(/-/g, '')
  const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//FloodReady Houston//EN', 'BEGIN:VEVENT',
    `UID:floodready-${d}@floodready.local`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15)}Z`,
    `DTSTART;VALUE=DATE:${d}`, `DTEND;VALUE=DATE:${next}`,
    'SUMMARY:Flood insurance coverage starts', 'DESCRIPTION:Your flood insurance waiting period ends and coverage begins. Confirm with your insurer.',
    'END:VEVENT', 'END:VCALENDAR'].join('\r\n')
  const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }))
  const a = document.createElement('a')
  a.href = url; a.download = 'flood-insurance-coverage.ics'
  document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function fmtDate(iso: string, lang: string) {
  try { return new Date(iso + 'T12:00:00').toLocaleDateString(lang, { weekday: 'long', month: 'short', day: 'numeric' }) } catch { return iso }
}

export default function Prepare() {
  const { t, lang } = useApp()
  const bk = useBk()
  const { place, household } = usePlace()
  const { demo } = useDemoMode()
  const { openHouseholdSheet } = useShell()

  const defaultTab: Tab = household.medical.dialysis ? 'medical' : household.renter ? 'renters' : 'plan'
  const fromHash = (): Tab => { const s = parseHash().sub?.split('/')[0]; return (TABS as readonly string[]).includes(s ?? '') ? (s as Tab) : defaultTab }
  const [tab, setTab] = useState<Tab>(fromHash)
  useEffect(() => {
    const f = () => { if (parseHash().route === 'prepare') setTab(fromHash()) }
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    const sub = parseHash().sub
    if (sub) document.getElementById('prepare-' + sub.split('/')[1])?.scrollIntoView?.()
  }, [tab])
  const pick = (v: Tab) => { setTab(v); history.replaceState(history.state, '', '#prepare/' + v) }

  // Insurance
  const [date, setDate] = useState(today())
  const [cd, setCd] = useState<Countdown | null>(null)
  const [cdErr, setCdErr] = useState<string | null>(null)
  const [cdBusy, setCdBusy] = useState(false)
  const runCd = async () => {
    setCdBusy(true); setCdErr(null)
    try { setCd(await api.countdown(date)) } catch (e) { setCdErr(errText(e, t('offline'))) } finally { setCdBusy(false) }
  }

  // Plan
  const [plan, setPlanState] = useState<Plan | null>(() => {
    try { const p = JSON.parse(localStorage.getItem('lastPlan') || 'null'); return p && Array.isArray(p.steps) ? p : null } catch { return null }
  })
  const [planAt, setPlanAt] = useState<number | null>(() => Number(store.get(PLAN_AT)) || null)
  const [fallback, setFallback] = useState(false)
  const online = useOnline()
  const setPlan = (p: Plan | null, fb = false) => {
    setPlanState(p); setFallback(fb)
    if (!fb) { const now = Date.now(); store.set('lastPlan', JSON.stringify(p)); store.set(PLAN_AT, String(now)); setPlanAt(now) }
  }
  const [planErr, setPlanErr] = useState<string | null>(null)
  const [planBusy, setPlanBusy] = useState(false)
  const [stage, setStage] = useState(0)
  const [done, setDone] = useState<Record<string, boolean>>(() => store.json(DONE_KEY, {}))
  const toggle = (k: string, v: boolean) => { const n = { ...done, [k]: v }; setDone(n); store.set(DONE_KEY, JSON.stringify(n)) }
  const runPlan = async () => {
    setPlanBusy(true); setPlanErr(null)
    const profile = toProfile(household, place, lang)
    try {
      let saved = profile
      try { saved = await api.saveProfile(profile) } catch { /* plan can still run without saving */ }
      setPlan(await api.plan(saved, place?.lat ?? 29.7604, place?.lon ?? -95.3698))
      setStage(0)
    } catch (e2) {
      if (e2 instanceof ApiError && e2.status === 0 && !plan) {
        const st = (n: number, when: When) => ({ title: t(`p37.plan.fb${n}t`), detail: t(`p37.plan.fb${n}d`), when })
        setPlan({ steps: [st(1, 'now'), st(2, 'now'), st(3, 'storm'), st(4, 'storm')], generated_by: 'template' }, true); setStage(0)
      } else setPlanErr(errText(e2, t('offline')))
    } finally { setPlanBusy(false) }
  }
  const chips = householdChips(household)
  const stages = WHEN.map((w) => ({ w, steps: (plan?.steps ?? []).filter((s) => s.when === w) }))
  const stageNames = WHEN.map((w) => t('when.' + w))
  const cur = stages[stage]
  const doneN = (plan?.steps ?? []).filter((s) => done[s.when + '|' + s.title]).length

  return (
    <div>
      <PageHeader title={t('p5a.title')} forPlace />
      <div className="sticky top-0 z-10 -mx-4 mb-4 bg-bg px-4 md:-mx-0 md:px-0">
        <Tabs label={t('p5a.tabs')} idPrefix="prep" value={tab} onChange={pick}
          items={TABS.map((v) => ({ value: v, label: t(v === 'gobag' || v === 'season' || v === 'pets' ? 'p10.tab.' + v : 'p5a.tab.' + v) }))} />
      </div>

      <div role="tabpanel" id={`prep-panel-${tab}`} aria-labelledby={`prep-tab-${tab}`} className="space-y-4">
        {tab === 'plan' && (
          <>
            <Card id="prepare-plan" title={t('prep.profile')} subtitle={t('p5a.plan.sub')}
              action={<Button variant="ghost" icon={Pencil} onClick={openHouseholdSheet}>{t('hh.edit')}</Button>}>
              {chips.length ? (
                <ul className="flex flex-wrap gap-2">{chips.map((k) => <li key={k} className="rounded-full bg-surface-2 px-3 py-1 text-body-sm text-ink">{t(k)}</li>)}</ul>
              ) : <p className="text-body-sm text-muted">{t('p5a.plan.noHh')}</p>}
              <Button className="mt-4" size="lg" loading={planBusy} onClick={runPlan}>{plan ? t('p5a.plan.update') : t('p5a.plan.build')}</Button>
              {planErr && <div className="mt-3"><ErrorBox error={planErr} onRetry={runPlan} /></div>}
            </Card>

            <SharePlanCard />

            <a href="#offline" className="inline-flex min-h-11 items-center font-semibold text-brand underline underline-offset-2">{t('p37.card.open')}</a>

            {planBusy && (
              <Card aria-busy={true}>
                <p className="mb-3 text-body-sm font-semibold text-ink">{t('p5a.plan.building')}</p>
                <SkeletonText lines={5} />
              </Card>
            )}

            {plan && !planBusy && (!online || fallback) && (
              <p role="status" className="text-body-sm text-muted">
                {fallback ? t('p37.plan.fbNote') : planAt ? t('p37.plan.saved').replace('{time}', fmtAt(planAt, lang)) : ''}
              </p>
            )}

            {plan && !planBusy && (
              <Card title={stageNames[stage]} titleAs="h2" subtitle={t('p5a.plan.done').replace('{n}', String(doneN)).replace('{m}', String(plan.steps.length))}>
                <Stepper className="mb-4" steps={stageNames} current={stage} />
                {cur.steps.length === 0 ? <p className="text-body-sm text-muted">{t('p5a.plan.empty')}</p> : (
                  <ul className="space-y-2">
                    {cur.steps.map((s) => {
                      const k = s.when + '|' + s.title
                      return (
                        <li key={k} className="rounded-md border border-line bg-surface p-3">
                          <Checkbox checked={!!done[k]} onChange={(v) => toggle(k, v)}
                            label={<span className={done[k] ? 'text-muted line-through' : 'font-semibold'}>{s.title}</span>}
                            description={s.detail} />
                        </li>
                      )
                    })}
                  </ul>
                )}
                <div className="mt-4 flex justify-between gap-2" role="group" aria-label={t('p5a.plan.stages')}>
                  <Button variant="secondary" icon={ChevronLeft} disabled={stage === 0} onClick={() => setStage(stage - 1)}>{t('p5a.plan.prev')}</Button>
                  <Button variant="secondary" iconEnd={ChevronRight} disabled={stage === WHEN.length - 1} onClick={() => setStage(stage + 1)}>{t('p5a.plan.next')}</Button>
                </div>
                <div className="mt-4 space-y-1">
                  <Warnings items={plan.warnings} codes={plan.warning_codes} />
                  <p className="text-caption text-muted">{t('p5a.plan.footer')}{demo && <> {t('p5a.plan.by')}: {plan.generated_by}.</>}</p>
                </div>
              </Card>
            )}

            <Card title={t('p5a.alerts.h')} titleAs="h2">
              <ul className="divide-y divide-line">
                {[
                  ['ReadyHarris accessible alert system', 'https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-launches-accessible-alert-system'],
                  ['Harris County Flood Warning System', 'https://harriscountyfws.org/'],
                ].map(([n, u]) => (
                  <li key={u}><a href={u} target="_blank" rel="noreferrer" className="flex min-h-12 items-center justify-between gap-2 text-brand">
                    <span className="underline underline-offset-2">{n}</span><ExternalLink aria-hidden size={16} /><span className="sr-only">{t('ds.newTab')}</span></a></li>
                ))}
              </ul>
            </Card>
          </>
        )}

        {tab === 'insurance' && (
          <>
            <Card id="prepare-insurance" title={t('p5a.ins.h')} titleAs="h2">
              <div className="flex flex-wrap items-end gap-3">
                <div className="min-w-44 flex-1"><Field label={t('p5a.ins.date')}>
                  <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                </Field></div>
                <Button loading={cdBusy} onClick={runCd}>{t('p5a.ins.go')}</Button>
              </div>
              {cdErr && <div className="mt-3"><ErrorBox error={cdErr} onRetry={runCd} /></div>}
              {cd && (
                <div className="mt-4 space-y-3">
                  <StatTile label={t('p5a.ins.starts')} value={fmtDate(cd.effective_date, lang)} sub={t('p5a.ins.wait').replace('{n}', String(cd.days_wait)).replace('{d}', new Date(cd.season_end + 'T12:00:00').toLocaleDateString(lang, { year: 'numeric', month: 'short', day: 'numeric' }))} icon={Check} />
                  <p className="text-body-sm text-ink">{bk(cd.message_code, cd.message_params, cd.message)}</p>
                  {cd.exceptions_note && <p className="text-caption text-muted">{bk(cd.exceptions_note_code || 'ins.exceptions', {}, cd.exceptions_note)}<SourceLink href="https://www.floodsmart.gov/get-insured/buy-a-policy" label={t('p26.ins.src')} /></p>}
                  <div className="flex flex-wrap items-center gap-3">
                    <Button variant="secondary" icon={CalendarPlus} onClick={() => downloadIcs(cd)}>{t('p5a.ins.cal')}</Button>
                    <SourceLink href={cd.source} />
                  </div>
                </div>
              )}
            </Card>
            <PayLess />
            <a href="#home/rentbuy" className="flex min-h-12 items-center justify-between gap-2 rounded-lg border border-line bg-surface p-4 text-body-sm font-semibold text-brand">
              {place?.zip ? t('p5a.ins.zip').replace('{zip}', place.zip) : t('p5a.ins.zipNone')}<ChevronRight aria-hidden size={18} />
            </a>
          </>
        )}

        {tab === 'medical' && <div id="prepare-medical"><MedicalAccess /><div className="mt-4"><PowerDependentCard /></div></div>}

        {tab === 'renters' && (
          <>
            <p className="rounded-lg bg-surface-2 p-4 text-body-sm text-ink">{t('home.c5')} <SourceLink href="https://statutes.capitol.texas.gov/Docs/PR/htm/PR.92.htm" /></p>
            <TenantLetter />
          </>
        )}

        {tab === 'evacuate' && <div id="prepare-evacuate" className="space-y-6"><EvacuationHelp /><StayInformed /></div>}
        {tab === 'gobag' && <GoBag />}
        {tab === 'pets' && <PetsCard />}
        {tab === 'season' && <SeasonReminders />}
      </div>
    </div>
  )
}
