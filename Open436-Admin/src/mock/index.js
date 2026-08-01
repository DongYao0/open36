export const MOCK_CONFIG = {
  quiz: true,
  enrollment: false
}

export function isMockEnabled(module) {
  return !!MOCK_CONFIG[module]
}
