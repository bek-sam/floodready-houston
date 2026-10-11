import { useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { Printer, X } from 'lucide-react'
import { useApp } from '../../ctx'
import { Button } from '../ds'

const CSS = `@page{size:letter;margin:0.5in}
@media print{body *{visibility:hidden!important}.fr-poster,.fr-poster *{visibility:visible!important}
.fr-poster{position:absolute;left:0;top:0;width:100%;border:0!important;color:#000!important;background:#fff!important}.fr-noprint{display:none!important}}`

export const posterUrl = (lat: number, lon: number) => `${location.origin}/#drive/to=${lat.toFixed(5)},${lon.toFixed(5)}`

export default function PosterSheet({ name, lat, lon, onClose }: { name: string; lat: number; lon: number; onClose: () => void }) {
  const { t } = useApp()
  const [svg, setSvg] = useState('')
  const url = posterUrl(lat, lon)
  useEffect(() => { QRCode.toString(url, { type: 'svg', margin: 1, color: { dark: '#000000', light: '#ffffff' } }).then(setSvg).catch(() => setSvg('')) }, [url])
  useEffect(() => { const f = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; addEventListener('keydown', f); return () => removeEventListener('keydown', f) }, [onClose])
  return (
    <div role="dialog" aria-modal="true" aria-label={t('poster.h')} className="fixed inset-0 z-50 overflow-auto bg-bg p-4">
      <style>{CSS}</style>
      <div className="fr-noprint mx-auto mb-3 flex max-w-[8.5in] justify-between gap-2">
        <Button variant="primary" icon={Printer} onClick={() => window.print()}>{t('poster.print')}</Button>
        <Button variant="secondary" icon={X} onClick={onClose}>{t('poster.close')}</Button>
      </div>
      <div className="fr-poster mx-auto max-w-[8.5in] space-y-6 rounded-lg border-2 border-black bg-white p-8 text-center text-black">
        <p className="text-2xl font-bold uppercase tracking-wide">{t('poster.title')}</p>
        <h1 className="text-5xl font-extrabold leading-tight">{t('poster.head')}</h1>
        <p className="text-xl">{t('poster.sub')}</p>
        <p className="text-2xl font-semibold">{t('poster.crossing')}: {name}</p>
        {svg && <div className="mx-auto h-64 w-64" aria-label={t('poster.scan')} role="img" dangerouslySetInnerHTML={{ __html: svg }} />}
        <p className="text-xl font-semibold">{t('poster.scan')}</p>
        <p className="break-all text-sm">{url}</p>
        <p className="text-4xl font-extrabold">{t('poster.emerg')}</p>
        <p className="text-sm">{t('poster.src')}</p>
      </div>
    </div>
  )
}
