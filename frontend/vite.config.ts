import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy-Ziel: Standard localhost. Bei Remote-Backend z.B. VITE_PROXY_TARGET=http://192.168.1.10:8000
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
})
