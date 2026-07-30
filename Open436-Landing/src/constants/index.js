import {
  mobile,
  backend,
  creator,
  web,
  javascript,
  typescript,
  html,
  css,
  reactjs,
  redux,
  tailwind,
  nodejs,
  mongodb,
  git,
  figma,
  docker,
  meta,
  starbucks,
  tesla,
  shopify,
  carrent,
  jobit,
  tripguide,
  threejs,
} from "../assets";

export const navLinks = [
  {
    id: "forum",
    title: "论坛",
    href: "/app/forum",
  },
  {
    id: "contests",
    title: "赛事",
    href: "/app/contests",
  },
  {
    id: "announcements",
    title: "公告",
    href: "/app/announcements",
  },
  {
    id: "algo",
    title: "算法",
    href: "/app/quiz",
  },
];

const services = [
  {
    title: "在线判题",
    icon: web,
  },
  {
    title: "编程赛事",
    icon: mobile,
  },
  {
    title: "技术社区",
    icon: backend,
  },
  {
    title: "AI 助手",
    icon: creator,
  },
];

const technologies = [
  {
    name: "HTML 5",
    icon: html,
  },
  {
    name: "CSS 3",
    icon: css,
  },
  {
    name: "JavaScript",
    icon: javascript,
  },
  {
    name: "TypeScript",
    icon: typescript,
  },
  {
    name: "React JS",
    icon: reactjs,
  },
  {
    name: "Redux Toolkit",
    icon: redux,
  },
  {
    name: "Tailwind CSS",
    icon: tailwind,
  },
  {
    name: "Node JS",
    icon: nodejs,
  },
  {
    name: "MongoDB",
    icon: mongodb,
  },
  {
    name: "Three JS",
    icon: threejs,
  },
  {
    name: "git",
    icon: git,
  },
  {
    name: "figma",
    icon: figma,
  },
  {
    name: "docker",
    icon: docker,
  },
];

const experiences = [
  {
    title: "在线判题系统",
    company_name: "Online Judge",
    icon: starbucks,
    iconBg: "#383E56",
    date: "HOJ 集成 · 多语言编译",
    points: [
      "集成 HOJ 在线判题内核，支持 C/C++/Java/Python 等多语言代码提交与自动评测。",
      "毫秒级沙箱隔离执行，保障判题安全与公平，实时反馈运行结果与通过状态。",
      "海量题库管理与测试数据导入，支持题目分类、难度标记与标签检索。",
      "为编程训练与竞赛提供稳定可靠的判题基础设施。",
    ],
  },
  {
    title: "编程赛事平台",
    company_name: "Contest",
    icon: tesla,
    iconBg: "#E6DEDD",
    date: "赛事日历 · 报名排名",
    points: [
      "赛事日历集中展示 upcoming 与进行中的编程竞赛，一键查看赛事详情。",
      "在线报名与参赛管理，赛后实时排名与解题情况统计。",
      "赛事详情页集成评论区，方便参赛者交流讨论与赛后复盘。",
      "为成员提供从训练到竞技的完整赛事体验闭环。",
    ],
  },
  {
    title: "技术交流社区",
    company_name: "Forum",
    icon: shopify,
    iconBg: "#383E56",
    date: "板块 · 帖子 · 互动",
    points: [
      "多板块技术论坛，支持发帖、评论、点赞、收藏与转发等完整互动。",
      "富文本内容编辑与资源分享，构建沉淀式技术知识库。",
      "全站搜索与个人收藏夹，帮助成员高效定位优质内容。",
      "营造开放、协作、共同成长的技术交流氛围。",
    ],
  },
  {
    title: "AI 智能助手",
    company_name: "AI Service",
    icon: meta,
    iconBg: "#E6DEDD",
    date: "RAG · 向量检索",
    points: [
      "基于 RAG 与向量数据库（Milvus）的智能问答，结合论坛知识库精准响应。",
      "AI 辅助内容生成与摘要，降低创作门槛、提升社区活跃度。",
      "学习辅导与错题解析，为成员提供个性化的技术成长建议。",
      "持续迭代的 AI 能力，让平台随社区一同进化。",
    ],
  },
];

const testimonials = [
  {
    testimonial:
      "在 Open436 刷题备赛的那段时间，我的算法能力提升明显，社区里的讨论也总能给我新的启发。",
    name: "社区成员",
    designation: "算法竞赛爱好者",
    company: "Open436",
    image: "https://randomuser.me/api/portraits/women/4.jpg",
  },
  {
    testimonial:
      "论坛的氛围很纯粹，提的技术问题总有人认真解答，资源板块也沉淀了大量优质学习资料。",
    name: "活跃用户",
    designation: "后端开发",
    company: "Open436",
    image: "https://randomuser.me/api/portraits/men/5.jpg",
  },
  {
    testimonial:
      "AI 助手结合社区知识库回答得很到位，赛事报名和排名也一目了然，是一个真正为技术人打造的平台。",
    name: "参赛选手",
    designation: "全栈方向",
    company: "Open436",
    image: "https://randomuser.me/api/portraits/women/6.jpg",
  },
];

const projects = [
  {
    name: "在线判题 OJ",
    description:
      "集成 HOJ 判题内核，支持多语言代码提交、沙箱隔离执行与自动评测，为编程训练与竞赛提供稳定的判题基础设施。",
    tags: [
      {
        name: "java",
        color: "blue-text-gradient",
      },
      {
        name: "docker",
        color: "green-text-gradient",
      },
      {
        name: "sandbox",
        color: "pink-text-gradient",
      },
    ],
    image: carrent,
    source_code_link: "https://github.com/",
  },
  {
    name: "编程赛事",
    description:
      "赛事日历、在线报名、实时排名与赛后复盘一体的竞赛平台，详情页集成评论区，打造从训练到竞技的完整闭环。",
    tags: [
      {
        name: "vue",
        color: "blue-text-gradient",
      },
      {
        name: "ranking",
        color: "green-text-gradient",
      },
      {
        name: "enroll",
        color: "pink-text-gradient",
      },
    ],
    image: jobit,
    source_code_link: "https://github.com/",
  },
  {
    name: "技术论坛",
    description:
      "多板块技术社区，支持发帖、评论、点赞、收藏、搜索与资源分享，配合 AI 助手沉淀高质量技术知识库。",
    tags: [
      {
        name: "vue",
        color: "blue-text-gradient",
      },
      {
        name: "ai",
        color: "green-text-gradient",
      },
      {
        name: "rag",
        color: "pink-text-gradient",
      },
    ],
    image: tripguide,
    source_code_link: "https://github.com/",
  },
];

export { services, technologies, experiences, testimonials, projects };
