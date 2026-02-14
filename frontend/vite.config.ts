import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Proxy-Ziel: Standard localhost. Bei Remote-Backend z.B. VITE_PROXY_TARGET=http://192.168.1.10:8000
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'
const isTauriEnv = !!process.env.TAURI_ENV_PLATFORM

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: isTauriEnv ? {} : { 'tauri-plugin-screenshots-api': path.resolve(__dirname, 'src/lib/tauri-screenshots-stub.ts') },
  },
  server: {
    port: 3001,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        configure: (proxy) => {
          let lastLog = 0
          proxy.on('error', (err: NodeJS.ErrnoException, _req, res) => {
            if (err?.code === 'ECONNREFUSED' && Date.now() - lastLog > 10000) {
              lastLog = Date.now()
              console.warn('[vite] Backend unter %s nicht erreichbar. Backend starten: ./start-backend.sh (im Projektroot)', proxyTarget)
            }
            if (res && !res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'application/json' })
              res.end(JSON.stringify({ error: 'Backend nicht erreichbar' }))
            }
          })
        },
      },
    },
  },
})
