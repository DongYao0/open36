import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3001,
    open: true,
    proxy: {
      '/api/enrollment': {
        target: 'http://localhost:8084',
        changeOrigin: true
      },
      '/api/ai': {
        target: 'http://localhost:8008',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8081',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
