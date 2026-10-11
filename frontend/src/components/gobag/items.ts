import type { Household } from '../../state/place'

export interface BagItem { id: string; group: 'docs' | 'health' | 'family' | 'basics' | 'plan'; key: string }

/** Personalized go-bag list from the My place household. Item text lives in i18n as `p10.bag.<id>`. */
export function bagItems(h: Household): BagItem[] {
  const a = (group: BagItem['group'], id: string): BagItem => ({ id, group, key: 'p10.bag.' + id })
  const out: BagItem[] = [
    a('docs', 'ids'), a('docs', 'insurance'), a('docs', 'cash'), a('docs', 'usb'),
    a('basics', 'water'), a('basics', 'food'), a('basics', 'flashlight'), a('basics', 'charger'), a('basics', 'radio'), a('basics', 'clothes'), a('basics', 'firstaid'),
    a('plan', 'contacts'), a('plan', 'stear'),
  ]
  const m = h.medical
  out.push(a('health', 'meds'))
  if (m.dialysis) out.push(a('health', 'dialysis'), a('health', 'dialysisCenter'))
  if (m.oxygen) out.push(a('health', 'oxygen'))
  if (m.powerDevice) out.push(a('health', 'powerDevice'))
  if (m.other.trim()) out.push(a('health', 'otherMed'))
  if (h.mobility !== 'none') out.push(a('health', 'mobility'))
  if (h.ages.kids) out.push(a('family', 'kids'), a('family', 'formula'))
  if (h.ages.older) out.push(a('family', 'older'))
  if (h.pets) out.push(a('family', 'pets'))
  if (h.hasCar === false) out.push(a('plan', 'noCar'), a('plan', 'transit311'))
  if (h.renter) out.push(a('docs', 'lease'))
  return out
}
