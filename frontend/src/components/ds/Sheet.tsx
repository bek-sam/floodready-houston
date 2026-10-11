import { useEffect, useId, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { useApp } from '../../ctx'

/**
 * Modal sheet on a native <dialog> (focus trap + Esc).
 * side="bottom": bottom sheet on mobile, right drawer (420px) on desktop. side="right": right drawer everywhere.
 */
export function Sheet({ open, onClose, title, side = 'bottom', children, footer }: {
  open: boolean; onClose: () => void; title: ReactNode; side?: 'bottom' | 'right'; children: ReactNode; footer?: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  const { t } = useApp()
  const tid = useId()
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) { try { d.showModal() } catch { d.setAttribute('open', '') } }
    if (!open && d.open) d.close()
  }, [open])
  const pos = side === 'right'
    ? 'fr-side inset-y-0 end-0 start-auto h-full max-h-none w-[min(420px,100vw)] rounded-s-xl'
    : 'inset-x-0 bottom-0 top-auto max-h-[85vh] w-full rounded-t-xl md:inset-y-0 md:end-0 md:start-auto md:top-0 md:h-full md:max-h-none md:w-[420px] md:rounded-none md:rounded-s-xl'
  return (
    <dialog ref={ref} aria-labelledby={tid} onClose={onClose} onCancel={(e) => { e.preventDefault(); onClose() }}
      onClick={(e) => { if (e.target === ref.current) onClose() }}
      className={`fr-sheet fixed m-0 hidden max-w-none flex-col border-0 bg-surface p-0 text-ink shadow-raised open:flex ${pos}`}>
      {open && <>
        {side === 'bottom' && <span aria-hidden className="mx-auto mt-2 block h-1 w-9 shrink-0 rounded-full bg-line md:hidden" />}
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-line py-1 ps-4 pe-1">
          <h2 id={tid} className="text-h2 text-ink">{title}</h2>
          <button type="button" onClick={onClose} aria-label={t('ds.close')}
            className="inline-flex size-11 items-center justify-center rounded-md text-ink hover:bg-surface-2"><X aria-hidden size={20} /></button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">{children}</div>
        {footer && <div className="shrink-0 border-t border-line p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">{footer}</div>}
      </>}
    </dialog>
  )
}
