const honorGallerySource = [
  { title: "第22届百度之星 · 金奖", category: "百度之星", level: "金奖", image: "/honors/baidu/01.jpg", thumbnail: "/honors/baidu/thumbs/01.jpg" },
  { title: "第22届百度之星 · 金奖", category: "百度之星", level: "金奖", image: "/honors/baidu/02.jpg", thumbnail: "/honors/baidu/thumbs/02.jpg" },
  { title: "第22届百度之星 · 银奖", category: "百度之星", level: "银奖", image: "/honors/baidu/03.jpg", thumbnail: "/honors/baidu/thumbs/03.jpg" },
  { title: "第22届百度之星 · 铜奖", category: "百度之星", level: "铜奖", image: "/honors/baidu/04.jpg", thumbnail: "/honors/baidu/thumbs/04.jpg" },
  { title: "第22届百度之星 · 铜奖", category: "百度之星", level: "铜奖", image: "/honors/baidu/05.jpg", thumbnail: "/honors/baidu/thumbs/05.jpg" },
  { title: "第22届百度之星 · 银奖", category: "百度之星", level: "银奖", image: "/honors/baidu/06.jpg", thumbnail: "/honors/baidu/thumbs/06.jpg" },
  { title: "2023至2024学年 · 三好学生", category: "个人荣誉", level: "校级荣誉", image: "/honors/personal/01.jpg", thumbnail: "/honors/personal/thumbs/01.jpg" },
  { title: "2023至2024学年 · 优秀大学生奖学金", category: "个人荣誉", level: "奖学金", image: "/honors/personal/02.jpg", thumbnail: "/honors/personal/thumbs/02.jpg" },
  { title: "2023至2024学年 · 优秀共青团员", category: "个人荣誉", level: "校级荣誉", image: "/honors/personal/03.jpg", thumbnail: "/honors/personal/thumbs/03.jpg" },
  { title: "2024至2025学年 · 国家奖学金", category: "个人荣誉", level: "国家奖学金", image: "/honors/personal/04.jpg", thumbnail: "/honors/personal/thumbs/04.jpg" },
  { title: "第17届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/01.jpg", thumbnail: "/honors/lanqiao/thumbs/01.jpg" },
  { title: "第17届蓝桥杯 · 全国三等奖", category: "蓝桥杯", level: "国家级三等奖", image: "/honors/lanqiao/02.jpg", thumbnail: "/honors/lanqiao/thumbs/02.jpg" },
  { title: "第17届蓝桥杯 · 省一等奖", category: "蓝桥杯", level: "省级一等奖", image: "/honors/lanqiao/03.jpg", thumbnail: "/honors/lanqiao/thumbs/03.jpg" },
  { title: "第17届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/04.jpg", thumbnail: "/honors/lanqiao/thumbs/04.jpg" },
  { title: "第17届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/05.jpg", thumbnail: "/honors/lanqiao/thumbs/05.jpg" },
  { title: "第17届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/06.jpg", thumbnail: "/honors/lanqiao/thumbs/06.jpg" },
  { title: "第17届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/07.jpg", thumbnail: "/honors/lanqiao/thumbs/07.jpg" },
  { title: "第15届蓝桥杯 · 省三等奖", category: "蓝桥杯", level: "省级三等奖", image: "/honors/lanqiao/08.jpg", thumbnail: "/honors/lanqiao/thumbs/08.jpg" },
  { title: "第15届蓝桥杯 · 省三等奖", category: "蓝桥杯", level: "省级三等奖", image: "/honors/lanqiao/09.jpg", thumbnail: "/honors/lanqiao/thumbs/09.jpg" },
  { title: "第16届蓝桥杯 · 省一等奖", category: "蓝桥杯", level: "省级一等奖", image: "/honors/lanqiao/10.jpg", thumbnail: "/honors/lanqiao/thumbs/10.jpg" },
  { title: "第15届蓝桥杯 · 省一等奖", category: "蓝桥杯", level: "省级一等奖", image: "/honors/lanqiao/11.jpg", thumbnail: "/honors/lanqiao/thumbs/11.jpg" },
  { title: "第15届蓝桥杯 · 省一等奖", category: "蓝桥杯", level: "省级一等奖", image: "/honors/lanqiao/12.jpg", thumbnail: "/honors/lanqiao/thumbs/12.jpg" },
  { title: "第15届蓝桥杯 · 省三等奖", category: "蓝桥杯", level: "省级三等奖", image: "/honors/lanqiao/13.jpg", thumbnail: "/honors/lanqiao/thumbs/13.jpg" },
  { title: "第15届蓝桥杯 · 省三等奖", category: "蓝桥杯", level: "省级三等奖", image: "/honors/lanqiao/14.jpg", thumbnail: "/honors/lanqiao/thumbs/14.jpg" },
  { title: "第16届蓝桥杯 · 全国三等奖", category: "蓝桥杯", level: "国家级三等奖", image: "/honors/lanqiao/15.jpg", thumbnail: "/honors/lanqiao/thumbs/15.jpg" },
  { title: "第16届蓝桥杯 · 省一等奖", category: "蓝桥杯", level: "省级一等奖", image: "/honors/lanqiao/16.jpg", thumbnail: "/honors/lanqiao/thumbs/16.jpg" },
  { title: "第16届蓝桥杯 · 省三等奖", category: "蓝桥杯", level: "省级三等奖", image: "/honors/lanqiao/17.jpg", thumbnail: "/honors/lanqiao/thumbs/17.jpg" },
  { title: "第15届蓝桥杯 · 全国二等奖", category: "蓝桥杯", level: "国家级二等奖", image: "/honors/lanqiao/18.jpg", thumbnail: "/honors/lanqiao/thumbs/18.jpg" },
  { title: "第16届蓝桥杯 · 省三等奖", category: "蓝桥杯", level: "省级三等奖", image: "/honors/lanqiao/19.jpg", thumbnail: "/honors/lanqiao/thumbs/19.jpg" },
  { title: "第15届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/20.jpg", thumbnail: "/honors/lanqiao/thumbs/20.jpg" },
  { title: "第15届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/21.jpg", thumbnail: "/honors/lanqiao/thumbs/21.jpg" },
  { title: "第16届蓝桥杯 · 省二等奖", category: "蓝桥杯", level: "省级二等奖", image: "/honors/lanqiao/22.jpg", thumbnail: "/honors/lanqiao/thumbs/22.jpg" },
  { title: "第8届码蹄杯 · 省金奖", category: "码蹄杯", level: "省级金奖", image: "/honors/mati/01.jpg", thumbnail: "/honors/mati/thumbs/01.jpg" },
  { title: "第8届码蹄杯 · 省金奖", category: "码蹄杯", level: "省级金奖", image: "/honors/mati/02.jpg", thumbnail: "/honors/mati/thumbs/02.jpg" },
  { title: "第8届码蹄杯 · 省银奖", category: "码蹄杯", level: "省级银奖", image: "/honors/mati/03.jpg", thumbnail: "/honors/mati/thumbs/03.jpg" },
  { title: "第8届码蹄杯 · 省铜奖", category: "码蹄杯", level: "省级铜奖", image: "/honors/mati/04.jpg", thumbnail: "/honors/mati/thumbs/04.jpg" },
  { title: "第8届码蹄杯 · 省铜奖", category: "码蹄杯", level: "省级铜奖", image: "/honors/mati/05.jpg", thumbnail: "/honors/mati/thumbs/05.jpg" },
  { title: "第8届码蹄杯 · 优秀教练", category: "码蹄杯", level: "优秀教练", image: "/honors/mati/06.jpg", thumbnail: "/honors/mati/thumbs/06.jpg" },
  { title: "第8届码蹄杯 · 省铜奖", category: "码蹄杯", level: "省级铜奖", image: "/honors/mati/07.jpg", thumbnail: "/honors/mati/thumbs/07.jpg" },
  { title: "第8届码蹄杯 · 省银奖", category: "码蹄杯", level: "省级银奖", image: "/honors/mati/08.jpg", thumbnail: "/honors/mati/thumbs/08.jpg" },
  { title: "第18届挑战杯 · 恒星级作品一等奖", category: "团队项目赛", level: "一等奖", image: "/honors/team/01.jpg", thumbnail: "/honors/team/thumbs/01.jpg" },
  { title: "第18届计算机设计大赛省赛 · 一等奖", category: "团队项目赛", level: "省级一等奖", image: "/honors/team/02.jpg", thumbnail: "/honors/team/thumbs/02.jpg" },
  { title: "第18届计算机设计大赛省赛 · 三等奖", category: "团队项目赛", level: "省级三等奖", image: "/honors/team/03.jpg", thumbnail: "/honors/team/thumbs/03.jpg" },
  { title: "第18届计算机设计大赛省赛 · 一等奖", category: "团队项目赛", level: "省级一等奖", image: "/honors/team/04.jpg", thumbnail: "/honors/team/thumbs/04.jpg" },
  { title: "第19届计算机设计大赛省赛 · 一等奖", category: "团队项目赛", level: "省级一等奖", image: "/honors/team/05.jpg", thumbnail: "/honors/team/thumbs/05.jpg" },
  { title: "第19届计算机设计大赛省赛 · 一等奖", category: "团队项目赛", level: "省级一等奖", image: "/honors/team/06.jpg", thumbnail: "/honors/team/thumbs/06.jpg" },
  { title: "2026中国机器人大赛 · 三等奖", category: "团队项目赛", level: "三等奖", image: "/honors/team/07.jpg", thumbnail: "/honors/team/thumbs/07.jpg" },
  { title: "第27届机器人及人工智能大赛 · 三等奖", category: "团队项目赛", level: "三等奖", image: "/honors/team/08.jpg", thumbnail: "/honors/team/thumbs/08.jpg" },
  { title: "第27届机器人及人工智能大赛 · 三等奖", category: "团队项目赛", level: "三等奖", image: "/honors/team/09.jpg", thumbnail: "/honors/team/thumbs/09.jpg" },
  { title: "第27届机器人及人工智能大赛 · 三等奖", category: "团队项目赛", level: "三等奖", image: "/honors/team/10.jpg", thumbnail: "/honors/team/thumbs/10.jpg" },
  { title: "第28届机器人及人工智能大赛 · 三等奖", category: "团队项目赛", level: "三等奖", image: "/honors/team/11.jpg", thumbnail: "/honors/team/thumbs/11.jpg" },
  { title: "第28届机器人及人工智能大赛 · 三等奖", category: "团队项目赛", level: "三等奖", image: "/honors/team/12.jpg", thumbnail: "/honors/team/thumbs/12.jpg" },
];

