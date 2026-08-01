import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ══════════════════════════════════════════════════════════
//  Open436 聚合开发入口 (:5173)
//  本端口既是 3D 首页(本 React 应用)，又反向代理 Vue 业务应用(:3000)，
//  实现同源(localStorage 登录态共享)的统一入口。
//
//    :5173/        → 3D 首页(本应用)
//    :5173/app/*   → Vue 主应用 Open436-Frontend(:3000)，论坛/赛事/登录等
//    :5173/api/*   → Vue → 各后端微服务
//    :5173/algo    → Vue → HOJ(:8066)
// ══════════════════════════════════════════════════════════
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    open: true,
    proxy: {
      '/app': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        ws: true,
      },
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
      '/algo': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
})
