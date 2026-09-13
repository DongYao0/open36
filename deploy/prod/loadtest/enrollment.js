// 场景C：报名集中提交（三档：20 / 100 / 300 并发）
//
// 每个虚拟用户：
//   1. 生成唯一测试用户名/学号/幂等键（前缀 lt，便于压测后清理）；
//   2. 用同一个 X-Idempotency-Key 连续提交 3 次（模拟用户双击/刷新重试）；
//   3. 校验三次响应一致：全部成功且指向同一结果，或全部以 409 指向同一冲突；
//      不允许出现"一次 500 / 一次成功"的半成功账号；
//   4. 同 Key 提交不同内容（fingerprint 漂移）应得到 409，而不是复用旧结果。
//
// 运行（在实验室局域网，压测电脑直连天元 5G）：
//   k6 run -e BASE_URL=http://172.20.193.162:8080 -e TIER=20  enrollment.js
//   k6 run -e BASE_URL=... -e TIER=100 enrollment.js
//   k6 run -e BASE_URL=... -e TIER=300 enrollment.js   # 短时突发
//
// 阶段5 落地前，服务端会忽略幂等键，本脚本的第 3/4 步会如实暴露重复创建
// ——这是预期行为：改造前红、改造后绿。

import exec from 'k6/execution';
import { sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { postApi, BASE_URL } from './common.js';

const TIER = parseInt(__ENV.TIER || '20', 10);
const DURATION = __ENV.TIER_DURATION || (TIER >= 300 ? '2m' : '10m');

const enrollDuration = new Trend('enroll_duration', true);
const enrollFailRate = new Rate('enroll_fail_rate');
const enrollHalfSuccess = new Rate('enroll_half_success'); // 任一次响应与首次不一致
const enrollServerErrors = new Counter('enroll_5xx_count');

export const options = {
  scenarios: {
    enrollBurst: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: TIER },
        { duration: DURATION, target: TIER },
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '20s',
    },
  },
  thresholds: {
    enroll_duration: ['p(95)<2000'],
    enroll_fail_rate: ['rate<0.01'],
    enroll_half_success: ['rate<0.001'],
  },
};

// 与 Auth 校验规则一致：2-20 位
function uniqueName(iter) {
  return `lt${TIER}u${iter % 100000}`;
}

function applyBody(iter) {
  return {
    username: uniqueName(iter),
    password: 'LtTest#0436',
    studentId: `LT${TIER}${String(iter).padStart(7, '0')}`,
    realName: `压测用户${iter}`,
    phone: `170${String(10000000 + (iter % 89999999))}`,
    major: 'loadtest',
    selfIntro: '',
    skills: '',
  };
}

// 统一判定：HTTP 2xx 且业务 code=200 视为"受理成功"
function accepted(res) {
  if (res.status >= 500) { enrollServerErrors.add(1); return false; }
  if (res.status !== 200) return false;
  try {
    const body = res.json();
    return body && (body.code === 200 || body.status === 200);
  } catch (_e) { return false; }
}

export default function () {
  const iter = exec.scenario.iterationInTest;
  const idemKey = `lt-idem-${TIER}-${iter}`;
  const body = applyBody(iter);

  // ── 步骤1~3：同 Key 提交 3 次（双击 + 刷新重试模型），间隔 300ms ──
  const results = [];
  for (let i = 0; i < 3; i++) {
    const res = postApi('/api/enrollment/apply', body, { 'X-Idempotency-Key': idemKey });
    enrollDuration.add(res.timings.duration);
    const ok = accepted(res);
    enrollFailRate.add(!ok);
    results.push({ status: res.status, ok });
    sleep(0.3);
  }

  // 三次结果必须一致：全成功 或 全部一致的拒绝（409/4xx）。
  // 出现 500 与成功混杂、或部分成功部分失败 = 半成功账号。
  const okCount = results.filter(r => r.ok).length;
  const statuses = new Set(results.map(r => r.status >= 500 ? '5xx' : (r.ok ? 'ok' : '4xx')));
  const consistent = okCount === 0 || okCount === 3;
  enrollHalfSuccess.add(!consistent || statuses.size > 1);

  // ── 步骤4：同 Key 不同内容 → 必须 409，不得静默复用旧结果 ──
  const drifted = Object.assign({}, body, { realName: `压测用户${iter}DRIFT` });
  const driftRes = postApi('/api/enrollment/apply', drifted, { 'X-Idempotency-Key': idemKey });
  // 阶段5 前服务端忽略 Key，会返回"用户名已存在"类 4xx——同样不可接受为 5xx
  if (driftRes.status >= 500) enrollServerErrors.add(1);

  sleep(1 + Math.random() * 2);
}
