import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Hero from "./components/Hero";
import Navbar from "./components/Navbar";
import DeferredRender from "./components/DeferredRender";

const About = lazy(() => import("./components/About"));
const Contact = lazy(() => import("./components/Contact"));
const Experience = lazy(() => import("./components/Experience"));
const Feedbacks = lazy(() => import("./components/Feedbacks"));
const HonorsGallery = lazy(() => import("./components/HonorsGallery"));
const Tech = lazy(() => import("./components/Tech"));
const Works = lazy(() => import("./components/Works"));
const StarsCanvas = lazy(() => import("./components/canvas/Stars"));

const Home = () => (
  <div className='relative z-0 bg-primary'>
    <div className='bg-hero-pattern bg-cover bg-no-repeat bg-center'>
      <Navbar />
      <Hero />
    </div>
    <Suspense fallback={<div className='min-h-[520px]' />}>
      <About />
    </Suspense>
    <DeferredRender minHeight='900px'>
      <Suspense fallback={<div className='min-h-[900px]' />}><Experience /></Suspense>
    </DeferredRender>
    <DeferredRender minHeight='650px'>
      <Suspense fallback={<div className='min-h-[650px]' />}><Tech /></Suspense>
    </DeferredRender>
    <DeferredRender minHeight='760px'>
      <Suspense fallback={<div className='min-h-[760px]' />}><Works /></Suspense>
    </DeferredRender>
    <DeferredRender minHeight='560px'>
      <Suspense fallback={<div className='min-h-[560px]' />}><Feedbacks /></Suspense>
    </DeferredRender>
    <DeferredRender minHeight='720px'>
      <Suspense fallback={<div className='min-h-[720px]' />}>
        <div className='relative z-0'>
          <Contact />
          <StarsCanvas />
        </div>
      </Suspense>
    </DeferredRender>
  </div>
);

const App = () => (
  <Suspense fallback={<div className='min-h-screen bg-primary' />}>
    <BrowserRouter>
      <Routes>
        <Route path='/' element={<Home />} />
        <Route path='/honors' element={<HonorsGallery />} />
        <Route path='/honors/:albumIndex' element={<HonorsGallery />} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </BrowserRouter>
  </Suspense>
);

export default App;
