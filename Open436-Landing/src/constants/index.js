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

import competition from "../assets/advantages/competition.png";
import training from "../assets/advantages/training.png";
import hardware from "../assets/advantages/hardware.png";
import team from "../assets/advantages/team.png";

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
    title: "竞赛升学优势",
    company_name: "Advantages in Competition & Further Study",
    icon: competition,
    iconBg: "#383E56",
    points: [
      "学业升学成果突出，实验室往届学长学姐连续两年拿下计算机学院专业第一名，多名成员成功上岸985、211 重点院校，为学弟学妹提供成熟升学指导路径。",
      "国家级赛事奖项丰厚，团队先后斩获挑战杯一等奖、中国大学生计算机设计大赛国三、蓝桥杯省赛一二三等奖及全国总决赛奖项，覆盖 Java、C/C++ 多赛道，赛事成果可直接用于综测加分、奖学金评定、考研复试与校招简历背书。",
    ],
  },
  {
    title: "培训实战优势",
    company_name: "Advantages of Training & Practical Development",
    icon: training,
    iconBg: "#E6DEDD",
    points: [
      "拥有前后端完整分层教学体系，学长学姐一对一全程带教，零基础可循序渐进上手主流开发技术。",
      "坐拥多款全栈、AI 落地自研项目，可查看完整源码，积累能够直接写入简历的开发实战经历。",
    ],
  },
  {
    title: "硬件环境优势",
    company_name: "Advantages of Hardware & Study Environment",
    icon: hardware,
    iconBg: "#383E56",
    points: [
      "配备独立服务器、双屏工位、人体工学椅，搭配打印机、冰箱、中央空调，学习生活配套齐全。",
      "实验室全天开放，空间宽敞整洁，随时可进入开展编程学习与项目研发。",
    ],
  },
  {
    title: "团队氛围优势",
    company_name: "Advantages of Team Atmosphere",
    icon: team,
    iconBg: "#E6DEDD",
    points: [
      "定期组织聚餐、桌游、剧本杀等团建活动，平衡学习与休闲，舒缓日常学习压力。",
      "团队互助氛围浓厚，学长无偿分享竞赛、考研、求职经验，大家互帮互助共同进步。",
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
