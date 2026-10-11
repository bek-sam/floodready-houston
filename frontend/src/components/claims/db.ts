// Offline-first claim photo store (IndexedDB). Everything stays on this device.
export interface ClaimPhoto { id?: number; blob: Blob; ts: number; room: string; note: string }
const DB = 'floodready-claims', STORE = 'photos'

const open = (): Promise<IDBDatabase> => new Promise((res, rej) => {
  if (typeof indexedDB === 'undefined') return rej(new Error('no-idb'))
  const r = indexedDB.open(DB, 1)
  r.onupgradeneeded = () => { r.result.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true }) }
  r.onsuccess = () => res(r.result)
  r.onerror = () => rej(r.error ?? new Error('idb'))
})
async function run<T>(mode: IDBTransactionMode, f: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await open()
  return new Promise<T>((res, rej) => {
    const tx = db.transaction(STORE, mode)
    const rq = f(tx.objectStore(STORE))
    tx.oncomplete = () => { db.close(); res(rq.result) }
    tx.onerror = tx.onabort = () => { db.close(); rej(tx.error ?? new Error('idb')) }
  })
}
export const listPhotos = async (): Promise<ClaimPhoto[]> => ((await run('readonly', (s) => s.getAll() as IDBRequest<ClaimPhoto[]>)) ?? []).sort((a, b) => a.ts - b.ts)
export const addPhoto = (p: ClaimPhoto) => run('readwrite', (s) => s.add(p))
export const updatePhoto = (p: ClaimPhoto) => run('readwrite', (s) => s.put(p))
export const deletePhoto = (id: number) => run('readwrite', (s) => s.delete(id))
export const clearPhotos = () => run('readwrite', (s) => s.clear())

/** Downscale an image to maxPx on its long side (JPEG). Falls back to the original blob on failure. */
export async function shrink(file: Blob, maxPx: number, q = 0.8): Promise<Blob> {
  try {
    const bmp = await createImageBitmap(file)
    const k = Math.min(1, maxPx / Math.max(bmp.width, bmp.height))
    const c = document.createElement('canvas')
    c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k)
    c.getContext('2d')!.drawImage(bmp, 0, 0, c.width, c.height)
    bmp.close?.()
    return await new Promise<Blob>((res) => c.toBlob((b) => res(b ?? file), 'image/jpeg', q))
  } catch { return file }
}
export const toDataUrl = (b: Blob) => new Promise<string>((res) => { const r = new FileReader(); r.onload = () => res(String(r.result)); r.onerror = () => res(''); r.readAsDataURL(b) })
