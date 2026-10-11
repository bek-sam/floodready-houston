import { useApp } from '../../ctx'
import { useDemoMode } from '../../state/place'
import { Lockup } from '../brand/Logo'
import { JUDGE, PRIMARY, SECONDARY, type NavItem } from './nav'

function Item({ item: { id, icon: Icon }, route }: { item: NavItem; route: string }) {
  const { t } = useApp()
  const on = route === id
  return (
    <li>
      <a href={'#' + id} aria-current={on ? 'page' : undefined}
        className={`relative flex min-h-11 items-center gap-3 rounded-[10px] px-3 text-[15px] font-medium transition-colors duration-150 ${on ? 'bg-brand-tint text-brand' : 'text-ink hover:bg-surface-2'}`}>
        {on && <span aria-hidden className="absolute inset-y-2 start-0 w-[3px] rounded-full bg-brand" />}
        <Icon aria-hidden size={20} className="shrink-0" />
        <span className="min-w-0 truncate">{t('nav.' + id)}</span>
      </a>
    </li>
  )
}

/** Desktop sidebar (240px): primary group, then "More". */
export function Sidebar({ route, logoProps }: { route: string; logoProps: React.AnchorHTMLAttributes<HTMLAnchorElement> }) {
  const { t } = useApp()
  const { demo } = useDemoMode()
  const more = demo ? [...SECONDARY, JUDGE] : SECONDARY
  return (
    <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col overflow-y-auto border-e border-line bg-surface md:flex">
      <div className="flex h-14 shrink-0 items-center px-4">
        <a href="#home" aria-label={t('app') + ', ' + t('nav.home')} className="rounded-md" {...logoProps}><Lockup /></a>
      </div>
      <nav aria-label={t('nav.main')} className="flex-1 px-3 pb-4">
        <ul className="space-y-0.5">{PRIMARY.map((x) => <Item key={x.id} item={x} route={route} />)}</ul>
        <p className="mb-1 mt-6 px-3 text-overline uppercase text-muted">{t('nav.more')}</p>
        <ul className="space-y-0.5">{more.map((x) => <Item key={x.id} item={x} route={route} />)}</ul>
      </nav>
    </aside>
  )
}
