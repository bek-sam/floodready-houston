import { ChevronDown, Download, FlaskConical, Languages, MapPin, MapPinPlus, Menu, Moon, Sun, X } from 'lucide-react'
import { useApp } from '../../ctx'
import { placeName, streetOf, usePlace } from '../../state/place'
import { Lockup } from '../brand/Logo'
import { IconButton } from '../ds'

export function Header({ onPlace, onLang, onMore, onInstall, logoProps }: {
  onPlace: () => void; onLang: () => void; onMore: () => void; onInstall?: () => void
  logoProps: React.AnchorHTMLAttributes<HTMLAnchorElement>
}) {
  const { t, lang, dark, setDark } = useApp()
  const { place, demo, setDemo } = usePlace()
  const name = place ? placeName(place.nickname, t) : ''
  const street = place ? streetOf(place.label) : ''
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b border-line bg-surface px-3 md:px-6">
      <a href="#home" aria-label={t('app') + ', ' + t('nav.home')} className="shrink-0 rounded-md md:hidden" {...logoProps}>
        <Lockup compact textClassName="hidden min-[400px]:inline" />
      </a>

      <div className="flex min-w-0 flex-1 justify-center md:justify-start">
        <button type="button" onClick={onPlace}
          aria-label={place ? t('place.chipAria').replace('{name}', name).replace('{street}', street) : t('place.set')}
          className={`inline-flex h-9 min-w-0 max-w-full items-center gap-1.5 rounded-full border px-3 text-body-sm font-medium ${place ? 'border-line bg-surface-2 text-ink hover:border-ui' : 'border-brand bg-surface text-brand'}`}>
          {place ? <MapPin aria-hidden size={16} className="shrink-0 text-brand" /> : <MapPinPlus aria-hidden size={16} className="shrink-0" />}
          {place ? (
            <span className="flex min-w-0 items-center gap-1">
              <span className="shrink-0 font-semibold">{name}</span>
              <span aria-hidden className="shrink-0 text-muted">·</span>
              <span className="min-w-0 max-w-[22ch] truncate text-muted md:max-w-[40ch]"><bdi>{street}</bdi></span>
            </span>
          ) : <span className="truncate">{t('place.set')}</span>}
          <ChevronDown aria-hidden size={16} className="shrink-0 text-muted" />
        </button>
      </div>

      <div className="flex shrink-0 items-center gap-1">
        {demo && (
          <span className="inline-flex h-8 items-center gap-1 rounded-full border border-watch bg-watch-tint ps-2.5 text-caption font-semibold text-watch">
            <FlaskConical aria-hidden size={14} />
            <span className="hidden sm:inline">{t('demo.badge')}</span><span className="pe-2.5 sm:hidden">{t('demo.short')}</span>
            <button type="button" onClick={() => setDemo(false)} aria-label={t('demo.exit')}
              className="-my-2 hidden size-11 items-center justify-center rounded-full sm:inline-flex"><X aria-hidden size={14} /></button>
          </span>
        )}
        <button type="button" onClick={onLang} aria-label={t('language') + ': ' + lang.toUpperCase()}
          className="inline-flex min-h-11 items-center gap-1 rounded-md px-1.5 text-body-sm font-semibold text-ink hover:bg-surface-2">
          <Languages aria-hidden size={20} /><span className="uppercase">{lang}</span>
        </button>
        {onInstall && (
          <button type="button" onClick={onInstall} className="hidden min-h-11 items-center gap-1.5 rounded-md px-2 text-body-sm font-semibold text-ink hover:bg-surface-2 sm:inline-flex">
            <Download aria-hidden size={20} />{t('install')}
          </button>
        )}
        <IconButton icon={dark ? Sun : Moon} label={t('theme')} aria-pressed={dark} onClick={() => setDark(!dark)} className="max-md:hidden" />
        <IconButton icon={Menu} label={t('nav.more')} onClick={onMore} className="md:hidden" />
      </div>
    </header>
  )
}
