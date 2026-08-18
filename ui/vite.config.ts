import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_TARGET = process.env.FEDOTWEB_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Keeps the browser on a single origin during development, so the
      // WebSocket used for run progress needs no special-casing.
      '/api': { target: API_TARGET, changeOrigin: true, ws: true },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        // The canvas and the charts are each only needed on one screen, so
        // splitting them keeps the first paint off the critical path.
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          flow: ['@xyflow/react', '@dagrejs/dagre'],
          charts: ['recharts'],
        },
      },
    },
  },
})
