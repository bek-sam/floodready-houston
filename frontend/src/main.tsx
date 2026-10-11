import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import { toast } from './components/ds/Toast'
import { tr } from './i18n'
import { initEasy } from './components/easyread/easyRead'

initEasy()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

function showUpdateToast() {
  let lang = 'en'
  try { lang = localStorage.getItem('lang') || 'en' } catch { /* ignore */ }
  toast({ id: 'sw-update', message: tr(lang, 'shell.update'), action: { label: tr(lang, 'shell.reload'), onClick: () => location.reload() }, sticky: true })
}

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  const hadController = !!navigator.serviceWorker.controller
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then((r) => { r.update().catch(() => {}) }).catch(() => { /* offline support is optional */ })
  })
  // skipWaiting + clients.claim: a controller change after the first visit means a new build took over.
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (hadController) showUpdateToast() })
}
