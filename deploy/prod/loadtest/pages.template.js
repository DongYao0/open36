// 页面资源清单（由 gen-pages.py 对着真实部署生成 pages.generated.js）。
// k6 不执行浏览器解析，真实页面的哈希资源/图片/API 依赖由本清单表达。
// 生成命令（Windows，压测前执行一次）：
//   python deploy/prod/loadtest/gen-pages.py --base http://172.20.193.162:8080
//
// 结构：每组 = 一次"页面访问"触发的静态资源 + 动态 API。
export const PAGE_GROUPS = [
  {
    name: 'home',
    weight: 30,
    static: ['/', '/assets/INDEX_JS', '/assets/INDEX_CSS'],
    api: ['/api/users/homepage/public'],
  },
  {
    name: 'app-home',
    weight: 10,
    static: ['/app/', '/app/assets/APP_JS', '/app/assets/APP_CSS', '/app/user.jpg'],
    api: ['/api/sections/'],
  },
  {
    name: 'forum',
    weight: 25,
    static: ['/app/'],
    api: ['/api/sections/', '/api/posts/?page=1&page_size=20'],
  },
  {
    name: 'resources',
    weight: 15,
    static: ['/app/'],
    api: ['/api/posts/?section=share&page=1&page_size=20'],
  },
  {
    name: 'contests',
    weight: 10,
    static: ['/app/'],
    api: ['/api/sections/'],
  },
  {
    name: 'honors',
    weight: 10,
    static: ['/honors/', '/honors/SAMPLE_IMG'],
    api: [],
  },
];
