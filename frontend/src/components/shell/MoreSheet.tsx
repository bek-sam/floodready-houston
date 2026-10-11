import { Download, FlaskConical, Moon, Sun } from 'lucide-react'
import { useApp } from '../../ctx'
import { useDemoMode } from '../../state/place'
import { Sheet, Switch } from '../ds'
import { JUDGE, SECONDARY } from './nav'

export function MoreSheet({ open, onClose, route, onInstall }: { open: boolean; onClose: () => void; route: string; onInstall?: () => void }) {
  const { t, dark, setDark } = useApp()
  const { demo, setDemo } = useDemoMode()
  const items = demo ? [...SECONDARY, JUDGE] : SECONDARY
  return (
    <Sheet open={open} onClose={onClose} title={t('nav.more')} side="right">
      <nav aria-label={t('nav.more')}>
        <ul className="space-y-1">
          {items.map(({ id, icon: Icon }) => (
            <li key={id}>
              <a href={'#' + id} onClick={onClose} aria-current={route === id ? 'page' : undefined}
                className={`flex min-h-12 items-center gap-3 rounded-[10px] px-3 text-[15px] font-medium ${route === id ? 'bg-brand-tint text-brand' : 'text-ink hover:bg-surface-2'}`}>
                <Icon aria-hidden size={20} />{t('nav.' + id)}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="mt-4 border-t border-line pt-3">
        {demo && (
          <button type="button" onClick={() => { setDemo(false); onClose() }}
            className="mb-2 flex min-h-12 w-full items-center gap-3 rounded-[10px] px-3 text-[15px] font-medium text-watch hover:bg-surface-2">
            <FlaskConical aria-hidden size={20} />{t('demo.exit')}
          </button>
        )}
        {onInstall && (
          <button type="button" onClick={() => { onInstall(); onClose() }}
            className="mb-2 flex min-h-12 w-full items-center gap-3 rounded-[10px] px-3 text-[15px] font-medium text-ink hover:bg-surface-2">
            <Download aria-hidden size={20} />{t('install')}
          </button>
        )}
        <Switch label={<span className="inline-flex items-center gap-2">{dark ? <Moon aria-hidden size={18} /> : <Sun aria-hidden size={18} />}{t('settings.dark')}</span>}
          checked={dark} onChange={setDark} />
      </div>
    </Sheet>
  )
}
