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

import lanqiao from "../assets/lanqiao.png";

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
    iconBg: "#ffffff",
    points: [
      "学业升学成果突出，实验室往届学长学姐连续两年拿下计算机学院专业第一名，多名成员成功上岸985、211 重点院校，为学弟学妹提供成熟升学指导路径。",
      "国家级赛事奖项丰厚，团队先后斩获挑战杯一等奖、中国大学生计算机设计大赛国三、蓝桥杯省赛一二三等奖及全国总决赛奖项，覆盖 Java、C/C++ 多赛道，赛事成果可直接用于综测加分、奖学金评定、考研复试与校招简历背书。",
    ],
  },
  {
    title: "培训实战优势",
    company_name: "Advantages of Training & Practical Development",
    icon: training,
    iconBg: "#ffffff",
    points: [
      "拥有前后端完整分层教学体系，学长学姐一对一全程带教，零基础可循序渐进上手主流开发技术。",
      "坐拥多款全栈、AI 落地自研项目，可查看完整源码，积累能够直接写入简历的开发实战经历。",
    ],
  },
  {
    title: "硬件环境优势",
    company_name: "Advantages of Hardware & Study Environment",
    icon: hardware,
    iconBg: "#ffffff",
    points: [
      "配备独立服务器、双屏工位、人体工学椅，搭配打印机、冰箱、中央空调，学习生活配套齐全。",
      "实验室全天开放，空间宽敞整洁，随时可进入开展编程学习与项目研发。",
    ],
  },
  {
    title: "团队氛围优势",
    company_name: "Advantages of Team Atmosphere",
    icon: team,
    iconBg: "#ffffff",
    points: [
      "定期组织聚餐、桌游、剧本杀等团建活动，平衡学习与休闲，舒缓日常学习压力。",
      "团队互助氛围浓厚，学长无偿分享竞赛、考研、求职经验，大家互帮互助共同进步。",
    ],
  },
];

const testimonials = [
  {
    testimonial:
      "愿大家在实验室保持热爱，深耕算法、坚持思考，在一次次训练与竞赛中突破自我，奔赴心中目标。",
    name: "往届学姐",
    designation: "算法竞赛方向",
    company: "Open436",
    image: "https://randomuser.me/api/portraits/women/4.jpg",
  },
  {
    testimonial:
      "珍惜并肩学习的时光，大胆提问、动手实践。在这里沉淀的技术与友谊，终将成为前行路上珍贵的财富。",
    name: "往届学长",
    designation: "后端开发方向",
    company: "Open436",
    image: "https://randomuser.me/api/portraits/men/5.jpg",
  },
  {
    testimonial:
      "沉下心打磨项目，积极参与科创竞赛。希望各位脚踏实地，学有所成，在考研与求职赛道收获满意答卷。",
    name: "往届学长",
    designation: "全栈开发方向",
    company: "Open436",
    image: "https://randomuser.me/api/portraits/women/6.jpg",
  },
];

const projects = [
  {
    name: "蓝桥杯大赛",
    description:
      "组织实验室成员组队参与蓝桥杯竞赛，覆盖 Java、C/C++ 主流赛道，依托常态化刷题训练与赛前集中辅导，多名成员斩获省级一、二、三等奖及全国总决赛奖项，夯实算法编程核心能力。",
    image: lanqiao,
    tags: [
      {
        name: "算法竞赛",
        color: "blue-text-gradient",
      },
      {
        name: "C++",
        color: "green-text-gradient",
      },
      {
        name: "Java",
        color: "pink-text-gradient",
      },
    ],
    source_code_link: "https://github.com/",
  },
  {
    name: "中国大学生计算机设计大赛",
    description:
      "围绕软件开发、人工智能、大数据等赛道组建参赛队伍，从选题、开发到作品打磨全程指导，往届团队斩获国家级、省级奖项，锻炼完整项目开发与作品答辩能力。",
    tags: [
      {
        name: "全栈开发",
        color: "blue-text-gradient",
      },
      {
        name: "AI 项目",
        color: "green-text-gradient",
      },
      {
        name: "作品答辩",
        color: "pink-text-gradient",
      },
    ],
    image: jobit,
    source_code_link: "https://github.com/",
  },
  {
    name: "挑战杯科创竞赛",
    description:
      "聚焦科创创新课题，支持跨方向组队开展项目研发，配备学长全程指导项目撰写与路演准备，团队多次获得各级赛事荣誉，培养创新思维与团队协作能力。",
    tags: [
      {
        name: "科创项目",
        color: "blue-text-gradient",
      },
      {
        name: "创新实践",
        color: "green-text-gradient",
      },
      {
        name: "路演备赛",
        color: "pink-text-gradient",
      },
    ],
    image: tripguide,
    source_code_link: "https://github.com/",
  },
];

export { services, technologies, experiences, testimonials, projects };
