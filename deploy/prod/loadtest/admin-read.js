// 管理端只读压测：约 200 名在线管理员，查询为主。
// Admin 直接监听 LAN 的 3001 端口，不经 public-web/隧道。
//
// 运行：k6 run -e ADMIN_URL=http://172.20.193.162:3001 \
//          -e ADMIN_USER=xxx -e ADMIN_PASS=yyy admin-read.js
// 使用专用压测管理员账号，勿用生产管理员。

import http from 'k6/http';
import { sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const ADMIN_URL = __ENV.ADMIN_URL || 'http://172.20.193.162:3001';
const adminDuration = new Trend('admin_req_duration', true);
const adminFailRate = new Rate('admin_fail_rate');

export const options = {
  scenarios: {
    adminRead: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 200 },
        { duration: '10m', target: 200 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    admin_fail_rate: ['rate<0.01'],
    admin_req_duration: ['p(95)<800', 'p(99)<2000'],
  },
};

const QUERIES = [
  '/api/enrollment/?page=1&page_size=20',
  '/api/enrollment/statistics',
  '/api/auth/users?page=1&page_size=20',
  '/api/posts/?page=1&page_size=20',
];

let token = null;

function login() {
  const res = http.post(`${ADMIN_URL}/api/auth/admin/login`,
    JSON.stringify({ username: __ENV.ADMIN_USER, password: __ENV.ADMIN_PASS }),
    { headers: { 'Content-Type': 'application/json' } });
  if (res.status !== 200) return null;
  try {
    const b = res.json();
    return (b.data && (b.data.token || b.data.accessToken)) || b.token || null;
  } catch (_e) { return null; }
}

export default function () {
  if (!token) {
    token = login();
    if (!token) { adminFailRate.add(1); sleep(5); return; }
  }
  const q = QUERIES[Math.floor(Math.random() * QUERIES.length)];
  const res = http.get(`${ADMIN_URL}${q}`, {
    headers: token.startsWith('eyJ') ? { Authorization: token } : { token: token },
  });
  const ok = res.status >= 200 && res.status < 300;
  adminDuration.add(res.timings.duration, { q });
  adminFailRate.add(!ok);
  sleep(3 + Math.random() * 5); // 管理员在页面间阅读停留
}