const recipients = {
  baidu: ["葛露辉", "林城", "乔中乐", "时慧杰", "田涛", "尹讯哲"],
  personal: ["杨雅岚", "杨雅岚", "杨雅岚", "杨雅岚"],
  lanqiao: ["贾凡", "林城", "林城", "刘思涵", "刘彦笑", "王严", "尹讯哲", "丁雅文", "梁悦", "林城", "时慧杰", "时慧杰", "孙宇昂", "王景然", "王瑞聪", "王瑞聪", "王严", "王一方", "杨雅岚", "张佳乐", "张婷", "赵满"],
  mati: ["葛露怿", "林城", "乔申乐", "时慧杰", "田涛", "王广超", "杨雅岚", "尹讯哲"],
  team: Array(12).fill("Open436 参赛团队"),
};

const years = {
  baidu: Array(6).fill(2026),
  personal: [2024, 2024, 2024, 2025],
  lanqiao: [2026, 2026, 2026, 2026, 2026, 2026, 2026, 2024, 2024, 2025, 2024, 2024, 2024, 2024, 2025, 2025, 2025, 2024, 2025, 2024, 2024, 2025],
  mati: Array(8).fill(2026),
  team: [2023, 2025, 2025, 2025, 2026, 2026, 2026, 2025, 2025, 2025, 2026, 2026],
};

