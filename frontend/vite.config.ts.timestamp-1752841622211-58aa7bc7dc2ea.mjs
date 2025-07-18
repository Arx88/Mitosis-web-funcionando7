// vite.config.ts
import { defineConfig } from "file:///app/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///app/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3e3,
    watch: {
      usePolling: true,
      // Usar polling en lugar de file watchers
      interval: 2e3,
      // Intervalo de 2 segundos para reducir carga
      ignored: ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/.vscode/**"]
    },
    hmr: {
      clientPort: 443,
      // Remover host específico para evitar binding a IP externa
      overlay: false,
      port: 24678
    },
    allowedHosts: [
      "localhost",
      "127.0.0.1",
      ".preview.emergentagent.com",
      "02adb51f-83c2-48e6-b3b0-2ac1480e7852.preview.emergentagent.com"
    ]
  },
  optimizeDeps: {
    include: ["react", "react-dom"]
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          icons: ["lucide-react"]
        }
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvYXBwL2Zyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvYXBwL2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9hcHAvZnJvbnRlbmQvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xuXG4vLyBodHRwczovL3ZpdGVqcy5kZXYvY29uZmlnL1xuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3JlYWN0KCldLFxuICBzZXJ2ZXI6IHtcbiAgICBob3N0OiAnMC4wLjAuMCcsXG4gICAgcG9ydDogMzAwMCxcbiAgICB3YXRjaDoge1xuICAgICAgdXNlUG9sbGluZzogdHJ1ZSwgLy8gVXNhciBwb2xsaW5nIGVuIGx1Z2FyIGRlIGZpbGUgd2F0Y2hlcnNcbiAgICAgIGludGVydmFsOiAyMDAwLCAgIC8vIEludGVydmFsbyBkZSAyIHNlZ3VuZG9zIHBhcmEgcmVkdWNpciBjYXJnYVxuICAgICAgaWdub3JlZDogWycqKi9ub2RlX21vZHVsZXMvKionLCAnKiovLmdpdC8qKicsICcqKi9kaXN0LyoqJywgJyoqLy52c2NvZGUvKionXVxuICAgIH0sXG4gICAgaG1yOiB7XG4gICAgICBjbGllbnRQb3J0OiA0NDMsXG4gICAgICAvLyBSZW1vdmVyIGhvc3QgZXNwZWNcdTAwRURmaWNvIHBhcmEgZXZpdGFyIGJpbmRpbmcgYSBJUCBleHRlcm5hXG4gICAgICBvdmVybGF5OiBmYWxzZSxcbiAgICAgIHBvcnQ6IDI0Njc4XG4gICAgfSxcbiAgICBhbGxvd2VkSG9zdHM6IFtcbiAgICAgICdsb2NhbGhvc3QnLFxuICAgICAgJzEyNy4wLjAuMScsXG4gICAgICAnLnByZXZpZXcuZW1lcmdlbnRhZ2VudC5jb20nLFxuICAgICAgJzAyYWRiNTFmLTgzYzItNDhlNi1iM2IwLTJhYzE0ODBlNzg1Mi5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tJ1xuICAgIF1cbiAgfSxcbiAgb3B0aW1pemVEZXBzOiB7XG4gICAgaW5jbHVkZTogWydyZWFjdCcsICdyZWFjdC1kb20nXSxcbiAgfSxcbiAgYnVpbGQ6IHtcbiAgICByb2xsdXBPcHRpb25zOiB7XG4gICAgICBvdXRwdXQ6IHtcbiAgICAgICAgbWFudWFsQ2h1bmtzOiB7XG4gICAgICAgICAgdmVuZG9yOiBbJ3JlYWN0JywgJ3JlYWN0LWRvbSddLFxuICAgICAgICAgIGljb25zOiBbJ2x1Y2lkZS1yZWFjdCddXG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9XG4gIH1cbn0pXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQXlOLFNBQVMsb0JBQW9CO0FBQ3RQLE9BQU8sV0FBVztBQUdsQixJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTLENBQUMsTUFBTSxDQUFDO0FBQUEsRUFDakIsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBLE1BQ0wsWUFBWTtBQUFBO0FBQUEsTUFDWixVQUFVO0FBQUE7QUFBQSxNQUNWLFNBQVMsQ0FBQyxzQkFBc0IsY0FBYyxjQUFjLGVBQWU7QUFBQSxJQUM3RTtBQUFBLElBQ0EsS0FBSztBQUFBLE1BQ0gsWUFBWTtBQUFBO0FBQUEsTUFFWixTQUFTO0FBQUEsTUFDVCxNQUFNO0FBQUEsSUFDUjtBQUFBLElBQ0EsY0FBYztBQUFBLE1BQ1o7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsY0FBYztBQUFBLElBQ1osU0FBUyxDQUFDLFNBQVMsV0FBVztBQUFBLEVBQ2hDO0FBQUEsRUFDQSxPQUFPO0FBQUEsSUFDTCxlQUFlO0FBQUEsTUFDYixRQUFRO0FBQUEsUUFDTixjQUFjO0FBQUEsVUFDWixRQUFRLENBQUMsU0FBUyxXQUFXO0FBQUEsVUFDN0IsT0FBTyxDQUFDLGNBQWM7QUFBQSxRQUN4QjtBQUFBLE1BQ0Y7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
