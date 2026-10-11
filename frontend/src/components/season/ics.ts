const pad = (n: number) => String(n).padStart(2, '0')
const ymd = (d: Date) => `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}`
const addDays = (d: Date, n: number) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + n))
const esc = (s: string) => s.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n')

/** RFC 5545 3.1: fold content lines longer than 75 octets (UTF-8) with CRLF + space; never split a character. */
export function fold(line: string): string {
  const enc = new TextEncoder()
  const out: string[] = []
  let cur = '', n = 0, limit = 75
  for (const ch of line) {
    const b = enc.encode(ch).length
    if (n + b > limit) { out.push(cur); cur = ' '; n = 1; limit = 75 }
    cur += ch; n += b
  }
  out.push(cur)
  return out.join('\r\n')
}
export const icsEscape = esc

export interface SeasonText { start: string; startD: string; ins: string; insD: string; bag: string; bagD: string; stear: string; stearD: string; monthly: string; monthlyD: string }

/** Next June 1 (hurricane season start) on or after `now`. */
export function nextSeasonStart(now = new Date()): Date {
  const y = now.getUTCFullYear()
  const d = new Date(Date.UTC(y, 5, 1))
  return d.getTime() >= Date.UTC(y, now.getUTCMonth(), now.getUTCDate()) ? d : new Date(Date.UTC(y + 1, 5, 1))
}

export function seasonEvents(tx: SeasonText, now = new Date()) {
  const s = nextSeasonStart(now)
  const firstOfNext = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1))
  return [
    { id: 'insurance', date: addDays(s, -45), summary: tx.ins, desc: tx.insD }, // >= 30 days: flood policies have a 30-day wait
    { id: 'stear', date: addDays(s, -31), summary: tx.stear, desc: tx.stearD },
    { id: 'bag', date: addDays(s, -14), summary: tx.bag, desc: tx.bagD },
    { id: 'start', date: s, summary: tx.start, desc: tx.startD },
    { id: 'monthly', date: firstOfNext, summary: tx.monthly, desc: tx.monthlyD, rrule: 'FREQ=MONTHLY' },
  ]
}

export function buildIcs(tx: SeasonText, now = new Date()): string {
  const stamp = now.toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z'
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//FloodReady Houston//Storm season//EN', 'CALSCALE:GREGORIAN']
  for (const e of seasonEvents(tx, now)) {
    lines.push('BEGIN:VEVENT', `UID:floodready-season-${e.id}-${ymd(e.date)}@floodready.local`, `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${ymd(e.date)}`, `DTEND;VALUE=DATE:${ymd(addDays(e.date, 1))}`,
      ...(e.rrule ? [`RRULE:${e.rrule}`] : []),
      `SUMMARY:${esc(e.summary)}`, `DESCRIPTION:${esc(e.desc)}`,
      'BEGIN:VALARM', 'ACTION:DISPLAY', `DESCRIPTION:${esc(e.summary)}`, 'TRIGGER:-PT0M', 'END:VALARM', 'END:VEVENT')
  }
  lines.push('END:VCALENDAR')
  return lines.map(fold).join('\r\n') + '\r\n'
}
