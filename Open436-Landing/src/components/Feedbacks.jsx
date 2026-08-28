import React from "react";
import { motion } from "framer-motion";

import { styles } from "../styles";
import { SectionWrapper } from "../hoc";
import { fadeIn, textVariant } from "../utils/motion";
import { testimonials as defaultTestimonials } from "../constants";
import { useHomepage } from "../context/HomepageContext";
import noimg from "../assets/noimg.svg";

const defaultFeedbacks = {
  subText: "社区声音",
  headText: "学长学姐寄语.",
  items: defaultTestimonials,
};

const FeedbackCard = ({
  index,
  testimonial,
  name,
  designation,
  company,
  image,
}) => (
  <motion.div
    variants={fadeIn("", "spring", index * 0.5, 0.75)}
    className='bg-black-200 p-10 rounded-3xl xs:w-[320px] w-full'
  >
    <p className='text-white-100 font-black text-[48px]'>"</p>

    <div className='mt-1'>
      <p className='text-white-100 tracking-wider text-[18px] whitespace-pre-line'>{testimonial}</p>

      <div className='mt-7 flex justify-between items-center gap-1'>
        <div className='flex-1 flex flex-col'>
          <p className='text-white-100 font-medium text-[16px]'>
            <span className='blue-text-gradient'>@</span> {name}
          </p>
          <p className='mt-1 text-secondary text-[12px]'>
            {[designation, company].filter(Boolean).join(' · ')}
          </p>
        </div>

        <img
          src={image || noimg}
          alt={`feedback_by-${name || 'user'}`}
          className='w-10 h-10 rounded-full object-cover'
        />
      </div>
    </div>
  </motion.div>
);

const Feedbacks = () => {
  const { get } = useHomepage();
  const feedbacks = get("feedbacks", defaultFeedbacks);
  const items = Array.isArray(feedbacks.items) ? feedbacks.items : defaultTestimonials;

  return (
    <div className={`mt-12 bg-black-100 rounded-[20px]`}>
      <div
        className={`bg-tertiary rounded-2xl ${styles.padding} min-h-[300px]`}
      >
        <motion.div variants={textVariant()}>
          <p className={styles.sectionSubText}>{feedbacks.subText}</p>
          <h2 className={styles.sectionHeadText}>{feedbacks.headText}</h2>
        </motion.div>
      </div>
      <div className={`-mt-20 pb-14 ${styles.paddingX} flex flex-wrap gap-7`}>
        {items.map((testimonial, index) => (
          <FeedbackCard key={index} index={index} {...testimonial} />
        ))}
      </div>
    </div>
  );
};

export default SectionWrapper(Feedbacks, "");
