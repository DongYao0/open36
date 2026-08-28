import React from "react";
import Tilt from "react-tilt";
import { motion } from "framer-motion";

import { styles } from "../styles";
import { github } from "../assets";
import { SectionWrapper } from "../hoc";
import { projects as defaultProjects } from "../constants";
import { useHomepage } from "../context/HomepageContext";
import { fadeIn, textVariant } from "../utils/motion";
import noimg from "../assets/noimg.svg";

const defaultWorks = {
  subText: "实验室荣誉",
  headText: "竞赛奖项.",
  description:
    "实验室鼓励成员积极参与各类学科竞赛，依托完善的技术指导体系，组织团队参与挑战杯、蓝桥杯、中国大学生计算机设计大赛等高水平学科赛事。历年参赛队伍多次斩获国家级、省级竞赛奖项，竞赛成果可用于综测加分、奖学金评定、考研复试与求职简历背书。众多成员以竞赛为契机夯实专业能力，拓展项目经验，实现综合能力持续提升。",
  items: defaultProjects,
};

const ProjectCard = ({
  index,
  name,
  description,
  tags,
  image,
  source_code_link,
}) => {
  return (
    <motion.div variants={fadeIn("up", "spring", index * 0.5, 0.75)}>
      <Tilt
        options={{
          max: 45,
          scale: 1,
          speed: 450,
        }}
        className='bg-tertiary p-5 rounded-2xl sm:w-[360px] w-full'
      >
        <div className='relative w-full h-[230px]'>
          <img
            src={image || noimg}
            alt={name || 'project'}
            className='w-full h-full object-cover rounded-2xl'
          />

          <div className='absolute inset-0 flex justify-end m-3 card-img_hover'>
            <div
              onClick={() => source_code_link && window.open(source_code_link, "_blank")}
              className='black-gradient w-10 h-10 rounded-full flex justify-center items-center cursor-pointer'
            >
              <img
                src={github}
                alt='source code'
                className='w-1/2 h-1/2 object-contain'
              />
            </div>
          </div>
        </div>

        <div className='mt-5'>
          <h3 className='text-white-100 font-bold text-[24px]'>{name}</h3>
          <p className='mt-2 text-secondary text-[14px] whitespace-pre-line'>{description}</p>
        </div>

        <div className='mt-4 flex flex-wrap gap-2'>
          {(tags || []).map((tag) => (
            <p
              key={`${name}-${tag.name}`}
              className={`text-[14px] ${tag.color}`}
            >
              #{tag.name}
            </p>
          ))}
        </div>
      </Tilt>
    </motion.div>
  );
};

const Works = () => {
  const { get } = useHomepage();
  const works = get("works", defaultWorks);
  const items = (Array.isArray(works.items) ? works.items : defaultProjects).map((project, index) => ({
    ...project,
    image: project.image || defaultProjects[index]?.image || "",
  }));

  return (
    <>
      <motion.div variants={textVariant()}>
        <p className={`${styles.sectionSubText} `}>{works.subText}</p>
        <h2 className={`${styles.sectionHeadText}`}>{works.headText}</h2>
      </motion.div>

      <div className='w-full flex'>
        <motion.p
          variants={fadeIn("", "", 0.1, 1)}
          className='mt-3 text-secondary text-[17px] max-w-3xl leading-[30px] whitespace-pre-line'
        >
          {works.description}
        </motion.p>
      </div>

      <div className='mt-20 flex flex-wrap gap-7'>
        {items.map((project, index) => (
          <ProjectCard key={`project-${(project.name || '') + index}`} index={index} {...project} />
        ))}
      </div>
    </>
  );
};

export default SectionWrapper(Works, "");
