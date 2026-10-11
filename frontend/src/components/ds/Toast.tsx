import { useEffect, useSyncExternalStore } from 'react'
import { X } from 'lucide-react'
import { useApp } from '../../ctx'

export interface ToastInput { message: string; action?: { label: string; onClick: () => void }; tone?: 'default' | 'error'; id?: string; sticky?: boolean }
interface ToastItem extends ToastInput { id: string }

let items: ToastItem[] = []
const subs = new Set<() => void>()
const emit = () => subs.forEach((f) => f())
let seq = 0

/** Show a toast from anywhere (also outside React). Returns its id. Errors stay until dismissed; others auto-dismiss after 5s. */
export function toast(input: ToastInput | string): string {
  const t: ToastItem = typeof input === 'string' ? { message: input, id: 't' + ++seq } : { ...input, id: input.id ?? 't' + ++seq }
  items = [...items.filter((x) => x.id !== t.id), t].slice(-3)
  emit()
  return t.id
}
export function dismissToast(id: string) { items = items.filter((x) => x.id !== id); emit() }
export const useToast = () => toast

const subscribe = (f: () => void) => { subs.add(f); return () => { subs.delete(f) } }
const snapshot = () => items

function ToastRow({ item }: { item: ToastItem }) {
  const { t } = useApp()
  useEffect(() => {
    if (item.tone === 'error' || item.sticky) return
    const h = setTimeout(() => dismissToast(item.id), 5000)
    return () => clearTimeout(h)
  }, [item])
  return (
    <div role={item.tone === 'error' ? 'alert' : 'status'}
      className="fr-fade-in pointer-events-auto flex w-full items-center gap-3 rounded-md bg-ink py-2 ps-4 pe-1 text-body-sm text-surface shadow-raised">
      <p className="min-w-0 flex-1 py-1.5">{item.message}</p>
      {item.action && (
        <button type="button" onClick={() => { item.action!.onClick(); dismissToast(item.id) }}
          className="min-h-11 shrink-0 rounded-sm px-3 font-semibold text-surface underline underline-offset-2">{item.action.label}</button>
      )}
      <button type="button" aria-label={t('ds.close')} onClick={() => dismissToast(item.id)}
        className="inline-flex size-11 shrink-0 items-center justify-center rounded-sm"><X aria-hidden size={18} /></button>
    </div>
  )
}

/** Render once at the app root. Bottom-center, above the mobile tab bar. */
export function Toaster() {
  const list = useSyncExternalStore(subscribe, snapshot, snapshot)
  if (!list.length) return null
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-[calc(80px+env(safe-area-inset-bottom))] z-[1100] flex flex-col items-center gap-2 px-4 md:bottom-6">
      <div className="flex w-full max-w-[420px] flex-col gap-2">{list.map((x) => <ToastRow key={x.id} item={x} />)}</div>
    </div>
  )
}
