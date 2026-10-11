import { useApp } from '../ctx'
import { ArrowRight } from 'lucide-react'
import EmbedSnippet from '../components/share/EmbedSnippet'
import { Card, PageHeader, SourceLink } from '../components/ds'

// Same list as README "Data sources".
const SOURCES: [string, string][] = [
  ['FEMA National Flood Hazard Layer', 'https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28'],
  ['NWS alerts', 'https://api.weather.gov'],
  ['NOAA National Water Prediction Service', 'https://api.water.noaa.gov/nwps/v1/'],
  ['USGS water data (OGC API)', 'https://api.waterdata.usgs.gov/ogcapi/v0/'],
  ['USGS elevation (EPQS)', 'https://epqs.nationalmap.gov/v1/json'],
  ['City of Houston Harvey inundation', 'https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4'],
  ['HCFCD bond program', 'https://www.hcfcd.org/2018-bond-program/bond-program-project-list'],
  ['US Census geocoder', 'https://geocoding.geo.census.gov/geocoder/'],
  ['OSRM routing (demo server)', 'https://router.project-osrm.org'],
  ['Open-Meteo', 'https://open-meteo.com'],
  ['TranStar flood sensors (sample)', 'https://traffic.houstontranstar.org/api/roadwayfloodwarning_sample.json'],
]

export default function About() {
  const { t } = useApp()
  return (
    <div className="space-y-6">
      <PageHeader title={t('nav.about')} subtitle={t('about.sub')} />
      <Card title={t('about.whatTitle')}>
        <p className="text-body">{t('about.what')}</p>
      </Card>
      <Card title={t('p29.demo.h')}>
        <p className="mb-3 text-body-sm text-muted">{t('p29.demo.d')}</p>
        <a className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-brand px-4 font-semibold text-white no-underline dark:text-bg" href="/?demo=1#drive">{t('p29.demo.btn')} <ArrowRight aria-hidden size={16} /></a>
      </Card>
      <Card title={t('about.notOfficialTitle')} tone="watch">
        <p className="text-body">{t('about.notOfficial')}</p>
      </Card>
      <Card title={t('about.sourcesTitle')}>
        <ul className="divide-y divide-line">
          {SOURCES.map(([name, url]) => (
            <li key={url} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-2.5">
              <span className="text-body-sm text-ink">{name}</span>
              <SourceLink href={url} />
            </li>
          ))}
        </ul>
      </Card>
      <a href="#status" className="flex min-h-14 items-center gap-3 rounded-lg border border-line bg-surface px-4 py-2 shadow-card hover:bg-surface-2/60">
        <span className="min-w-0 flex-1"><span className="block text-h3 text-ink">{t('p9.status.link')}</span><span className="block text-caption text-muted">{t('p9.status.link.d')}</span></span>
        <ArrowRight aria-hidden size={20} className="shrink-0 text-muted rtl:rotate-180" />
      </a>
      <EmbedSnippet />
      <Card title={t('about.aiTitle')}>
        <p className="text-body">{t('about.ai')}</p>
      </Card>
      <Card title={t('about.privacyTitle')}>
        <p className="text-body">{t('about.privacy')}</p>
      </Card>
    </div>
  )
}
