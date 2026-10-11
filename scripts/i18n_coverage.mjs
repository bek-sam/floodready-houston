// Prints missing-key counts per language vs English. Run: node scripts/i18n_coverage.mjs [--list]
import { createRequire } from 'node:module'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
const here = dirname(fileURLToPath(import.meta.url))
const require = createRequire(join(here, '..', 'frontend', 'package.json'))
const jiti = require('jiti').createJiti(import.meta.url)
const { dicts } = await jiti.import(join(here, '..', 'frontend', 'src', 'i18n.ts'))
const keys = Object.keys(dicts.en)
let bad = 0
for (const l of Object.keys(dicts)) {
  const miss = keys.filter((k) => !(k in dicts[l]))
  console.log(`${l}: ${miss.length} missing of ${keys.length}`)
  if (process.argv.includes('--list')) miss.forEach((k) => console.log('  ' + k))
  bad += miss.length
}
process.exit(bad ? 1 : 0)
