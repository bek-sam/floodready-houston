// One semantic level scale used everywhere (docs/ux/redesign-spec.md §5.2).
import { CircleCheck, CircleHelp, Eye, OctagonAlert, TriangleAlert, type LucideIcon } from 'lucide-react'
import type { Status, WatchLevel } from '../api'

export type Level = 'normal' | 'watch' | 'warning' | 'danger' | 'unknown'
export const LEVEL_RANK: Record<Level, number> = { unknown: -1, normal: 0, watch: 1, warning: 2, danger: 3 }

export const LEVEL_ICON: Record<Level, LucideIcon> = {
  normal: CircleCheck, watch: Eye, warning: TriangleAlert, danger: OctagonAlert, unknown: CircleHelp,
}
/** Tailwind classes: text/icon color, tint background, border color. */
export const LEVEL_CLASS: Record<Level, { text: string; bg: string; border: string; borderTop: string }> = {
  normal: { text: 'text-normal', bg: 'bg-normal-tint', border: 'border-normal/40', borderTop: 'border-t-normal' },
  watch: { text: 'text-watch', bg: 'bg-watch-tint', border: 'border-watch/40', borderTop: 'border-t-watch' },
  warning: { text: 'text-warning', bg: 'bg-warning-tint', border: 'border-warning/40', borderTop: 'border-t-warning' },
  danger: { text: 'text-danger', bg: 'bg-danger-tint', border: 'border-danger/40', borderTop: 'border-t-danger' },
  unknown: { text: 'text-muted', bg: 'bg-surface-2', border: 'border-ui/40', borderTop: 'border-t-ui' },
}
/** CSS variable for a level (for Leaflet / SVG, resolve with cssVar()). */
export const LEVEL_VAR: Record<Level, string> = {
  normal: '--normal', watch: '--watch', warning: '--warning', danger: '--danger', unknown: '--muted',
}
export const cssVar = (name: string, fallback = '#4A5868') =>
  (typeof document !== 'undefined' && getComputedStyle(document.documentElement).getPropertyValue(name).trim()) || fallback

/** Gauge NWS category -> level. */
export const gaugeLevel = (s: Status | string | null | undefined): Level =>
  s === 'normal' ? 'normal' : s === 'action' ? 'watch' : s === 'minor' || s === 'moderate' ? 'warning' : s === 'major' ? 'danger' : 'unknown'
/** i18n key for the plain gauge label ("Near flood stage", ...). */
export const gaugeLabelKey = (s: Status | string | null | undefined) =>
  'gauge.' + (['normal', 'action', 'minor', 'moderate', 'major'].includes(String(s)) ? s : 'unknown')

/** /watch/status level -> level. */
export const watchLevel = (w: WatchLevel | string | null | undefined): Level =>
  w === 'ok' ? 'normal' : w === 'watch' ? 'watch' : w === 'warning' ? 'warning' : 'unknown'

/** /route-check verdict -> level + i18n label key. */
export const verdictLevel = (v: string | null | undefined): Level =>
  v === 'safe' ? 'normal' : v === 'caution' ? 'warning' : v === 'avoid' ? 'danger' : 'unknown'
export const verdictLabelKey = (v: string | null | undefined) => 'verdict.' + (v === 'safe' || v === 'caution' || v === 'avoid' ? v : 'unknown')

export type Exposure = 'high' | 'elevated' | 'lower' | 'unknown'
export const exposureLevel = (e: Exposure): Level =>
  e === 'high' ? 'danger' : e === 'elevated' ? 'watch' : e === 'lower' ? 'normal' : 'unknown'
export const exposureLabelKey = (e: Exposure) => 'exposure.' + e

export const maxLevel = (...ls: Level[]): Level => ls.reduce((a, b) => (LEVEL_RANK[b] > LEVEL_RANK[a] ? b : a), 'unknown' as Level)
