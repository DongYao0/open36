// 共享配置与工具：所有场景 import 本文件。
// 用法：k6 run -e BASE_URL=http://172.20.193.162:8080 browse.js
//
// 设计原则（任务书阶段1）：
//   - 在线用户会阅读、停留、点击 → 动作间随机停顿 3~8s，禁止无停顿死循环；
//   - 静态/动态指标分开统计，便于对照验收线；
//   - 阈值即验收线：静态失败<0.1%、动态失败<1%、P95<800ms、P99<2000ms。

import http from 'k6/http';
import { sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

export const BASE_URL = __ENV.BASE_URL || 'http://172.20.193.162:8080';

// ── 分类指标：静态资源 / 动态 API / 报名提交 ──
export const staticDuration = new Trend('static_req_duration', true);
export const dynamicDuration = new Trend('dynamic_req_duration', true);
export const staticFailRate = new Rate('static_fail_rate');
export const dynamicFailRate = new Rate('dynamic_fail_rate');

// 真实用户停顿：3~8 秒随机（阅读/发呆/点击间隙）
export function think() {
  sleep(3 + Math.random() * 5);
}

// 静态页面/资源请求：2xx/3xx 视为成功，304 也算命中缓存
export function getStatic(path, extras) {
  const res = http.get(`${BASE_URL}${path}`, Object.assign({ tags: { type: 'static' } }, extras));
  const ok = res.status >= 200 && res.status < 400;
  staticDuration.add(res.timings.duration, { path: path });
  staticFailRate.add(!ok);
  return res;
}

// 动态 API 请求：仅 2xx 视为成功；429/503 记录为"明确限流"而非协议失败
export function getApi(path, extras) {
  const res = http.get(`${BASE_URL}${path}`, Object.assign({ tags: { type: 'api' } }, extras));
  const ok = res.status >= 200 && res.status < 300;
  dynamicDuration.add(res.timings.duration, { path: path });
  dynamicFailRate.add(!ok);
  return res;
}

export function postApi(path, body, headers) {
  const res = http.post(`${BASE_URL}${path}`, JSON.stringify(body), Object.assign(
    { tags: { type: 'api' }, headers: Object.assign({ 'Content-Type': 'application/json' }, headers || {}) }));
  const ok = res.status >= 200 && res.status < 300;
  dynamicDuration.add(res.timings.duration, { path: path });
  dynamicFailRate.add(!ok);
  return res;
}

// 1000 人在线浏览的公共页面池（任务书场景A清单）
export const PAGE_POOL = [
  '/',
  '/app/',
  '/app/forum',
  '/app/resources',
  '/app/contests',
  '/honors/',
  '/api/users/homepage/public',
  '/api/sections/',
  '/api/posts/?page=1&page_size=20',
];

export function randomPage() {
  return PAGE_POOL[Math.floor(Math.random() * PAGE_POOL.length)];
}

// 通用阈值：各场景可在此基础上叠加（k6 options 合并规则：本文件导出的是
// 构建 options 的辅助函数，具体场景自行组装 thresholds）
export function baseThresholds() {
  return {
    static_fail_rate: ['rate<0.001'],
    dynamic_fail_rate: ['rate<0.01'],
    'dynamic_req_duration': ['p(95)<800', 'p(99)<2000'],
  };
}
