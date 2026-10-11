import { useEffect, useState } from 'react'

const KEY = 'floodready.easyread.v1'
export const readEasy = (): boolean => { try { return localStorage.getItem(KEY) === '1' } catch { return false } }
export const applyEasy = (on: boolean) => { try { document.documentElement.classList.toggle('easy-read', on) } catch { /* ignore */ } }
export const setEasy = (on: boolean) => { try { localStorage.setItem(KEY, on ? '1' : '0') } catch { /* ignore */ } applyEasy(on); try { window.dispatchEvent(new Event('floodready:easyread')) } catch { /* ignore */ } }
/** Apply the saved preference on startup (call once at module load). */
export const initEasy = () => applyEasy(readEasy())

export function useEasy(): [boolean, (on: boolean) => void] {
  const [on, setOn] = useState(readEasy)
  useEffect(() => {
    const f = () => setOn(readEasy())
    window.addEventListener('floodready:easyread', f)
    return () => window.removeEventListener('floodready:easyread', f)
  }, [])
  return [on, setEasy]
}
/** Use the plain "easy.<key>" string when easy-read is on and one exists. */
export const easyT = (t: (k: string) => string, key: string, on: boolean) => {
  if (!on) return t(key)
  const v = t('easy.' + key)
  return v === 'easy.' + key ? t(key) : v
}
