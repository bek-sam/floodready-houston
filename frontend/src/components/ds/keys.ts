import type { KeyboardEvent } from 'react'

/** Arrow/Home/End navigation for tablists and radiogroups. Returns the next index or null. */
export function rovingIndex(e: KeyboardEvent, i: number, n: number): number | null {
  const rtl = document.documentElement.dir === 'rtl'
  const next = rtl ? 'ArrowLeft' : 'ArrowRight', prev = rtl ? 'ArrowRight' : 'ArrowLeft'
  if (e.key === next || e.key === 'ArrowDown') return (i + 1) % n
  if (e.key === prev || e.key === 'ArrowUp') return (i - 1 + n) % n
  if (e.key === 'Home') return 0
  if (e.key === 'End') return n - 1
  return null
}
