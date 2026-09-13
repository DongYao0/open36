// 场景A：1000 人同时在线浏览（不是 1000 rps！）
// 爬坡：0→200(2m) →500(3m) →1000(5m) 保持1000(10m) →0(2m)
//
// 修复（压测前置）：
//   1. /api/* 一律按动态统计（原先混进 getStatic 导致失败率口径错误）；
//   2. k6 不做浏览器解析 → 按真实页面清单加载哈希资源与配套 API
//      （pages.generated.js 由 gen-pages.py 对实际部署生成）。
//
// 运行：k6 run -e BASE_URL=http://172.20.193.162:8080 browse.js

import http from 'k6/http';
import { PAGE_GROUPS } from './pages.generated.js';
import { BASE_URL, getApi, think, baseThresholds, makeSummary,
         recordStatic } from './common.js';

const TOTAL_WEIGHT = PAGE_GROUPS.reduce((s, g) => s + g.weight, 0);

function pickGroup() {
  let r = Math.random() * TOTAL_WEIGHT;
  for (const g of PAGE_GROUPS) {
    r -= g.weight;
    if (r < 0) return g;
  }
  return PAGE_GROUPS[0];
}

export const options = {
  scenarios: {
    browse1000: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 200 },
        { duration: '3m', target: 500 },
        { duration: '5m', target: 1000 },
        { duration: '10m', target: 1000 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: baseThresholds(),
};

export default function () {
  const group = pickGroup();
  const urls = group.static;

  // 页面 HTML + 静态资源一次性并发拉取（还原浏览器首屏）
  const responses = http.batch(
    urls.map(u => ['GET', `${BASE_URL}${u}`,
                   null, { tags: { type: 'static', page: group.name } }]));
  const arr = Array.isArray(responses) ? responses : [responses];
  for (const res of arr) {
    recordStatic(res.status >= 200 && res.status < 400,
                 res.timings.duration, { page: group.name });
  }

  // 页面配套动态 API（串行小批，还原前端首屏请求顺序）
  for (const api of group.api) {
    getApi(api, { tags: { page: group.name } });
  }
  think(); // 3~8s 阅读停顿
}

export function handleSummary(data) {
  return makeSummary('browse')(data);
}
