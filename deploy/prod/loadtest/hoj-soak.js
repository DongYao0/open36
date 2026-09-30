// HOJ 60 用户长稳测试：浏览 + 正常提交 + 连点/非法载荷。
// 示例：k6 run -e BASE_URL=https://open0436.space -e SOAK_DURATION=5h
//   -e HOJ_ACCOUNTS_FILE=hoj-soak-accounts.txt -e HOJ_PROBLEM_ID=1 hoj-soak.js
import http from 'k6/http';
import { sleep } from 'k6';
import exec from 'k6/execution';
import { Counter, Rate, Trend } from 'k6/metrics';
import { BASE_URL, makeSummary, SUMMARY_TREND_STATS } from './common.js';

const DURATION = __ENV.SOAK_DURATION || '5h';
const BROWSE_VUS = parseInt(__ENV.HOJ_BROWSE_VUS || '60', 10);
const SUBMIT_RATE = parseInt(__ENV.SUBMIT_RATE_PER_MINUTE || '45', 10);
const PROBLEM_ID = __ENV.HOJ_PROBLEM_ID || '1';
const ACCOUNTS_FILE = __ENV.HOJ_ACCOUNTS_FILE || 'hoj-soak-accounts.txt';
const PASSWORD_FALLBACK = __ENV.HOJ_ACCOUNT_PASSWORD || '';
const CODE = '#include <iostream>\nusing namespace std;\nint main(){int a=0,b=0;if(cin>>a>>b)cout<<a+b<<endl;else cout<<0<<endl;return 0;}';

const accounts = open(ACCOUNTS_FILE).split('\n')
  .map(line => line.trim()).filter(line => line && !line.startsWith('#'))
  .map(line => {
    const split = line.indexOf(':');
    return { username: line.slice(0, split), password: line.slice(split + 1) || PASSWORD_FALLBACK };
  });
if (accounts.length < BROWSE_VUS + 3) throw new Error(`账号不足：需要至少 ${BROWSE_VUS + 3}，当前 ${accounts.length}`);

const apiDuration = new Trend('hoj_api_duration', true);
const submitAccepted = new Rate('hoj_submit_accepted');
const submitLost = new Counter('hoj_submit_lost');
const abnormalSafe = new Rate('hoj_abnormal_safe');
const rateLimited = new Counter('hoj_rate_limited');
const loginSuccess = new Rate('hoj_login_success');

export const options = {
  summaryTrendStats: SUMMARY_TREND_STATS,
  scenarios: {
    browse: { executor: 'constant-vus', vus: BROWSE_VUS, duration: DURATION, exec: 'browse' },
    submit: {
      executor: 'constant-arrival-rate', rate: SUBMIT_RATE, timeUnit: '1m', duration: DURATION,
      preAllocatedVUs: 12, maxVUs: 40, exec: 'submit',
    },
    abnormal: {
      executor: 'constant-arrival-rate', rate: 6, timeUnit: '1m', duration: DURATION,
      preAllocatedVUs: 3, maxVUs: 10, exec: 'abnormal',
    },
  },
  thresholds: {
    hoj_api_duration: ['p(95)<800', 'p(99)<2000'],
    hoj_submit_accepted: ['rate>0.999'],
    hoj_abnormal_safe: ['rate>0.999'],
    hoj_login_success: ['rate>0.999'],
  },
};

const tokens = {};
function accountFor(offset = 0) {
  return accounts[(exec.vu.idInTest - 1 + offset) % accounts.length];
}
function tokenFor(account) {
  if (tokens[account.username]) return tokens[account.username];
  const response = http.post(`${BASE_URL}/api/login`, JSON.stringify(account), {
    headers: { 'Content-Type': 'application/json' }, tags: { action: 'login' },
  });
  const token = response.headers.Authorization;
  const ok = response.status === 200 && Boolean(token);
  loginSuccess.add(ok);
  if (ok) tokens[account.username] = token;
  return token;
}
function authHeaders(token) {
  return { headers: { 'Content-Type': 'application/json', Authorization: token || '' } };
}
function record(response, path) {
  apiDuration.add(response.timings.duration, { path });
}

export function browse() {
  const token = tokenFor(accountFor());
  if (!token) { sleep(3); return; }
  const paths = [
    '/api/get-problem-list?limit=20&currentPage=1',
    `/api/get-problem-detail?problemId=${encodeURIComponent(PROBLEM_ID)}`,
    '/api/get-submission-list?limit=20&currentPage=1&onlyMine=false',
  ];
  const path = paths[Math.floor(Math.random() * paths.length)];
  const response = http.get(`${BASE_URL}${path}`, authHeaders(token));
  record(response, path);
  sleep(3 + Math.random() * 5);
}

export function submit() {
  const account = accounts[exec.scenario.iterationInTest % BROWSE_VUS];
  const token = tokenFor(account);
  if (!token) { submitAccepted.add(false); submitLost.add(1); return; }
  const response = http.post(`${BASE_URL}/api/submit-problem-judge`, JSON.stringify({
    pid: PROBLEM_ID, cid: 0, gid: null, tid: null, language: 'C++', code: CODE, isRemote: false,
  }), authHeaders(token));
  record(response, '/api/submit-problem-judge');
  submitAccepted.add(response.status === 200);
  if (response.status !== 200) submitLost.add(1);
}

export function abnormal() {
  const abnormalPool = accounts.length - BROWSE_VUS;
  const account = accounts[BROWSE_VUS + ((exec.vu.idInTest - 1) % abnormalPool)];
  const token = tokenFor(account);
  if (!token) { abnormalSafe.add(false); return; }
  const valid = JSON.stringify({ pid: PROBLEM_ID, cid: 0, language: 'C++', code: CODE, isRemote: false });
  const first = http.post(`${BASE_URL}/api/submit-problem-judge`, valid, authHeaders(token));
  const second = http.post(`${BASE_URL}/api/submit-problem-judge`, valid, authHeaders(token));
  const invalid = http.post(`${BASE_URL}/api/submit-problem-judge`, JSON.stringify({
    pid: PROBLEM_ID, cid: 0, language: null, code: '', isRemote: null,
  }), authHeaders(token));
  for (const response of [first, second, invalid]) {
    abnormalSafe.add(response.status > 0 && response.status < 500);
    if (response.status === 403 || response.status === 429) rateLimited.add(1);
  }
}

export function handleSummary(data) {
  const output = makeSummary('hoj-soak')(data);
  const target = __ENV.SUMMARY_FILE;
  if (target) {
    output[target] = output['hoj-soak-summary.json'];
    delete output['hoj-soak-summary.json'];
  }
  return output;
}
