import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, MapPin } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../ctx'
import { placeName, toProfile, usePlace, type Household } from '../state/place'
import { Lockup } from '../components/brand/Logo'
import { Button, Card, Stepper } from '../components/ds'
import { LanguageList } from '../components/shell/LanguageSheet'
import { PlaceForm } from '../components/shell/PlaceForm'
import { HouseholdForm } from '../components/shell/HouseholdForm'

/** First-run onboarding: language -> place -> household (§3.5). Skippable. */
export default function Welcome({ onDone }: { onDone: () => void }) {
  const { t, lang, setLang } = useApp()
  const { place, household, setHousehold, finishOnboarding } = usePlace()
  const [step, setStep] = useState(0)
  const [changing, setChanging] = useState(false)
  const [draft, setDraft] = useState<Household>(household)
  const h1 = useRef<HTMLHeadingElement>(null)
  useEffect(() => { h1.current?.focus() }, [step])

  const finish = (saveHousehold: boolean) => {
    if (saveHousehold) {
      setHousehold(draft)
      api.saveProfile(toProfile(draft, place, lang)).catch(() => { /* fire-and-forget */ })
    }
    finishOnboarding()
    onDone()
  }
  const steps = [t('welcome.s1'), t('welcome.s2'), t('welcome.s3')]

  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <div className="mx-auto flex w-full max-w-lg flex-1 flex-col px-4 pt-[max(1rem,env(safe-area-inset-top))]">
        <header className="flex h-14 items-center justify-between">
          <Lockup size={32} />
          <button type="button" onClick={() => finish(step === 2)} className="min-h-11 rounded-md px-3 text-body-sm font-semibold text-brand underline-offset-2 hover:underline">
            {t('welcome.skip')}
          </button>
        </header>
        <Stepper steps={steps} current={step} className="mb-6 mt-2" />

        <main className="flex-1 pb-6">
          {step === 0 && (
            <section aria-labelledby="w-h1">
              <h1 id="w-h1" ref={h1} tabIndex={-1} className="text-h1 outline-none">{t('app')}</h1>
              <p className="mt-2 text-body text-muted">{t('welcome.sub')}</p>
              <div className="mt-6"><LanguageList value={lang} onChange={setLang} large /></div>
              <p className="mt-6 text-body-sm text-muted">{t('welcome.note')}</p>
            </section>
          )}
          {step === 1 && (
            <section aria-labelledby="w-h1">
              <h1 id="w-h1" ref={h1} tabIndex={-1} className="text-h1 outline-none">{t('welcome.placeTitle')}</h1>
              <p className="mt-2 text-body text-muted">{t('welcome.placeSub')}</p>
              <div className="mt-6">
                {place && !changing ? (
                  <Card tone="normal">
                    <p className="flex items-center gap-2 text-h3"><Check aria-hidden size={20} className="text-normal" />{placeName(place.nickname, t)}</p>
                    <p className="mt-1 flex items-start gap-2 text-body-sm"><MapPin aria-hidden size={16} className="mt-0.5 shrink-0 text-brand" /><bdi>{place.label}</bdi></p>
                    <button type="button" onClick={() => setChanging(true)} className="mt-2 min-h-11 font-semibold text-brand underline underline-offset-2">{t('place.change')}</button>
                  </Card>
                ) : (
                  <PlaceForm onSaved={() => setChanging(false)} />
                )}
              </div>
            </section>
          )}
          {step === 2 && (
            <section aria-labelledby="w-h1">
              <h1 id="w-h1" ref={h1} tabIndex={-1} className="text-h1 outline-none">{t('welcome.hhTitle')}</h1>
              <p className="mt-2 text-body text-muted">{t('welcome.hhSub')}</p>
              <div className="mt-6"><HouseholdForm value={draft} onChange={setDraft} /></div>
            </section>
          )}
        </main>
      </div>

      <div className="sticky bottom-0 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)]">
        <div className="mx-auto flex w-full max-w-lg items-center justify-between gap-3 px-4 py-3">
          {step > 0
            ? <Button variant="ghost" icon={ArrowLeft} onClick={() => setStep(step - 1)} className="rtl:[&_svg]:rotate-180">{t('welcome.back')}</Button>
            : <span />}
          {step === 0 && <Button size="lg" iconEnd={ArrowRight} onClick={() => setStep(1)} className="rtl:[&_svg]:rotate-180">{t('welcome.next')}</Button>}
          {step === 1 && (place && !changing
            ? <Button size="lg" iconEnd={ArrowRight} onClick={() => setStep(2)} className="rtl:[&_svg]:rotate-180">{t('welcome.next')}</Button>
            : <Button variant="secondary" size="lg" onClick={() => finish(false)}>{t('welcome.skipPlace')}</Button>)}
          {step === 2 && <Button size="lg" icon={Check} onClick={() => finish(true)}>{t('welcome.finish')}</Button>}
        </div>
      </div>
    </div>
  )
}
