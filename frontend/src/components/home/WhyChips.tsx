import { useState } from 'react'
import {
  ArrowDownToLine, BellRing, CloudOff, CloudRain, Droplets, ExternalLink, FileText, History, LifeBuoy, Map as MapIcon, Waves, type LucideIcon,
} from 'lucide-react'
import { useApp } from '../../ctx'
import { LEVEL_CLASS } from '../../lib/levels'
import { useBk } from '../../lib/bk'
import { fill, SRC, type Chip, type ChipKind, type SummaryInputs } from '../../lib/summary'
import { Skeleton, Sheet, SourceLink } from '../ds'

const ICON: Record<ChipKind, LucideIcon> = {
  fema: MapIcon, harvey: Waves, harveyNo: Waves, gaugeHist: History, zipClaims: FileText, lowGround: ArrowDownToLine,
  reservoir: Droplets, evac: LifeBuoy, surge: Waves, alert: BellRing, outlook: CloudRain, gaugeNow: Waves, unavailable: CloudOff,
}
const LABEL_KEY: Record<ChipKind, string> = {
  fema: 'chip.fema', harvey: 'chip.harvey', harveyNo: 'chip.harveyNo', gaugeHist: 'chip.gaugeHist', zipClaims: 'chip.zipClaims',
  lowGround: 'chip.lowGround', evac: 'chip.evac', surge: 'chip.surge', reservoir: 'chip.reservoir', alert: 'chip.alert', outlook: 'chip.outlook', gaugeNow: 'chip.gaugeNow',
  unavailable: 'chip.unavailable',
}
/** Friendly source labels for links the generic host map does not cover. */
const SOURCE_LABEL: Record<string, string> = {
  [SRC.sfha]: '12 CFR 339 App. A', [SRC.flat]: 'Harris County MAAPnext', [SRC.dams]: 'Texas Tribune', [SRC.evac]: 'ReadyHarris', [SRC.surge]: 'NOAA NHC storm surge maps',
}

function chipLabel(t: (k: string) => string, c: Chip, lang: string) {
  const vars = { ...c.vars }
  if (c.kind === 'zipClaims') vars.n = Number(vars.n).toLocaleString(lang)
  return fill(t, LABEL_KEY[c.kind], vars)
}

/** Plain explanation for a chip, from API fields and existing sourced copy only. */
function Explain({ chip, inputs }: { chip: Chip; inputs: SummaryInputs }) {
  const { t, lang } = useApp()
  const bk = useBk()
  const r = inputs.risk.data
  const p = (s?: string | null) => (s ? <p className="text-body-sm text-ink">{s}</p> : null)
  const note = (s?: string | null) => (s ? <p className="text-caption text-muted">{s}</p> : null)
  switch (chip.kind) {
    case 'fema': return <>{p(t(r?.sfha ? 'home.femaPlain.sfha' : 'home.femaPlain.low'))}{r?.zone_subtype && note(r.zone_subtype)}</>
    case 'harvey': return <>{p(t('ex.harvey'))}{note(bk(r?.harvey?.note_code, {}, r?.harvey?.note))}</>
    case 'harveyNo': return <>{p(t('ex.harveyNo'))}{note(bk(r?.harvey?.note_code, {}, r?.harvey?.note))}</>
    case 'gaugeHist': return <>{p(fill(t, 'ex.gaugeHist', chip.vars))}{note(t('c6.hist.note'))}
      <p><a href="#replay" className="text-body-sm font-semibold text-brand underline underline-offset-2">{t('det.replayLink')}</a></p></>
    case 'zipClaims': return <>{p(fill(t, 'ex.zip', { ...chip.vars, n: Number(chip.vars.n).toLocaleString(lang), m: Number(chip.vars.m).toLocaleString(lang) }))}{note(bk(inputs.zip?.data?.note_code, {}, inputs.zip?.data?.note))}</>
    case 'evac': return <>{p(fill(t, 'ex.evac', chip.vars))}{note(t('p10.evac.note'))}</>
    case 'surge': return <>{p(fill(t, 'ex.surge', chip.vars))}{note(t('p10.evac.note'))}</>
    case 'lowGround': return <>{p(t('home.lowGround'))}</>
    case 'reservoir': {
      const fact = (r?.facts ?? []).find((f) => f?.source === SRC.dams)
      return <>{p(fact ? bk(fact.code, fact.params, fact.text) : t('home.c3'))}</>
    }
    case 'alert': {
      const a = (inputs.alerts.data?.alerts ?? []).find((x) => x.event === chip.vars.event)
      return <>{p(fill(t, 'ex.alert', chip.vars))}{a?.headline && note(a.headline)}</>
    }
    case 'outlook': return <>{p(fill(t, 'ex.outlook', chip.vars))}{note(bk(inputs.outlook.data?.note_code, {}, inputs.outlook.data?.note))}</>
    case 'gaugeNow': return <>{p(fill(t, 'ex.gaugeNow', chip.vars))}</>
    default: return <>{p(t('ex.unavailable'))}</>
  }
}

/** One chip per signal that fired. Tapping opens a sheet with the explanation and the source. */
export function WhyChips({ chips, inputs, pending }: { chips: Chip[]; inputs: SummaryInputs; pending: number }) {
  const { t, lang } = useApp()
  const [open, setOpen] = useState<Chip | null>(null)
  const skeletons = Math.min(3, pending)
  return (
    <>
      <ul aria-label={t('sum.whyLabel')} className="flex flex-wrap gap-2">
        {chips.map((c) => {
          const Icon = ICON[c.kind]
          const label = chipLabel(t, c, lang)
          const cls = c.tone === 'neutral'
            ? (c.kind === 'unavailable' ? 'border-line bg-surface-2 text-muted' : 'border-line bg-surface-2 text-ink')
            : `${LEVEL_CLASS[c.tone].bg} ${LEVEL_CLASS[c.tone].text} ${LEVEL_CLASS[c.tone].border}`
          return (
            <li key={c.id} className="max-w-full">
              <button type="button" onClick={() => setOpen(c)} aria-label={fill(t, 'chip.more', { label })} aria-haspopup="dialog"
                className={`inline-flex min-h-9 max-w-full items-center gap-1.5 rounded-full border px-3 py-1 text-start text-caption font-semibold transition-colors duration-150 hover:brightness-95 ${cls}`}>
                <Icon aria-hidden size={14} className="shrink-0" />
                <span className="min-w-0 break-words">{label}</span>
                {c.source && <ExternalLink aria-hidden size={12} className="shrink-0 opacity-70" />}
              </button>
            </li>
          )
        })}
        {Array.from({ length: skeletons }, (_, i) => <li key={'sk' + i}><Skeleton w={90 + i * 14} h={36} radius={999} /></li>)}
      </ul>
      <Sheet open={!!open} onClose={() => setOpen(null)} title={open ? chipLabel(t, open, lang) : ''}>
        {open && (
          <div className="space-y-3">
            <Explain chip={open} inputs={inputs} />
            {open.source && <p className="text-caption text-muted">{t('source')}:<SourceLink href={open.source} label={SOURCE_LABEL[open.source] ?? (open.kind === 'outlook' ? 'NOAA WPC' : open.kind === 'zipClaims' ? 'OpenFEMA NFIP' : undefined)} /></p>}
          </div>
        )}
      </Sheet>
    </>
  )
}
