import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'

// Im Dev-Modus (npm run dev) laufen API und WebSocket über das Backend auf 8237.
export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8237',
      '/ws': { target: 'ws://127.0.0.1:8237', ws: true },
    },
  },
})
