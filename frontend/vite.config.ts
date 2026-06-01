import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import pkg from './package.json'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Proxy-Ziel: Standard localhost. Bei Remote-Backend z.B. VITE_PROXY_TARGET=http://192.168.1.10:8000
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'
const isTauriEnv = !!process.env.TAURI_ENV_PLATFORM
/** Nur beim gebündelten Tauri-Build: relative asset-URLs; `tauri dev` bleibt bei `/` (Vite auf localhost). */
const isTauriProductionBuild =
  isTauriEnv && process.env.NODE_ENV === 'production'

const apiProxy = {
  '/api': {
    target: proxyTarget,
    changeOrigin: true,
    configure: (proxy) => {
      let lastLog = 0
      proxy.on('error', (err: NodeJS.ErrnoException, _req, res) => {
        if (err?.code === 'ECONNREFUSED' && Date.now() - lastLog > 10000) {
          lastLog = Date.now()
          console.warn(
            '[vite] Backend unter %s nicht erreichbar. Backend starten: ./start-backend.sh (im Projektroot)',
            proxyTarget,
          )
        }
        if (res && !res.headersSent) {
          res.writeHead(502, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'Backend nicht erreichbar' }))
        }
      })
    },
  },
}

/** Unter /opt: Cache nach /tmp legen (Service-User, kein Schreiben in node_modules/.vite nötig). */
const viteCacheDir =
  process.env.PI_INSTALLER_VITE_CACHE_DIR ||
  path.resolve(__dirname, 'node_modules/.vite')

const frontendBuildProfile =
  process.env.SETUPHELFER_FRONTEND_BUILD_PROFILE ||
  process.env.VITE_SETUPHELFER_FRONTEND_BUILD_PROFILE ||
  'release'
const labLike = frontendBuildProfile === 'developer' || frontendBuildProfile === 'local_lab'
const devControlUiEnabled = labLike
const devDiagnosticsUiEnabled =
  labLike || frontendBuildProfile === 'rescue_lab'
const fleetSessionsUiEnabled =
  labLike || frontendBuildProfile === 'rescue_lab'
const rescueRemoteUiEnabled =
  frontendBuildProfile === 'local_lab' || frontendBuildProfile === 'rescue_lab'
const buildId =
  process.env.SETUPHELFER_BUILD_ID ||
  process.env.VITE_SETUPHELFER_BUILD_ID ||
  `${Date.now()}`

export default defineConfig({
  cacheDir: viteCacheDir,
  base: isTauriProductionBuild ? './' : '/',
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version || '0.0.0'),
    __SETUPHELFER_FRONTEND_BUILD_PROFILE__: JSON.stringify(frontendBuildProfile),
    __SETUPHELFER_DEV_CONTROL_UI_ENABLED__: devControlUiEnabled,
    __SETUPHELFER_DEV_DIAGNOSTICS_UI_ENABLED__: devDiagnosticsUiEnabled,
    __SETUPHELFER_FLEET_SESSIONS_UI_ENABLED__: fleetSessionsUiEnabled,
    __SETUPHELFER_RESCUE_REMOTE_UI_ENABLED__: rescueRemoteUiEnabled,
    __SETUPHELFER_BUILD_ID__: JSON.stringify(buildId),
  },
  resolve: {
    alias: isTauriEnv ? {} : { 'tauri-plugin-screenshots-api': path.resolve(__dirname, 'src/lib/tauri-screenshots-stub.ts') },
  },
  server: {
    port: 3001,
    host: '0.0.0.0',
    proxy: { ...apiProxy },
  },
  /** Wichtig: `vite preview` (ohne diesen Block) leitet /api nicht weiter → 404 auf alle API-Calls. */
  preview: {
    port: 3001,
    host: '0.0.0.0',
    proxy: { ...apiProxy },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
    passWithNoTests: true,
  },
})