const levelWeight = (level = "") => {
  const scope = /国家|全国/.test(level) ? 200 : /省级|省/.test(level) ? 100 : 0;
  const rank = /金奖|一等奖/.test(level) ? 40 : /银奖|二等奖/.test(level) ? 30 : /铜奖|三等奖/.test(level) ? 20 : 10;
  return scope + rank;
};

export const sortHonorGallery = (photos = []) => [...photos].sort((a, b) => {
  const getYear = (value) => Number(String(value || "").match(/\d{4}/)?.[0] || 0);
  const timeDiff = getYear(b.year) - getYear(a.year);
  return timeDiff || levelWeight(b.level) - levelWeight(a.level) || Number(a.sortOrder || 0) - Number(b.sortOrder || 0);
});

export const honorGallery = honorGallerySource.map((item, sourceIndex) => {
  const match = item.image.match(/\/honors\/([^/]+)\/(\d+)\.jpg$/);
  const group = match?.[1] || "team";
  const index = Number(match?.[2] || 1) - 1;
  const level = group === "baidu" ? `省级${item.level}`
    : group === "team" && index === 0 ? "国家级一等奖"
      : group === "team" && index === 6 ? "国家级三等奖" : item.level;
  return { ...item, level, recipient: recipients[group]?.[index] || "Open436 参赛团队", year: years[group]?.[index] || "", sortOrder: sourceIndex };
});

export const defaultHonorProjects = [
  { name: "蓝桥杯大赛", description: "从省赛到全国总决赛，记录实验室成员在算法赛场上的持续突破。", image: "/honors/lanqiao/02.jpg", tags: [] },
  { name: "码蹄杯算法竞赛", description: "以限时编程检验算法功底，在高强度实战中锻炼解题能力。", image: "/honors/mati/01.jpg", tags: [] },
  { name: "百度之星算法竞赛", description: "面向高水平程序设计挑战，展现实验室成员的算法实力。", image: "/honors/baidu/01.jpg", tags: [] },
  { name: "团队项目赛", description: "覆盖挑战杯、计算机设计大赛与机器人赛事，见证团队协作成果。", image: "/honors/team/07.jpg", tags: [] },
  { name: "个人荣誉", description: "收录国家奖学金、三好学生等学业与综合表现荣誉。", image: "/honors/personal/04.jpg", tags: [] },
];

export const projectGallery = (project, legacyGallery = honorGallery) => {
  if (Array.isArray(project?.gallery)) return sortHonorGallery(project.gallery);
  const name = String(project?.name || "");
  const keyword = name.includes("蓝桥") ? "蓝桥" : /[马码]蹄/.test(name) ? "码蹄" : name.includes("百度之星") ? "百度之星" : name.includes("个人荣誉") ? "个人荣誉" : "团队项目赛";
  return sortHonorGallery(legacyGallery.filter((photo) => `${photo.category || ""}${photo.title || ""}`.includes(keyword)));
};

export const withHonorAlbums = (items, legacyGallery = honorGallery) => {
  const source = Array.isArray(items) && items.length ? [...items] : [...defaultHonorProjects];
  if (!source.some((item) => String(item.name || "").includes("个人荣誉"))) source.push(defaultHonorProjects[4]);
  return source.map((item) => ({ ...item, gallery: projectGallery(item, legacyGallery) }));
};
