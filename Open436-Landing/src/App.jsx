import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { About, Contact, Experience, Feedbacks, Hero, Navbar, Tech, Works, StarsCanvas } from "./components";
import HonorsGallery from "./components/HonorsGallery";

const Home = () => (
  <div className='relative z-0 bg-primary'>
    <div className='bg-hero-pattern bg-cover bg-no-repeat bg-center'>
      <Navbar />
      <Hero />
    </div>
    <About />
    <Experience />
    <Tech />
    <Works />
    <Feedbacks />
    <div className='relative z-0'>
      <Contact />
      <StarsCanvas />
    </div>
  </div>
);

const App = () => (
  <BrowserRouter>
    <Routes>
      <Route path='/' element={<Home />} />
      <Route path='/honors' element={<HonorsGallery />} />
      <Route path='/honors/:albumIndex' element={<HonorsGallery />} />
      <Route path='*' element={<Navigate to='/' replace />} />
    </Routes>
  </BrowserRouter>
);

export default App;
