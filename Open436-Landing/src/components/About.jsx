import React from "react";
import Tilt from "react-tilt";
import { motion } from "framer-motion";

import { styles } from "../styles";
import { defaultAbout, services as defaultServices } from "../constants";
import { useHomepage } from "../context/HomepageContext";
import { SectionWrapper } from "../hoc";
import { fadeIn, textVariant } from "../utils/motion";
import noimg from "../assets/noimg.svg";

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
          src={icon || noimg}
          alt={title || 'service'}
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
  const { get } = useHomepage();
  const about = get("about", defaultAbout);
  const services = (Array.isArray(about.services) ? about.services : []).map((service, index) => ({
    ...service,
    icon: service.icon || defaultServices[index]?.icon || "",
  }));

  return (
    <>
      <motion.div variants={textVariant()}>
        <p className={styles.sectionSubText}>{about.subText}</p>
        <h2 className={styles.sectionHeadText}>{about.headText}</h2>
      </motion.div>

      <motion.p
        variants={fadeIn("", "", 0.1, 1)}
        className='mt-4 text-secondary text-[17px] max-w-3xl leading-[30px] whitespace-pre-line'
      >
        {about.description}
      </motion.p>

      <div className='mt-20 flex flex-wrap gap-10'>
        {services.map((service, index) => (
          <ServiceCard key={(service.title || '') + index} index={index} {...service} />
        ))}
      </div>
    </>
  );
};

export default SectionWrapper(About, "about");
