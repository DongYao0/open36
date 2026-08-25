import React from "react";
import { motion } from "framer-motion";

import { EarthCanvas } from "./canvas";
import { SectionWrapper } from "../hoc";
import { slideIn } from "../utils/motion";

const Contact = () => {
  return (
    <div
      className='xl:mt-12 grid items-center gap-6 overflow-hidden lg:grid-cols-[minmax(0,0.85fr)_minmax(420px,1.15fr)] lg:gap-8'
    >
      <motion.div
        variants={slideIn("left", "tween", 0.2, 1)}
        className='relative isolate max-w-xl overflow-hidden rounded-[2rem] border border-white/10 bg-[#120f2f]/80 px-8 py-9 shadow-[0_24px_80px_rgba(15,8,48,0.45)] backdrop-blur-md sm:px-10'
      >
        <div aria-hidden='true' className='absolute -right-20 -top-20 -z-10 h-56 w-56 rounded-full bg-[#7c5cff]/20 blur-3xl' />
        <p className='mb-5 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.28em] text-[#b8a5ff]'>
          <span className='h-px w-8 bg-current' /> 招新通道已开启
        </p>
        <h2 className='max-w-md text-4xl font-black leading-[1.08] text-white sm:text-5xl'>
          让下一段代码，
          <span className='block text-[#b8a5ff]'>从 Open436 起航。</span>
        </h2>
        <p className='mt-6 max-w-md text-base leading-7 text-[#c8c2dc]'>
          填写报名信息，选择感兴趣的技术方向，和一群热爱创造的人一起把想法变成作品。
        </p>
        <div className='mt-7 flex flex-wrap gap-x-5 gap-y-2 text-sm text-[#ded9f2]'>
          <span>01 · 提交申请</span>
          <span>02 · 进入审核</span>
          <span>03 · 加入社区</span>
        </div>
        <a
          href='/app/login?mode=register'
          className='group mt-9 inline-flex items-center gap-4 rounded-full bg-[#b8a5ff] px-6 py-3.5 text-base font-bold text-[#120f2f] shadow-[0_12px_32px_rgba(139,108,255,0.3)] transition duration-300 hover:-translate-y-1 hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d8ceff]'
        >
          前往报名
          <span aria-hidden='true' className='grid h-7 w-7 place-items-center rounded-full bg-[#120f2f] text-[#d8ceff] transition-transform duration-300 group-hover:translate-x-1'>→</span>
        </a>
      </motion.div>
      <motion.div
        variants={slideIn("right", "tween", 0.2, 1)}
        className='h-[350px] w-full md:h-[500px] xl:h-[600px]'
      >
        <EarthCanvas />
      </motion.div>
    </div>
  );
};

export default SectionWrapper(Contact, "contact");
