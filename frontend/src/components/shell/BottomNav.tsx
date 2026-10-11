import { useApp } from '../../ctx'
import { PRIMARY } from './nav'

/** Mobile bottom bar: 5 equal columns, 64px + safe area. */
export function BottomNav({ route }: { route: string }) {
  const { t } = useApp()
  return (
    <nav aria-label={t('nav.main')} className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] md:hidden">
      <ul className="grid h-16 grid-cols-5">
        {PRIMARY.map(({ id, icon: Icon }) => {
          const on = route === id
          return (
            <li key={id} className="min-w-0">
              <a href={'#' + id} aria-current={on ? 'page' : undefined}
                className={`flex h-full flex-col items-center justify-center gap-1 px-0.5 ${on ? 'text-brand' : 'text-muted hover:text-ink'}`}>
                <span className="relative flex h-6 items-center">
                  {on && <span aria-hidden className="absolute -top-2 left-1/2 h-1 w-8 -translate-x-1/2 rounded-full bg-brand" />}
                  <Icon aria-hidden size={22} strokeWidth={on ? 2.25 : 2} />
                </span>
                <span className="max-w-full text-center text-[12px] font-semibold leading-4">{t('nav.' + id)}</span>
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
