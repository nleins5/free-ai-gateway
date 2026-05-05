import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Listen on all network interfaces
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:8000',
        ws: true,
        secure: false
      }
    }
  }
})
