import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const BACKEND_URL = 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // `npm run dev:mobile`: HTTPS on the local network, because phone browsers
  // only allow the camera on secure origins. Self-signed certificate.
  const mobile = mode === 'mobile'

  return {
    plugins: [react(), tailwindcss(), mobile && basicSsl()],
    server: {
      host: mobile,
      // Cloudflare quick tunnel (cloudflared tunnel --url http://localhost:5173)
      allowedHosts: ['.trycloudflare.com'],
      // Dev only: forwards backend routes so local development needs no CORS.
      // In production the app calls VITE_API_URL, allowed by the backend's CORS_ORIGINS.
      proxy: {
        '/api': BACKEND_URL,
        '/auth': BACKEND_URL,
        '/health': BACKEND_URL,
      },
    },
  }
})
