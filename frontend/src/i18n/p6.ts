// AI-reviewed translations — pending review by native-speaking community partners.
// P6 strings (owned by the P6 builder). en is the reference; es must keep parity.
type Dict = Record<string, string>
export const en: Dict = {
  // Plain language instead of "SFHA" jargon.
  'c11.ins.sfha': 'FEMA calls this a high-risk flood zone, so lenders usually require flood insurance.',
  'p6.drive.start': '{label}: start', 'p6.drive.end': '{label}: end',
}
export const es: Dict = {
  'c11.ins.sfha': 'FEMA la considera una zona de alto riesgo de inundación, por eso los prestamistas suelen exigir seguro contra inundaciones.',
  'p6.drive.start': '{label}: inicio', 'p6.drive.end': '{label}: final',
  // Replay storm names and summaries (the server sends English; same facts and numbers).
  'p6.ev.harvey-2017.name': 'Huracán Harvey',
  'p6.ev.harvey-2017.summary': 'Harvey inundó 154,170 viviendas del condado de Harris; solo el 36% tenía seguro y casi la mitad estaba fuera de las planicies de inundación de 100 y 500 años. 36 muertes en el condado de Harris.',
  'p6.ev.taxday-2016.name': 'Inundación del Tax Day',
  'p6.ev.taxday-2016.summary': 'De 12 a 16 pulgadas de lluvia en 12 horas; unas 9,820 estructuras inundadas y 7 muertes en el condado de Harris.',
  'p6.ev.imelda-2019.name': 'Tormenta tropical Imelda',
  'p6.ev.imelda-2019.summary': 'Unas 8,200 viviendas inundadas en 4 condados; 2 muertes en el condado de Harris.',
  'p6.ev.june-2026.name': 'Inundación repentina de junio de 2026',
  'p6.ev.june-2026.summary': 'Inundaciones en el centro el 15 de junio de 2026: autos atrapados bajo puentes, UH-Downtown cerrado y declaración de desastre estatal.',
}
