// 场景D：HOJ 150 人比赛
//   - 浏览线程：约 150 VU 浏览题目列表/题目详情/提交列表（登录态）；
//   - 提交线程：20 次/秒 短时峰值持续 3~5 分钟（constant-arrival-rate）；
//   - 提交必须进入队列（Pending/Compiling 均算受理），不允许 5xx 丢任务；
//   - 不要求 150 个程序同时编译运行。
//
// 前置：准备 HOJ 压测账号（见 README「HOJ 压测账号准备」），
//       通过 HOJ_ACCOUNTS="u1:p1,u2:p2,..." 传入（建议 ≥50 个，
//       绕开单用户 defaultSubmitInterval=8s 的提交间隔限制）。
//
// 运行：k6 run -e BASE_URL=http://172.20.193.162:8080 \
//          -e HOJ_ACCOUNTS="ltc1:pass1,ltc2:pass2,..." hoj-submit.js

import http from 'k6/http';
import { sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://172.20.193.162:8080';
const ACCOUNTS = (__ENV.HOJ_ACCOUNTS || '').split(',').filter(Boolean).map(p => {
  const [username, password] = p.split(':');
  return { username, password, token: null };
});
if (ACCOUNTS.length === 0) {
  throw new Error('必须通过 HOJ_ACCOUNTS 提供至少一个压测账号（建议 ≥50 个）');
}

const hojApiDuration = new Trend('hoj_api_duration', true);
const submitAccepted = new Rate('hoj_submit_accepted');
const submitLost = new Counter('hoj_submit_lost'); // 5xx/网络失败=可能丢失
const CODE = '#include <iostream>\nusing namespace std;\nint main(){int a,b;while(cin>>a>>b)cout<<a+b<<endl;return 0;}';

export const options = {
  scenarios: {
    // 150 人浏览（3~8s 停顿）
    browse: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 150 },
        { duration: '5m', target: 150 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browse',
    },
    // 20 提交/秒 峰值（arrival rate 模型，与浏览并发并行）
    submit: {
      executor: 'constant-arrival-rate',
      rate: 20, timeUnit: '1s',
      duration: '3m',
      preAllocatedVUs: 60, maxVUs: 120,
      startTime: '1m', // 与浏览高峰重叠
      exec: 'submit',
    },
  },
  thresholds: {
    hoj_api_duration: ['p(95)<800', 'p(99)<2000'],
    hoj_submit_accepted: ['rate>0.999'], // 提交受理失败率 <0.1%
  },
};

function login(acc) {
  const res = http.post(`${BASE_URL}/api/login`,
    JSON.stringify({ username: acc.username, password: acc.password }),
    { headers: { 'Content-Type': 'application/json' } });
  const auth = res.headers['Authorization'];
  if (res.status === 200 && auth) acc.token = auth;
}

function ensureToken(acc) {
  if (!acc.token) login(acc);
  return acc.token;
}

// ── 浏览：题目列表 / 单题 / 提交列表 ──
export function browse() {
  const acc = ACCOUNTS[__VU % ACCOUNTS.length];
  const token = ensureToken(acc);
  const headers = token ? { Authorization: token } : {};
  const r = Math.random();
  let path;
  if (r < 0.5) path = '/api/get-problem-list?limit=20&currentPage=1';
  else if (r < 0.8) path = '/api/get-problem?problemId=JC1';
  else path = '/api/get-submission-list?limit=20&currentPage=1&onlyMine=false';
  const res = http.get(`${BASE_URL}${path}`, { headers });
  hojApiDuration.add(res.timings.duration, { path });
  sleep(3 + Math.random() * 5);
}

// ── 提交：受理即成功（进入队列），5xx 计为丢失 ──
export function submit() {
  const acc = ACCOUNTS[Math.floor(Math.random() * ACCOUNTS.length)];
  const token = ensureToken(acc);
  if (!token) { submitAccepted.add(false); submitLost.add(1); return; }
  const res = http.post(`${BASE_URL}/api/submit-problem-judge`,
    JSON.stringify({ pid: 'JC1', cid: null, gid: null, tid: null, language: 'C++', code: CODE, isRemote: false }),
    { headers: { 'Content-Type': 'application/json', Authorization: token } });
  hojApiDuration.add(res.timings.duration, { path: '/api/submit-problem-judge' });
  const ok = res.status === 200;
  submitAccepted.add(ok);
  if (!ok) submitLost.add(1);
}
