import React from "react";
import Tilt from "react-tilt";
import { motion } from "framer-motion";

import { styles } from "../styles";
import { services } from "../constants";
import { SectionWrapper } from "../hoc";
import { fadeIn, textVariant } from "../utils/motion";

const ServiceCard = ({ index, title, icon }) => (
  <Tilt className='xs:w-[250px] w-full'>
    <motion.div
      variants={fadeIn("right", "spring", index * 0.5, 0.75)}
      className='w-full green-pink-gradient p-[1px] rounded-[20px] shadow-card'
    >
      <div
        options={{
          max: 45,
          scale: 1,
          speed: 450,
        }}
        className='bg-tertiary rounded-[20px] py-5 px-12 min-h-[280px] flex justify-evenly items-center flex-col'
      >
        <img
          src={icon}
          alt='web-development'
          className='w-16 h-16 object-contain'
        />

        <h3 className='text-white-100 text-[20px] font-bold text-center'>
          {title}
        </h3>
      </div>
    </motion.div>
  </Tilt>
);

const About = () => {
  return (
    <>
      <motion.div variants={textVariant()}>
        <p className={styles.sectionSubText}>实验室介绍</p>
        <h2 className={styles.sectionHeadText}>关于0436.</h2>
      </motion.div>

      <motion.p
        variants={fadeIn("", "", 0.1, 1)}
        className='mt-4 text-secondary text-[17px] max-w-3xl leading-[30px]'
      >
        0436 系统设计实验室专注前后端开发、智能计算与 AI 创新，为计算机专业学生
        提供系统化分层编程培训，拥有完善的前端、后端完整学习路线；实验室成员学业
        成绩优异，在挑战杯、计算机设计大赛、蓝桥杯等国家级赛事斩获多项一二三等奖；
        团队自主研发 Queue 学习平台、LeSoun AI 音乐创作等实战项目，还有多学科合作
        研发任务；实验室硬件配置顶配，配有独立服务器、双屏工位、打印机、冰箱与双
        中央空调，环境舒适；日常会组织聚餐、剧本杀等团建活动，学习氛围轻松互助，
        零基础同学也能得到学长学姐全程带教，欢迎热爱编程、竞赛、开发的同学加入
        QQ 群了解纳新详情。
      </motion.p>

      <div className='mt-20 flex flex-wrap gap-10'>
        {services.map((service, index) => (
          <ServiceCard key={service.title} index={index} {...service} />
        ))}
      </div>
    </>
  );
};

export default SectionWrapper(About, "about");
