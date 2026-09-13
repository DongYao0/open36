// 场景A：N 人同时在线浏览（真实停顿模型）
//
// 压测前置修复（第2轮）：
//   资产清单不再固化——setup() 对着【当前部署】的 HTML 动态解析哈希资产。
//   原因：部署侧可能被并行更新（assets 哈希变化），固化清单会产生整批 404，
//   污染静态失败率口径。
//
// 环境变量：
//   BROWSE_VUS（默认1000）BROWSE_HOLD（默认10m）BROWSE_RAMP（默认3m）
// 运行：k6 run -e BASE_URL=http://172.20.193.162:8080 browse.js

import http from 'k6/http';
import { BASE_URL, getApi, think, baseThresholds, makeSummary,
         recordStatic } from './common.js';

const VUS = parseInt(__ENV.BROWSE_VUS || '1000', 10);
const HOLD = __ENV.BROWSE_HOLD || '10m';
const RAMP = __ENV.BROWSE_RAMP || '3m';

export const options = {
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  scenarios: {
    browse: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: RAMP, target: VUS },
        { duration: HOLD, target: VUS },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: baseThresholds(),
};

/** 从 HTML 提取本站静态资源引用（js/css/图片），最多 maxN 个 */
function assetsFromHtml(html, maxN) {
  const out = [];
  const re = /(?:src|href)=["']([^"']+)["']/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    let u = m[1];
    if (u.startsWith('http') || u.startsWith('data:')) continue;
    if (!/\.(js|css|png|jpe?g|svg|webp|glb)(\?|$)/i.test(u)) continue;
    if (!u.startsWith('/')) u = '/' + u;
    if (out.indexOf(u) === -1) out.push(u);
    if (out.length >= maxN) break;
  }
  return out;
}

// 固定页面骨架：权重与每页 API；静态资源在 setup() 期对当前部署解析
const PAGE_SKELETON = [
  { name: 'home', weight: 30, htmlPath: '/', api: ['/api/users/homepage/public'] },
  { name: 'app-home', weight: 10, htmlPath: '/app/', api: ['/api/sections/'] },
  { name: 'forum', weight: 25, htmlPath: '/app/forum', api: ['/api/sections/', '/api/posts/?page=1&page_size=20'] },
  { name: 'resources', weight: 15, htmlPath: '/app/resources', api: ['/api/posts/?section=share&page=1&page_size=20'] },
  { name: 'contests', weight: 10, htmlPath: '/app/contests', api: ['/api/sections/'] },
  { name: 'honors', weight: 10, htmlPath: null,
    fixedStatic: ['/honors/baidu/01.jpg', '/honors/lanqiao/01.jpg',
                  '/honors/team/01.jpg', '/honors/mati/01.jpg'], api: [] },
];

export function setup() {
  const groups = PAGE_SKELETON.map(s => {
    let staticUrls = s.fixedStatic || [];
    if (s.htmlPath) {
      const res = http.get(`${BASE_URL}${s.htmlPath}`);
      const assets = res.status === 200 ? assetsFromHtml(res.body, 8) : [];
      staticUrls = [s.htmlPath].concat(assets);
    }
    return { name: s.name, weight: s.weight, static: staticUrls, api: s.api };
  });
  const total = groups.reduce((a, g) => a + g.static.length, 0);
  console.log(`setup: resolved ${groups.length} pages, ${total} static refs against live deployment`);
  return { groups };
}

const TOTAL_WEIGHT = PAGE_SKELETON.reduce((s, g) => s + g.weight, 0);

export default function (data) {
  const groups = (data && data.groups) || [];
  let r = Math.random() * TOTAL_WEIGHT;
  let group = groups[groups.length - 1];
  for (const g of groups) {
    r -= g.weight;
    if (r < 0) { group = g; break; }
  }
  if (!group || !group.static.length) { think(); return; }

  // 顺序请求（每 VU 单连接 keep-alive 复用）：
  // 天元5G AP 对并发连接数敏感（500VU×batch≈3000连接时整段断流），
  // 顺序模式连接数=VU数，施压链路稳定；页面资源总量语义不变
  for (const u of group.static) {
    const res = http.get(`${BASE_URL}${u}`, { tags: { type: 'static', page: group.name } });
    recordStatic(res.status >= 200 && res.status < 400,
                 res.timings.duration, { page: group.name, url: res.url }, res.status);
  }
  for (const api of group.api) {
    getApi(api, { tags: { page: group.name } });
  }
  think(); // 3~8s 阅读停顿——模拟真人，避免 DDoS 模式
}

export function handleSummary(data) {
  return makeSummary('browse')(data);
}
