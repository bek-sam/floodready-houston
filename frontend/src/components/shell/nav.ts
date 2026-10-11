import { BellRing, BookOpen, History, House, Landmark, LifeBuoy, Scale, MessageCircleQuestion, Presentation, Route, Settings, ShieldCheck, type LucideIcon } from 'lucide-react'

export interface NavItem { id: string; icon: LucideIcon }
/** Primary destinations (mobile bottom bar: exactly 5). */
export const PRIMARY: NavItem[] = [
  { id: 'home', icon: House }, { id: 'alerts', icon: BellRing }, { id: 'drive', icon: Route },
  { id: 'prepare', icon: ShieldCheck }, { id: 'ask', icon: MessageCircleQuestion },
]
/** Secondary destinations ("More"). Judge only shows in demo mode. */
export const SECONDARY: NavItem[] = [
  { id: 'replay', icon: History }, { id: 'recover', icon: LifeBuoy }, { id: 'civic', icon: Landmark }, { id: 'compare', icon: Scale },
  { id: 'settings', icon: Settings }, { id: 'about', icon: BookOpen },
]
export const JUDGE: NavItem = { id: 'judge', icon: Presentation }

/** Old hashes that still resolve. */
export const ALIASES: Record<string, string> = { watch: 'alerts', risk: 'home', '': 'home' }

/** Parse location.hash: "#prepare/medical" -> { route: "prepare", sub: "medical" }. */
export function parseHash(hash = location.hash): { route: string; sub: string | null } {
  const [r, ...rest] = decodeURIComponent(hash.replace(/^#\/?/, '')).split('/')
  return { route: ALIASES[r] ?? r, sub: rest.join('/') || null }
}
