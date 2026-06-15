import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  // 路径别名
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  
  // 开发服务器配置
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: true,
    // 代理配置 - Open436 API 通过 Kong，HOJ 资源直连 HOJ 前端 devServer
    proxy: {
      '/api/auth': {
        target: 'http://localhost:8081',
        changeOrigin: true
      },
      '/api/enrollment': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/assignment': {
        target: 'http://localhost:8084',
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
      '/api/comments': {
        target: 'http://localhost:8003',
        changeOrigin: true
      },
      '/api/files': {
        target: 'http://localhost:8007',
        changeOrigin: true
      },
      '/api/users': {
        target: 'http://localhost:8081',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:6688',
        changeOrigin: true
      },
      '/algo': {
        target: 'http://localhost:8066',
        changeOrigin: true,
        rewrite: (path) => path
      }
    }
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    // 分包策略
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'axios-vendor': ['axios']
        }
      }
    }
  }
})
