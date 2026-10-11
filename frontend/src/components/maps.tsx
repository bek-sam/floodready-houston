import { useEffect, type ReactNode } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import type { LatLngBoundsExpression, LatLngExpression } from 'leaflet'
import { HOUSTON } from '../ctx'

function Fit({ bounds }: { bounds?: LatLngBoundsExpression }) {
  const map = useMap()
  useEffect(() => { if (bounds) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 14 }) }, [map, bounds])
  return null
}

export function Map({ children, bounds, center, height = 'h-72 sm:h-96', label, legend, loading }: {
  children?: ReactNode; bounds?: LatLngBoundsExpression; center?: LatLngExpression; height?: string; label: string
  /** Legend row rendered under the map. */
  legend?: ReactNode; loading?: boolean
}) {
  return (
    <div>
    <div className={`${height} relative w-full overflow-hidden rounded-lg border border-line`} role="region" aria-label={label}>
      {loading && <span role="status" aria-label="Loading" className="absolute inset-0 z-[500] flex items-center justify-center bg-surface/60"><span className="size-8 animate-spin rounded-full border-4 border-line border-t-brand" /></span>}
      <MapContainer center={center ?? [HOUSTON.lat, HOUSTON.lon]} zoom={10} className="h-full w-full">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Fit bounds={bounds} />
        {children}
      </MapContainer>
    </div>
    {legend && <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-caption text-muted">{legend}</div>}
    </div>
  )
}
