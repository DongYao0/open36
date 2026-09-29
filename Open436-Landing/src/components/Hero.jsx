import { lazy, Suspense } from "react";
import { motion } from "framer-motion";

import { styles } from "../styles";
import DeferredRender from "./DeferredRender";

const ComputersCanvas = lazy(() => import("./canvas/Computers"));

const ComputerPlaceholder = () => (
  <div className='absolute inset-0 flex items-center justify-center pt-32' aria-hidden='true'>
    <div className='relative h-40 w-64 animate-pulse rounded-2xl border border-violet-300/20 bg-violet-500/5 shadow-[0_0_80px_rgba(145,94,255,0.14)] sm:h-52 sm:w-80'>
      <div className='absolute inset-3 rounded-xl border border-white/5 bg-gradient-to-br from-violet-400/10 to-transparent' />
      <div className='absolute -bottom-7 left-1/2 h-7 w-2 -translate-x-1/2 bg-violet-300/15' />
      <div className='absolute -bottom-9 left-1/2 h-2 w-20 -translate-x-1/2 rounded-full bg-violet-300/15' />
    </div>
  </div>
);

const Hero = () => {
  return (
    <section className={`relative w-full h-screen mx-auto`}>
      <div
        className={`absolute inset-0 top-[120px]  max-w-7xl mx-auto ${styles.paddingX} flex flex-row items-start gap-5`}
      >
        <div className='flex flex-col justify-center items-center mt-5'>
          <div className='w-5 h-5 rounded-full bg-[#915EFF]' />
          <div className='w-1 sm:h-80 h-40 violet-gradient' />
        </div>

        <div>
          <h1 className={`${styles.heroHeadText} text-white-100`}>
            <span className='text-[#915EFF]'>OPEN</span>436
          </h1>
          <p className={`${styles.heroSubText} mt-2 text-white-100`}>
            为技术而生的开放协作平台 <br className='sm:block hidden' />
            在线判题 · 编程赛事 · 技术社区 · 资源分享
          </p>
        </div>
      </div>

      <DeferredRender
        className='absolute inset-0'
        minHeight='100vh'
        rootMargin='0px'
        idle
        placeholder={<ComputerPlaceholder />}
      >
        <Suspense fallback={<ComputerPlaceholder />}>
          <ComputersCanvas />
        </Suspense>
      </DeferredRender>

      <div className='absolute xs:bottom-10 bottom-32 w-full flex justify-center items-center'>
        <a href='#about'>
          <div className='w-[35px] h-[64px] rounded-3xl border-4 border-secondary flex justify-center items-start p-2'>
            <motion.div
              animate={{
                y: [0, 24, 0],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                repeatType: "loop",
              }}
              className='w-3 h-3 rounded-full bg-secondary mb-1'
            />
          </div>
        </a>
      </div>
    </section>
  );
};

export default Hero;
