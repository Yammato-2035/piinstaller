#!/usr/bin/env node
/**
 * Erzeugt Marketing-Screenshots für das WordPress-Theme (website/setuphelfer-theme/assets/screenshots/).
 *
 * Voraussetzung: Vite-Dev-Server läuft (Standard: http://127.0.0.1:3001), z. B.:
 *   cd frontend && npm run dev
 *
 * Optional: Backend auf 127.0.0.1:8000 für Demo-Daten (X-Demo-Mode) – Dashboard/Webserver wirken dann „gefüllter“.
 *
 * Einmalig Chromium für Playwright:
 *   npx playwright install chromium
 */

import { chromium } from 'playwright'
import { mkdir } from 'fs/promises'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'
import http from 'http'

const __dirname = dirname(fileURLToPath(import.meta.url))
const THEME_SCREENSHOTS = join(__dirname, '..', '..', 'website', 'setuphelfer-theme', 'assets', 'screenshots')

const BASE = (process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:3001').replace(/\/$/, '')

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

const shots = [
  { file: 'theme-startscreen.png', path: '/?themeShot=start' },
  { file: 'theme-setup-auswahl.png', path: '/?themeShot=experience' },
  { file: 'theme-modul-webserver.png', path: '/?themeShot=webserver' },
  { file: 'theme-fehlerfall.png', path: '/?themeShot=error' },
  { file: 'theme-dashboard.png', path: '/?themeShot=dashboard' },
]

async function main() {
  if (!(await waitForServer(BASE))) {
    console.error(`Vite nicht erreichbar unter ${BASE}`)
    console.error('Starte z. B.: cd frontend && npm run dev')
    process.exit(1)
  }

  await mkdir(THEME_SCREENSHOTS, { recursive: true })

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  })

  for (const { file, path: p } of shots) {
    const page = await context.newPage()
    const isExperience = p.includes('themeShot=experience')
    await page.addInitScript((experience) => {
      try {
        localStorage.setItem('setuphelfer-ui-locale', 'de')
        if (experience) {
          localStorage.removeItem('pi-installer-first-run-done')
        } else {
          localStorage.setItem('pi-installer-first-run-done', '1')
        }
      } catch {
        /* ignore */
      }
    }, isExperience)

    await page.goto(`${BASE}${p}`, { waitUntil: 'domcontentloaded', timeout: 120000 })
    await waitMs(isExperience ? 3200 : 2800)
    await page.screenshot({ path: join(THEME_SCREENSHOTS, file) })
    await page.close()
    console.log('OK', file)
  }

  await browser.close()
  console.log('Fertig →', THEME_SCREENSHOTS)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
