import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true, // Usar polling en lugar de file watchers
      interval: 2000,   // Intervalo de 2 segundos para reducir carga
      ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/.vscode/**']
    },
    hmr: {
      clientPort: 443,
      // Remover host específico para evitar binding a IP externa
      overlay: false,
      port: 24678
    },
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '.preview.emergentagent.com',
      '02adb51f-83c2-48e6-b3b0-2ac1480e7852.preview.emergentagent.com'
    ]
  },
  optimizeDeps: {
    include: ['react', 'react-dom'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          icons: ['lucide-react']
        }
      }
    }
  }
})
