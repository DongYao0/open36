// 场景A：1000 人同时在线浏览（不是 1000 rps！）
// 爬坡模型（任务书）：
//   0 → 200 VU：2 分钟
//   200 → 500 VU：3 分钟
//   500 → 1000 VU：5 分钟
//   保持 1000 VU：10 分钟
//   1000 → 0：2 分钟
// 每个虚拟用户动作间随机停顿 3~8 秒，随机访问公共页面池。
//
// 运行：k6 run -e BASE_URL=http://172.20.193.162:8080 browse.js
// 总时长约 22 分钟，请预留窗口。

import { getStatic, think, randomPage, baseThresholds } from './common.js';

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
  getStatic(randomPage());
  think(); // 3~8s 阅读停顿——模拟真人，避免 DDoS 模式
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data),
    'browse-summary.json': JSON.stringify(data, null, 2),
  };
}

// 轻量文本摘要（避免依赖 k6 internals）
function textSummary(data) {
  const m = data.metrics;
  const line = (name) => name in m ? `${name}: ${JSON.stringify(m[name].values)}` : '';
  return [
    '==== browse.js summary ====',
    line('http_reqs'), line('http_req_duration'),
    line('static_fail_rate'), line('dynamic_fail_rate'),
    line('static_req_duration'), line('dynamic_req_duration'),
  ].join('\n') + '\n';
}
