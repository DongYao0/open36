import React from "react";
import Tilt from "react-tilt";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import { styles } from "../styles";
import { SectionWrapper } from "../hoc";
import { useHomepage } from "../context/HomepageContext";
import { defaultHonorProjects, honorGallery, withHonorAlbums } from "../data/honorGallery";
import { fadeIn, textVariant } from "../utils/motion";
import noimg from "../assets/noimg.svg";

const defaultWorks = {
  subText: "实验室荣誉",
  headText: "竞赛奖项.",
  description:
    "实验室鼓励成员积极参与各类学科竞赛，依托完善的技术指导体系，组织团队参与挑战杯、蓝桥杯、中国大学生计算机设计大赛等高水平学科赛事。历年参赛队伍多次斩获国家级、省级竞赛奖项，竞赛成果可用于综测加分、奖学金评定、考研复试与求职简历背书。众多成员以竞赛为契机夯实专业能力，拓展项目经验，实现综合能力持续提升。",
  items: defaultHonorProjects,
  gallery: honorGallery,
};

const ProjectCard = ({
  index,
  name,
  description,
  tags,
  image,
  onOpen,
  albumCount,
}) => {
  return (
    <motion.div
      variants={fadeIn("up", "spring", index * 0.5, 0.75)}
      role='link'
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(event) => (event.key === "Enter" || event.key === " ") && onOpen()}
      className='cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 rounded-2xl'
    >
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

          <div className='absolute inset-0 flex items-end justify-end p-3 card-img_hover'>
            <span className='rounded-full border border-white/20 bg-black/60 px-4 py-2 text-xs font-semibold tracking-wider text-white backdrop-blur'>
              查看相册 · {albumCount} 张 ↗
            </span>
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
  const navigate = useNavigate();
  const works = get("works", defaultWorks);
  const legacyGallery = Array.isArray(works.gallery) ? works.gallery : honorGallery;
  const items = withHonorAlbums(works.items, legacyGallery).map((project, index) => ({
    ...project,
    image: project.image || defaultHonorProjects[index]?.image || "",
    albumCount: project.gallery.length,
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
          <ProjectCard
            key={`project-${(project.name || '') + index}`}
            index={index}
            {...project}
            onOpen={() => navigate(`/honors/${index}`)}
          />
        ))}
      </div>
    </>
  );
};

export default SectionWrapper(Works, "");
