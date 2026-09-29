// 场景B：论坛集中读取（默认 600 并发持续 10 分钟）
// 流量构成：80% 帖子列表 / 20% 帖子详情+回复
//
// 运行：k6 run -e BASE_URL=http://172.20.193.162:8080 forum-read.js
// setup() 会从当前部署自动发现有效帖子 ID，避免稀疏 ID 产生假 404。

import http from 'k6/http';
import { BASE_URL, getApi, getStatic, think, baseThresholds, makeSummary } from './common.js';

const FORUM_VUS = parseInt(__ENV.FORUM_VUS || '600', 10);
const FORUM_RAMP = __ENV.FORUM_RAMP || '1m';
const FORUM_HOLD = __ENV.FORUM_HOLD || '10m';
const FORUM_RAMP_DOWN = __ENV.FORUM_RAMP_DOWN || '1m';

export const options = {
  scenarios: {
    forumRead: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: FORUM_RAMP, target: FORUM_VUS },
        { duration: FORUM_HOLD, target: FORUM_VUS },
        { duration: FORUM_RAMP_DOWN, target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: baseThresholds(),
};

export function setup() {
  const res = http.get(`${BASE_URL}/api/posts/?page=1&page_size=200`, { responseType: 'text' });
  if (res.status !== 200) return { postIds: [] };
  try {
    const body = res.json();
    const results = body && body.data && Array.isArray(body.data.results) ? body.data.results : [];
    const postIds = results.map(p => p.id).filter(id => Number.isInteger(id) && id > 0);
    console.log(`setup: discovered ${postIds.length} published forum posts`);
    return { postIds };
  } catch (_e) {
    return { postIds: [] };
  }
}

export default function (data) {
  const postIds = (data && data.postIds) || [];
  const isDetail = postIds.length > 0 && Math.random() < 0.2;

  if (isDetail) {
    // 帖子详情 + 回复列表（同屏两个动态请求，还原真实页面行为）
    const pid = postIds[Math.floor(Math.random() * postIds.length)];
    getApi(`/api/posts/${pid}/`);
    getApi(`/api/replies/?post_id=${pid}&page=1&page_size=50`);
  } else {
    const section = Math.random() < 0.5 ? 'tech' : 'share';
    getApi(`/api/posts/?section=${section}&page=1&page_size=20`);
  }
  // 少量静态页面（用户偶尔整页刷新）
  if (Math.random() < 0.1) {
    getStatic('/app/forum');
  }
  think();
}

export function handleSummary(data) {
  return makeSummary('forum-read')(data);
}
