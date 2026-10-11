import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, type Plugin } from 'vite'
import { readFileSync, writeFileSync, readdirSync } from 'node:fs'

// Stamp the service worker cache names with a per-build id so each deploy gets fresh caches.
const swVersion = (): Plugin => ({
  name: 'sw-version',
  apply: 'build',
  closeBundle() {
    try {
      const f = 'dist/sw.js'
      const assets = readdirSync('dist/assets').map((n) => '/assets/' + n)
      writeFileSync(f, readFileSync(f, 'utf8').replace('__BUILD__', Date.now().toString(36))
        .replace('const ASSETS = []', 'const ASSETS = ' + JSON.stringify(assets)))
    } catch { /* dist/sw.js missing: ignore */ }
  },
})

export default defineConfig({
  plugins: [react(), tailwindcss(), swVersion()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'leaflet', test: /node_modules[\\/](leaflet|react-leaflet|@react-leaflet)[\\/]/, priority: 20 },
            { name: 'qrcode', test: /node_modules[\\/]qrcode[\\/]/, priority: 20 },
          ],
        },
      },
    },
  },
  preview: { port: 4173, proxy: { '/api': 'http://localhost:8000' } },
  server: { port: 5173, proxy: { '/api/live': { target: 'ws://localhost:8000', ws: true }, '/api': 'http://localhost:8000' } },
})
