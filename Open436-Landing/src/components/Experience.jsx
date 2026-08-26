import React from "react";
import {
  VerticalTimeline,
  VerticalTimelineElement,
} from "react-vertical-timeline-component";
import { motion } from "framer-motion";

import "react-vertical-timeline-component/style.min.css";

import { styles } from "../styles";
import { experiences } from "../constants";
import { SectionWrapper } from "../hoc";
import { textVariant } from "../utils/motion";

const ExperienceCard = ({ experience }) => {
  return (
    <VerticalTimelineElement
      contentStyle={{
        background: "#1d1836",
        color: "#fff",
      }}
      contentArrowStyle={{ borderRight: "7px solid  #232631" }}
      date={experience.date}
      iconStyle={{ background: experience.iconBg }}
      icon={
        <div className='flex justify-center items-center w-full h-full'>
          <img
            src={experience.icon}
            alt={experience.company_name}
            className='w-[60%] h-[60%] object-contain'
          />
        </div>
      }
    >
      <div>
        <h3 className='text-white-100 text-[24px] font-bold'>{experience.title}</h3>
        <p
          className='text-secondary text-[16px] font-semibold'
          style={{ margin: 0 }}
        >
          {experience.company_name}
        </p>
      </div>

      <ul className='mt-5 list-disc ml-5 space-y-2'>
        {experience.points.map((point, index) => {
          // 关键词加粗
          const keywords = [
            "985、211", "专业第一名", "挑战杯一等奖", "蓝桥杯",
            "一对一全程带教", "自研项目", "简历",
            "独立服务器", "双屏工点", "人体工学椅", "全天开放",
            "团建活动", "互助氛围"
          ];
          let formattedPoint = point;
          keywords.forEach(kw => {
            formattedPoint = formattedPoint.replace(
              new RegExp(kw.replace(/、/g, '、'), 'g'),
              `**${kw}**`
            );
          });
          // 处理 ** 加粗标记
          const parts = formattedPoint.split(/(\*\*[^*]+\*\*)/);
          return (
            <li
              key={`experience-point-${index}`}
              className='text-white-100 text-[14px] pl-1 tracking-wider'
            >
              {parts.map((part, i) =>
                part.startsWith('**') ? (
                  <span key={i} className='text-white font-bold text-[16px]'>{part.slice(2, -2)}</span>
                ) : (
                  <span key={i}>{part}</span>
                )
              )}
            </li>
          );
        })}
      </ul>
    </VerticalTimelineElement>
  );
};

const Experience = () => {
  return (
    <>
      <motion.div variants={textVariant()}>
        <p className={`${styles.sectionSubText} text-center`}>
          核心优势
        </p>
        <h2 className={`${styles.sectionHeadText} text-center`}>
          实验室功能.
        </h2>
      </motion.div>

      <div className='mt-20 flex flex-col'>
        <VerticalTimeline>
          {experiences.map((experience, index) => (
            <ExperienceCard
              key={`experience-${index}`}
              experience={experience}
            />
          ))}
        </VerticalTimeline>
      </div>
    </>
  );
};

export default SectionWrapper(Experience, "work");
