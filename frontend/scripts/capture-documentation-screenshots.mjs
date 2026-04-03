#!/usr/bin/env node
/**
 * Dokumentations-Screenshots nach public/docs/screenshots/doc-*.png
 *
 * Voraussetzung: Frontend erreichbar (Vite z. B. :3001 oder :5173), optional Backend für volle Inhalte.
 *   export DOCS_SCREENSHOT_BASE=http://127.0.0.1:5173
 *   cd frontend && npm run screenshots:docs
 *
 * Einmalig: npx playwright install chromium
 *
 * Entfernt veraltete Dateien screenshot-*.png im Zielordner (alte Namensgebung).
 */

import { chromium } from 'playwright'
import { mkdir, readdir, unlink } from 'fs/promises'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'
import http from 'http'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = join(__dirname, '..', 'public', 'docs', 'screenshots')
const BASE = (process.env.DOCS_SCREENSHOT_BASE || process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:3001').replace(
  /\/$/,
  '',
)

function waitMs(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

async function waitForServer(url, timeoutMs = 90000) {
  const u = new URL(url)
  const port = u.port ? Number(u.port) : u.protocol === 'https:' ? 443 : 80
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.request(
          { hostname: u.hostname, port, path: '/', method: 'GET', timeout: 2500 },
          (res) => {
            res.resume()
            resolve()
          },
        )
        req.on('error', reject)
        req.on('timeout', () => {
          req.destroy()
          reject(new Error('timeout'))
        })
        req.end()
      })
      return true
    } catch {
      await waitMs(400)
    }
  }
  return false
}

async function removeLegacyScreenshots() {
  const files = await readdir(OUT_DIR).catch(() => [])
  for (const f of files) {
    if (f.startsWith('screenshot-') && f.endsWith('.png')) {
      await unlink(join(OUT_DIR, f)).catch(() => {})
      console.log('Alte Datei entfernt:', f)
    }
  }
}

/** Seiten inkl. page= Query wie in App.tsx */
const PAGE_SHOTS = [
  ['doc-dashboard.png', 'dashboard'],
  ['doc-wizard.png', 'wizard'],
  ['doc-presets.png', 'presets'],
  ['doc-security.png', 'security'],
  ['doc-users.png', 'users'],
  ['doc-devenv.png', 'devenv'],
  ['doc-webserver.png', 'webserver'],
  ['doc-mailserver.png', 'mailserver'],
  ['doc-nas.png', 'nas'],
  ['doc-homeautomation.png', 'homeautomation'],
  ['doc-musicbox.png', 'musicbox'],
  ['doc-kino-streaming.png', 'kino-streaming'],
  ['doc-learning.png', 'learning'],
  ['doc-monitoring.png', 'monitoring'],
  ['doc-backup.png', 'backup'],
  ['doc-control-center.png', 'control-center'],
  ['doc-periphery-scan.png', 'periphery-scan'],
  ['doc-raspberry-pi-config.png', 'raspberry-pi-config'],
  ['doc-documentation.png', 'documentation'],
]

async function main() {
  if (!(await waitForServer(BASE))) {
    console.error(`Frontend nicht erreichbar unter ${BASE}`)
    console.error('Setze DOCS_SCREENSHOT_BASE, z. B. http://127.0.0.1:5173')
    process.exit(1)
  }

  await mkdir(OUT_DIR, { recursive: true })
  await removeLegacyScreenshots()

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1360, height: 860 },
    deviceScaleFactor: 1,
  })

  const bootstrapLocalStorage = () => {
    try {
      localStorage.setItem('pi-installer-first-run-done', '1')
      localStorage.setItem('setuphelfer-ui-locale', 'de')
    } catch {
      /* ignore */
    }
  }

  for (const [file, pageId] of PAGE_SHOTS) {
    const page = await context.newPage()
    await page.addInitScript(bootstrapLocalStorage)
    const url = `${BASE}/?page=${encodeURIComponent(pageId)}`
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 })
    await waitMs(2200)
    await page.screenshot({ path: join(OUT_DIR, file), fullPage: false })
    await page.close()
    console.log('OK', file)
  }

  // Einstellungen: Tab „Allgemein“ (Standard)
  {
    const page = await context.newPage()
    await page.addInitScript(bootstrapLocalStorage)
    await page.goto(`${BASE}/?page=settings`, { waitUntil: 'domcontentloaded', timeout: 120000 })
    await waitMs(2000)
    await page.screenshot({ path: join(OUT_DIR, 'doc-settings-general.png'), fullPage: false })
    await page.close()
    console.log('OK doc-settings-general.png')
  }

  // Einstellungen: Tab Cloud-Backup (deutscher Button-Text)
  {
    const page = await context.newPage()
    await page.addInitScript(bootstrapLocalStorage)
    await page.goto(`${BASE}/?page=settings`, { waitUntil: 'domcontentloaded', timeout: 120000 })
    await waitMs(800)
    const cloudTab = page.getByRole('button', { name: /Cloud-Backup/i })
    if (await cloudTab.count()) {
      await cloudTab.first().click()
      await waitMs(1200)
    } else {
      const alt = page.getByRole('button', { name: /Cloud/i })
      if (await alt.count()) await alt.first().click()
      await waitMs(1200)
    }
    await page.screenshot({ path: join(OUT_DIR, 'doc-settings-cloud.png'), fullPage: false })
    await page.close()
    console.log('OK doc-settings-cloud.png')
  }

  await browser.close()
  console.log('Fertig →', OUT_DIR)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
