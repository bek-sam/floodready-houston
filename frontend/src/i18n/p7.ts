// P7 strings: 3D storm replay. en is the reference; es keeps parity.
type Dict = Record<string, string>
export const en: Dict = {
  'p7.view': 'Map view', 'p7.view2d': '2D', 'p7.view3d': '3D',
  'p7.disclaimer': 'Illustrative water level based on real gauge readings — not a flood model.',
  'p7.fly': 'Fly to my place', 'p7.noPlace': 'Save My place to fly there',
  'p7.orbit': 'Auto-orbit while playing', 'p7.loading': 'Loading 3D map…',
  'p7.nowebgl': 'Your browser or device cannot show the 3D view (WebGL is unavailable). Use the 2D map instead.',
  'p7.back2d': 'Back to 2D map', 'p7.label': '3D storm replay map',
  'p7.extentNote': 'Blue areas: City of Houston Harvey flood extent. Columns: river gauges colored by flood stage.',
  'p7.noExtent': 'Harvey extent data is not available; showing a zone around each gauge.',
  'p7.err': 'The 3D map could not load. Use the 2D map instead.',
}
export const es: Dict = {
  'p7.view': 'Vista del mapa', 'p7.view2d': '2D', 'p7.view3d': '3D',
  'p7.disclaimer': 'Nivel de agua ilustrativo basado en lecturas reales de medidores; no es un modelo de inundación.',
  'p7.fly': 'Ir a mi lugar', 'p7.noPlace': 'Guarda Mi lugar para ir allí',
  'p7.orbit': 'Órbita automática al reproducir', 'p7.loading': 'Cargando mapa 3D…',
  'p7.nowebgl': 'Tu navegador o dispositivo no puede mostrar la vista 3D (WebGL no está disponible). Usa el mapa 2D.',
  'p7.back2d': 'Volver al mapa 2D', 'p7.label': 'Mapa 3D de la repetición de la tormenta',
  'p7.extentNote': 'Áreas azules: extensión de la inundación de Harvey en la ciudad de Houston. Columnas: medidores de ríos por nivel de inundación.',
  'p7.noExtent': 'No hay datos de la extensión de Harvey; se muestra una zona alrededor de cada medidor.',
  'p7.err': 'No se pudo cargar el mapa 3D. Usa el mapa 2D.',
}
