import { useState, type ReactNode } from 'react'
import { Clock, RefreshCw, WifiOff } from 'lucide-react'
import { useApp } from '../../ctx'
import { exposureLabelKey, exposureLevel, LEVEL_CLASS, type Level } from '../../lib/levels'
import { anyFailed, fill, fillReason, pendingCount, timeOf, whyChips, type ExposureResult, type RightNow, type SummaryInputs } from '../../lib/summary'
import { ErrorBox, IconButton, LoadingText, RiskBadge, Sheet } from '../ds'
import { WhyChips } from './WhyChips'


function LevelBlock({ title, level, label, reason, busy, children }: {
  title: string; level: Level; label: string; reason: string; busy: boolean; children?: ReactNode
}) {
  return (
    <div className="min-w-0" aria-live="polite" aria-atomic="true">
      {/* Phones: label and badge share a row to keep the first action card on screen. */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 sm:block">
        <h2 className="min-w-[6.5rem] text-overline uppercase text-muted">{title}</h2>
        <RiskBadge level={level} label={label} size="lg" className="sm:mt-2 max-sm:min-h-10 max-sm:px-3 max-sm:text-[18px]" />
      </div>
      {children ?? <p className={`mt-1.5 text-body-sm sm:mt-2 ${busy ? 'text-muted' : 'text-ink'}`}>{reason}</p>}
    </div>
  )
}

/** "Flood readiness summary": Right now + This place, why chips, fine print, updated time (§4.2). */
export function SummaryHero({ placeLabel, inputs, now, exp, updatedAt, offlineAt, refreshing, onRefresh }: {
  placeLabel: string; inputs: SummaryInputs; now: RightNow; exp: ExposureResult
  updatedAt: number | null; offlineAt: number | null; refreshing: boolean; onRefresh: () => void
}) {
  const { t, lang } = useApp()
  const [how, setHow] = useState(false)
  const chips = whyChips(inputs)
  const pending = pendingCount(inputs)
  const busy = pending > 0
  const nowLabel = now.final ? (now.level === 'unknown' ? t('sum.nowUnknown') : t('level.' + now.level)) : t('level.unknown')
  const expLevel = exp.final ? exposureLevel(exp.exposure) : 'unknown'
  const expLabel = exp.final ? t(exposureLabelKey(exp.exposure)) : t('level.unknown')
  const top = now.final ? LEVEL_CLASS[now.level].borderTop : LEVEL_CLASS.unknown.borderTop
  const riskFailed = inputs.risk.failed

  return (
    <section aria-labelledby="sum-eyebrow" aria-busy={busy || undefined}
      className={`rounded-xl border border-t-4 border-line bg-surface px-4 pt-3 pb-1 shadow-card sm:p-5 md:p-6 ${top}`}>
      {busy && <LoadingText label={t('sum.checking')} />}
      <div className="flex items-start justify-between gap-2">
        <p id="sum-eyebrow" className="text-overline uppercase text-muted">
          <span className="sr-only">{t('sum.regionLabel')}: </span>{fill(t, 'sum.eyebrow', { place: placeLabel })}
        </p>
        {offlineAt != null && (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-caption text-muted">
            <WifiOff aria-hidden size={14} />{fill(t, 'sum.offline', { time: timeOf(offlineAt, lang) })}
          </span>
        )}
      </div>

      <div className="mt-2 grid gap-3 sm:mt-3 sm:grid-cols-2 sm:gap-6">
        <LevelBlock title={t('sum.now')} level={now.final ? now.level : 'unknown'} label={nowLabel}
          reason={now.final ? fillReason(t, now.reason) : t('sum.checking')} busy={!now.final} />
        <LevelBlock title={t('sum.place')} level={expLevel} label={expLabel}
          reason={exp.final ? fillReason(t, exp.reason) : t('sum.checking')} busy={!exp.final}>
          {riskFailed ? <ErrorBox className="mt-2" error={t('sum.exp.unknown')} onRetry={onRefresh} /> : undefined}
        </LevelBlock>
      </div>

      <div className="mt-3 sm:mt-4">
        <WhyChips chips={chips} inputs={inputs} pending={pending} />
      </div>

      {anyFailed(inputs) && <p className="mt-3 text-caption font-semibold text-ink sm:mt-4">{t('sum.partial')}</p>}
      {/* On phones the fine print moves into the "How we decide" sheet to keep the first action card on screen. */}
      <p className="mt-4 hidden text-caption text-muted sm:block">
        {t('sum.fine')}{' '}
        <button type="button" onClick={() => setHow(true)} aria-haspopup="dialog"
          className="min-h-6 font-semibold text-brand underline underline-offset-2 hover:text-brand-strong">{t('sum.how')}</button>
      </p>

      <div className="mt-1 flex min-h-11 flex-wrap items-center gap-x-1.5 text-caption text-muted sm:mt-2">
        <Clock aria-hidden size={14} />
        <span aria-live="polite">{updatedAt != null ? fill(t, 'sum.updated', { time: timeOf(updatedAt, lang) }) : t('sum.checking')}</span>
        <IconButton icon={RefreshCw} label={t('sum.refresh')} onClick={onRefresh} disabled={refreshing}
          className={`-my-2 text-muted ${refreshing ? '[&_svg]:animate-spin' : ''}`} />
        <button type="button" onClick={() => setHow(true)} aria-haspopup="dialog"
          className="ms-auto min-h-11 font-semibold text-brand underline underline-offset-2 sm:hidden">{t('sum.how')}</button>
      </div>

      <Sheet open={how} onClose={() => setHow(false)} title={t('how.title')}>
        <div className="space-y-4 text-body-sm text-ink">
          <p>{t('how.intro')}</p>
          <p className="text-muted sm:hidden">{t('sum.fine')}</p>
          <section>
            <h3 className="text-h3">{t('how.nowTitle')}</h3>
            <ul className="mt-2 space-y-2">
              {(['danger', 'warning', 'watch', 'normal'] as const).map((l, i) => (
                <li key={l} className="flex items-start gap-2"><RiskBadge level={l} label={t('level.' + l)} size="sm" className="mt-0.5 shrink-0" /><span>{t('how.now' + (i + 1)).replace(/^[^:]+:\s*/, '')}</span></li>
              ))}
            </ul>
          </section>
          <section>
            <h3 className="text-h3">{t('how.placeTitle')}</h3>
            <ul className="mt-2 space-y-2">
              {(['high', 'elevated', 'lower'] as const).map((e, i) => (
                <li key={e} className="flex items-start gap-2"><RiskBadge level={exposureLevel(e)} label={t(exposureLabelKey(e))} size="sm" className="mt-0.5 shrink-0" /><span>{t('how.place' + (i + 1)).replace(/^[^:]+:\s*/, '')}</span></li>
              ))}
            </ul>
            <p className="mt-2 text-muted">{t('how.place4')}</p>
          </section>
          <p className="font-semibold">{t('how.notOfficial')}</p>
        </div>
      </Sheet>
    </section>
  )
}
