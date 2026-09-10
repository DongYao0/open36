import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import noimg from "../assets/noimg.svg";
import { useHomepage } from "../context/HomepageContext";
import { defaultHonorProjects, honorGallery, withHonorAlbums } from "../data/honorGallery";

const HonorsGallery = () => {
  const { get } = useHomepage();
  const works = get("works", { items: defaultHonorProjects, gallery: honorGallery });
  const { albumIndex = "0" } = useParams();
  const projects = useMemo(
    () => withHonorAlbums(works.items, Array.isArray(works.gallery) ? works.gallery : honorGallery),
    [works.items, works.gallery],
  );
  const selectedIndex = Math.min(Math.max(Number(albumIndex) || 0, 0), Math.max(projects.length - 1, 0));
  const project = projects[selectedIndex];
  const photos = useMemo(
    () => (project?.gallery || []).map((item, index) => ({
      ...item, image: item.image || noimg, title: item.title || `荣誉作品 ${index + 1}`,
    })),
    [project],
  );
  const [active, setActive] = useState(0);
  const [direction, setDirection] = useState(1);

  const move = (step) => {
    if (photos.length < 2) return;
    setDirection(step);
    setActive((current) => (current + step + photos.length) % photos.length);
  };

  useEffect(() => {
    document.body.style.overflowX = "hidden";
    window.scrollTo(0, 0);
    const onKeyDown = (event) => {
      if (event.key === "ArrowLeft") move(-1);
      if (event.key === "ArrowRight") move(1);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [photos.length]);

  useEffect(() => {
    setActive((current) => Math.min(current, Math.max(photos.length - 1, 0)));
  }, [photos.length]);

  useEffect(() => setActive(0), [selectedIndex]);

  const photo = photos[active];

  return (
    <main className='min-h-screen overflow-hidden bg-primary text-white-100'>
      <div className='fixed inset-0 pointer-events-none bg-[radial-gradient(circle_at_50%_15%,rgba(145,94,255,.2),transparent_38%)]' />
      <header className='relative z-20 flex items-center justify-between px-6 py-6 sm:px-12'>
        <Link to='/' className='text-sm text-secondary transition hover:text-white'>
          ← 返回首页
        </Link>
        <div className='text-right'>
          <p className='text-xs uppercase tracking-[0.35em] text-secondary'>Open436 Honor Archive</p>
          <p className='mt-1 text-sm text-white/70'>{project?.name || "荣誉相册"}</p>
        </div>
      </header>

      <section className='relative z-10 mx-auto flex min-h-[calc(100vh-96px)] max-w-[1500px] flex-col px-4 pb-8 sm:px-10'>
        {!photo ? (
          <div className='m-auto text-center'>
            <p className='text-2xl font-semibold'>相册正在整理中</p>
            <p className='mt-3 text-secondary'>上传第一张荣誉照片后，这里会自动展示。</p>
          </div>
        ) : (
          <>
            <div className='relative flex flex-1 items-center justify-center'>
              <button aria-label='上一张' onClick={() => move(-1)} className='absolute left-0 z-20 h-12 w-12 rounded-full border border-white/20 bg-black/30 text-2xl backdrop-blur transition hover:border-violet-400 hover:bg-violet-500/20 sm:left-2'>‹</button>
              <AnimatePresence mode='wait' custom={direction}>
                <motion.figure
                  key={`${active}-${photo.image}`}
                  custom={direction}
                  initial={{ opacity: 0, x: direction * 90, scale: 0.97 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={{ opacity: 0, x: direction * -90, scale: 0.97 }}
                  transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
                  drag='x'
                  dragConstraints={{ left: 0, right: 0 }}
                  dragElastic={0.12}
                  onDragEnd={(_, info) => Math.abs(info.offset.x) > 70 && move(info.offset.x > 0 ? -1 : 1)}
                  className='grid w-full max-w-6xl items-center gap-8 px-8 sm:px-12 lg:grid-cols-[minmax(0,1fr)_330px]'
                >
                  <div className='relative flex h-[36vh] min-h-[280px] items-center justify-center overflow-hidden rounded-[28px] border border-white/10 bg-black/35 shadow-[0_30px_100px_rgba(0,0,0,.55)] sm:h-[52vh] sm:min-h-[340px]'>
                    <img src={photo.image} alt={photo.title} className='h-full w-full object-contain' />
                    <span className='absolute left-5 top-5 rounded-full border border-white/15 bg-black/50 px-3 py-1 text-xs tracking-widest backdrop-blur'>{String(active + 1).padStart(2, "0")} / {String(photos.length).padStart(2, "0")}</span>
                  </div>
                  <figcaption>
                    <div className='mb-5 h-px w-16 bg-violet-400' />
                    <h1 className='text-4xl font-black leading-tight sm:text-6xl'>{photo.recipient || "Open436 参赛团队"}</h1>
                    <p className='mt-4 text-xs uppercase tracking-[0.25em] text-violet-300'>{[photo.category, photo.level].filter(Boolean).join(" · ") || "荣誉见证"}</p>
                    <h2 className='mt-4 text-xl font-semibold leading-relaxed text-white/85'>{photo.title}</h2>
                    {photo.year && <p className='mt-2 text-sm text-white/45'>{photo.year}</p>}
                    {photo.description && <p className='mt-5 text-base leading-8 text-secondary'>{photo.description}</p>}
                    <p className='mt-8 text-xs tracking-wider text-white/40'>拖动图片或使用方向键切换</p>
                  </figcaption>
                </motion.figure>
              </AnimatePresence>
              <button aria-label='下一张' onClick={() => move(1)} className='absolute right-0 z-20 h-12 w-12 rounded-full border border-white/20 bg-black/30 text-2xl backdrop-blur transition hover:border-violet-400 hover:bg-violet-500/20 sm:right-2'>›</button>
            </div>

          </>
        )}
      </section>
    </main>
  );
};

export default HonorsGallery;
