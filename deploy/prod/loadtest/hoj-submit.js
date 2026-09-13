// 场景D：HOJ 150 人比赛
//   - 浏览线程：150 VU 浏览题目/提交列表（登录态，3~8s 停顿）；
//   - 提交线程：恒定速率提交（SUBMIT_RATE/秒，默认 5，可 10/20）；
//   - 提交必须进入队列（HTTP 200 受理），不允许 5xx 丢任务。
//
// 账号要求（压测前置修正）：
//   HOJ 单账号提交间隔 defaultSubmitInterval=8s。20 提交/秒时，账号 i 再次
//   提交需间隔 N/Rate 秒 → N ≥ 8×Rate → 20/s 需 ≥160 个账号。
//   脚本强制校验 ACCOUNTS ≥ ceil(8×Rate)+8 余量，且按迭代序号轮询取号，
//   杜绝随机取号造成的"同账号 8 秒内重复提交 403"。
//
// 准备（Windows，对 LAN）：
//   python deploy/prod/loadtest/gen-hoj-accounts.py --base http://172.20.193.162:8080 \
//       --count 170 --prefix ltc --password 'LtHoj#0436' --out hoj-accounts.txt
// 运行：
//   k6 run -e BASE_URL=... -e HOJ_ACCOUNTS_FILE=hoj-accounts.txt \
//          -e SUBMIT_RATE=20 hoj-submit.js
// （HOJ_ACCOUNTS_FILE 每行 user:pass；也可用 HOJ_ACCOUNTS=u:p,u:p 内联。）

import http from 'k6/http';
import { sleep } from 'k6';
import exec from 'k6/execution';
import { Trend, Rate, Counter } from 'k6/metrics';
import { BASE_URL, makeSummary } from './common.js';

const SUBMIT_RATE = parseInt(__ENV.SUBMIT_RATE || '5', 10);

// ── 账号装载（文件优先于内联）──
function loadAccounts() {
  const inline = (__ENV.HOJ_ACCOUNTS || '').split(',').filter(Boolean);
  return inline.map(p => {
    const [username, password] = p.split(':');
    return { username, password, token: null };
  });
}
// k6 init 支持 open()（编译期内嵌文件）；文件不存在时退回内联
let ACCOUNTS = loadAccounts();
if (__ENV.HOJ_ACCOUNTS_FILE) {
  try {
    const raw = open(__ENV.HOJ_ACCOUNTS_FILE);
    ACCOUNTS = raw.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'))
      .map(l => {
        const [username, password] = l.split(':');
        return { username, password, token: null };
      });
  } catch (e) {
    throw new Error('无法读取 HOJ_ACCOUNTS_FILE=' + __ENV.HOJ_ACCOUNTS_FILE + ': ' + e);
  }
}

// 强制校验：账号数 ≥ 8×Rate + 8（间隔余量），否则拒绝启动
const MIN_ACCOUNTS = Math.ceil(8 * SUBMIT_RATE) + 8;
if (ACCOUNTS.length < MIN_ACCOUNTS) {
  throw new Error(
    `账号不足：${SUBMIT_RATE} 提交/秒需要 ≥${MIN_ACCOUNTS} 个账号（当前 ${ACCOUNTS.length}）。` +
    `用 gen-hoj-accounts.py 生成并经 HOJ_ACCOUNTS_FILE 传入。`);
}

const hojApiDuration = new Trend('hoj_api_duration', true);
const submitAccepted = new Rate('hoj_submit_accepted');
const submitLost = new Counter('hoj_submit_lost'); // 5xx/网络失败=可能丢失
const CODE = '#include <iostream>\nusing namespace std;\nint main(){int a,b;while(cin>>a>>b)cout<<a+b<<endl;return 0;}';

export const options = {
  scenarios: {
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
    submit: {
      executor: 'constant-arrival-rate',
      rate: SUBMIT_RATE, timeUnit: '1s',
      duration: '3m',
      preAllocatedVUs: 2 * SUBMIT_RATE + 20, maxVUs: 4 * SUBMIT_RATE + 40,
      startTime: '1m',
      exec: 'submit',
    },
  },
  thresholds: {
    hoj_api_duration: ['p(95)<800', 'p(99)<2000'],
    hoj_submit_accepted: ['rate>0.999'],
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

// ── 提交：按迭代轮询取号（同账号两次提交间隔 ≥ N/Rate 秒 > 8s）──
export function submit() {
  const iter = exec.scenario.iterationInTest;
  const acc = ACCOUNTS[iter % ACCOUNTS.length];
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

export function handleSummary(data) {
  return makeSummary('hoj-submit')(data);
}
