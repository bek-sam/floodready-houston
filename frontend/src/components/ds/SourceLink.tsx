import { ExternalLink } from 'lucide-react'
import { useApp } from '../../ctx'

const HOSTS: [RegExp, string][] = [
  [/geogimsms\.houstontx\.gov$/, 'City of Houston'],
  [/houstontx\.gov$/, 'City of Houston'],
  [/hazards\.fema\.gov$/, 'FEMA'],
  [/(^|\.)weather\.gov$/, 'National Weather Service'],
  [/wpc\.ncep\.noaa\.gov$/, 'NOAA WPC'],
  [/^(www\.)?fema\.gov$/, 'OpenFEMA'],
  [/waterdata\.usgs\.gov$/, 'USGS'],
  [/usgs\.gov$/, 'USGS'],
  [/water\.noaa\.gov$/, 'NOAA'],
  [/hcfcd\.org$/, 'HCFCD'],
  [/communityimpact\.com$/, 'Community Impact'],
  [/reduceflooding\.com$/, 'ReduceFlooding.com'],
]
/** Friendly source name from a URL ("FEMA", "NOAA WPC", ...), falling back to the hostname. */
export function sourceName(href: string): string {
  let host = href
  try { host = new URL(href).hostname.replace(/^www\./, '') } catch { return href }
  return HOSTS.find(([re]) => re.test(host))?.[1] ?? host
}

/** Inline source link with a friendly label. Opens in a new tab. Replaces SrcLink. */
export function SourceLink({ href, label, className = '' }: { href?: string | null; label?: string; className?: string }) {
  const { t } = useApp()
  if (!href) return null
  return (
    <>
      {' '}
      <a href={href} target="_blank" rel="noreferrer"
        className={`inline-flex items-center gap-1 text-caption font-medium text-brand underline underline-offset-2 hover:text-brand-strong ${className}`}>
        {label ?? sourceName(href)}
        <ExternalLink aria-hidden size={12} className="shrink-0" />
        <span className="sr-only"> ({t('ds.newTab')})</span>
      </a>
    </>
  )
}
