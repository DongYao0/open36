// ─────────────────────────────────────────────────────────────
//  Open436 Admin Mock 中心开关
//
//  设计原则：mock 仅在开发构建（Vite dev server）启用；
//  生产构建（vite build）中 import.meta.env.PROD === true，
//  mock 全部强制关闭，避免后端未实现模块在生产返回伪造数据造成误解。
//
//  当前 Mock 实现仅为前端原型演示；任何 mock 模块必须确保生产构建
//  实际后端接口可用，否则该功能在生产不可用（明确报错，不静默）。
// ─────────────────────────────────────────────────────────────

// `import.meta.env.DEV` 在 vite build 时为 false（生产构建）；运行时永远为 false
// 这里同时检查 PROD 作为显式断言，便于读者理解意图
const isProdBuild = import.meta.env.PROD === true || import.meta.env.MODE === 'production'

export const MOCK_CONFIG = {
  // quiz 当前为 mock；生产环境强制关闭（如需启用须先实现真实后端）
  quiz: true,
  enrollment: false,
}

// 真实判定函数：dev 模式按 MOCK_CONFIG；生产构建永远返回 false
export function isMockEnabled(module) {
  if (isProdBuild) {
    // 生产构建：mock 永久关闭，不返回伪造数据
    if (MOCK_CONFIG[module]) {
      // eslint-disable-next-line no-console
      console.warn(`[mock] module '${module}' 已禁用：生产构建不允许 mock。`
        + `请确认该模块已接入真实后端。`)
    }
    return false
  }
  return !!MOCK_CONFIG[module]
}
