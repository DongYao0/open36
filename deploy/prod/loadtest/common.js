// 共享配置与工具：所有场景 import 本文件。
// 用法：k6 run -e BASE_URL=http://172.20.193.162:8080 browse.js
//
// 口径（压测前置修复）：
//   - 静态 = 页面 HTML / 哈希 js/css / 图片 / 3D 模型；
//   - 动态 = /api/* 一切接口（含 homepage/public，按服务端耗时与失败率
//     单独统计，不再混入静态口径）；
//   - 阈值即验收线：静态失败<0.1%、动态失败<1%、P95<800ms、P99<2000ms。

import http from 'k6/http';
import { sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

export const BASE_URL = __ENV.BASE_URL || 'http://172.20.193.162:8080';

// ── 分类指标 ──
export const staticDuration = new Trend('static_req_duration', true);
export const dynamicDuration = new Trend('dynamic_req_duration', true);
export const staticFailRate = new Rate('static_fail_rate');
export const dynamicFailRate = new Rate('dynamic_fail_rate');

// 真实用户停顿：3~8 秒随机
export function think() {
  sleep(3 + Math.random() * 5);
}

// ── 记账助手（供 http.batch 等自定义请求复用同一口径）──
export function recordStatic(ok, durationMs, tags) {
  staticDuration.add(durationMs, tags || {});
  staticFailRate.add(!ok);
}

export function recordDynamic(ok, durationMs, tags) {
  dynamicDuration.add(durationMs, tags || {});
  dynamicFailRate.add(!ok);
}

// ── 单请求封装 ──
export function getStatic(path, extras) {
  const res = http.get(`${BASE_URL}${path}`, Object.assign({ tags: { type: 'static' } }, extras));
  const ok = res.status >= 200 && res.status < 400;
  recordStatic(ok, res.timings.duration, Object.assign({ path }, (extras && extras.tags) || {}));
  return res;
}

export function getApi(path, extras) {
  const res = http.get(`${BASE_URL}${path}`, Object.assign({ tags: { type: 'api' } }, extras));
  const ok = res.status >= 200 && res.status < 300;
  recordDynamic(ok, res.timings.duration, Object.assign({ path }, (extras && extras.tags) || {}));
  return res;
}

export function postApi(path, body, headers) {
  const res = http.post(`${BASE_URL}${path}`, JSON.stringify(body), Object.assign(
    { tags: { type: 'api' }, headers: Object.assign({ 'Content-Type': 'application/json' }, headers || {}) }));
  const ok = res.status >= 200 && res.status < 300;
  recordDynamic(ok, res.timings.duration, { path });
  return res;
}

// 旧页面池保留给轻量场景
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

export function baseThresholds() {
  return {
    static_fail_rate: ['rate<0.001'],
    dynamic_fail_rate: ['rate<0.01'],
    dynamic_req_duration: ['p(95)<800', 'p(99)<2000'],
  };
}

// 统一 summary：控制台摘要 + <name>-summary.json（含 P50/90/95/99、RPS、状态码分布）
export function makeSummary(name) {
  return function (data) {
    const m = data.metrics;
    const pct = (t) => {
      if (!m[t]) return {};
      const v = m[t].values;
      return {
        count: v.count, avg: r2(v.avg),
        p50: r2(v['p(50)']), p90: r2(v['p(90)']),
        p95: r2(v['p(95)']), p99: r2(v['p(99)']), max: r2(v.max),
      };
    };
    const summary = {
      scenario: name,
      base_url: BASE_URL,
      started: new Date(data.state.testRunDurationMs ? Date.now() - data.state.testRunDurationMs : Date.now()).toISOString(),
      test_duration_s: r2(data.state.testRunDurationMs / 1000),
      http_reqs: m.http_reqs ? m.http_reqs.values.count : 0,
      actual_rps: m.http_reqs ? r2(m.http_reqs.values.rate) : 0,
      static: { duration: pct('static_req_duration'), fail_rate: m.static_fail_rate ? r4(m.static_fail_rate.values.rate) : null },
      dynamic: { duration: pct('dynamic_req_duration'), fail_rate: m.dynamic_fail_rate ? r4(m.dynamic_fail_rate.values.rate) : null },
      http_req_duration: pct('http_req_duration'),
      http_req_failed: m.http_req_failed ? r4(m.http_req_failed.values.rate) : null,
      checks: m.checks ? { rate: r4(m.checks.values.rate), passes: m.checks.values.passes } : null,
      scenario_state: data.state ? { testRunDurationMs: data.state.testRunDurationMs } : null,
    };
    // 状态码分布（从 counters 里找 http_reqs 之外的 http_resp_status*）
    const codes = {};
    for (const [k, v] of Object.entries(m)) {
      const mm = k.match(/^http_resp_status_(\d{3})$/);
      if (mm && v.values) codes[mm[1]] = v.values.count;
    }
    if (Object.keys(codes).length) summary.status_codes = codes;
    return {
      stdout: textBlock(name, summary),
      [`${name}-summary.json`]: JSON.stringify(summary, null, 2),
    };
  };
}

const r2 = (x) => (typeof x === 'number' ? Math.round(x * 100) / 100 : x);
const r4 = (x) => (typeof x === 'number' ? Math.round(x * 10000) / 10000 : x);

function textBlock(name, s) {
  return [
    `==== ${name} summary ====`,
    `duration_s=${s.test_duration_s}  reqs=${s.http_reqs}  rps=${s.actual_rps}`,
    `static:  fail=${s.static.fail_rate}  p95=${s.static.duration.p95}ms  p99=${s.static.duration.p99}ms`,
    `dynamic: fail=${s.dynamic.fail_rate}  p95=${s.dynamic.duration.p95}ms  p99=${s.dynamic.duration.p99}ms`,
    s.status_codes ? `codes: ${JSON.stringify(s.status_codes)}` : '',
  ].filter(Boolean).join('\n') + '\n';
}
