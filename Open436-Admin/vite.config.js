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
      '/api/admin/role': {
        target: 'http://localhost:6688',
        changeOrigin: true
      },
      '/api/admin/user': {
        target: 'http://localhost:6688',
        changeOrigin: true
      },
      '/api/enrollment': {
        target: 'http://localhost:8084',
        changeOrigin: true
      },
      '/api/assignment': {
        target: 'http://localhost:8084',
        changeOrigin: true
      },
      '/api/interview': {
        target: 'http://localhost:8084',
        changeOrigin: true
      },
      '/api/ai': {
        target: 'http://localhost:8008',
        changeOrigin: true
      },
      '/api/files': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/posts': {
        target: 'http://localhost:8003',
        changeOrigin: true
      },
      '/api/sections': {
        target: 'http://localhost:8003',
        changeOrigin: true
      },
      '/api/replies': {
        target: 'http://localhost:8003',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8081',
        changeOrigin: true
      },
      // HOJ 前端：同源 /algo 路径（与生产 Admin nginx 行为一致）
      '/algo': {
        target: 'http://localhost:8066',
        changeOrigin: true
      },
      // 荣誉相册静态资源：由 Landing(5173) 提供 public/honors
      '/honors': {
        target: 'http://localhost:5173',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
