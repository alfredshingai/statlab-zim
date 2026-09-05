import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/datasets': 'http://localhost:8000',
      '/analyses': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/projects': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/ai': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
      '/docs': 'http://localhost:8000',
      '/openapi.json': 'http://localhost:8000',
    },
  },
})
