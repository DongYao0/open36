// 场景B：论坛集中读取（300 并发持续 10 分钟）
// 流量构成：80% 帖子列表 / 20% 帖子详情+回复
//
// 运行：k6 run -e BASE_URL=http://172.20.193.162:8080 forum-read.js
// POST_ID_RANGE 控制详情页 id 范围（按当前库实际帖子量调整）。

import { getApi, getStatic, think, baseThresholds, makeSummary } from './common.js';

const POST_MAX = parseInt(__ENV.POST_ID_MAX || '200', 10);

export const options = {
  scenarios: {
    forumRead: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 300 },
        { duration: '10m', target: 300 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: baseThresholds(),
};

export default function () {
  const isDetail = Math.random() < 0.2;

  if (isDetail) {
    // 帖子详情 + 回复列表（同屏两个动态请求，还原真实页面行为）
    const pid = 1 + Math.floor(Math.random() * POST_MAX);
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
