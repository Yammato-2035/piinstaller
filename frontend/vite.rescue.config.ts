import path from 'path';
import { fileURLToPath } from 'url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import pkg from './package.json';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  base: './',
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version || '0.0.0'),
    __SETUPHELFER_RESCUE_UI__: JSON.stringify(true),
  },
  publicDir: path.resolve(__dirname, '../assets/rescue'),
  build: {
    outDir: path.resolve(__dirname, '../build/rescue/ui'),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'rescue.html'),
    },
  },
});
