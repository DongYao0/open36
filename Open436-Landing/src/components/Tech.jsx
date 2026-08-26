import React from "react";

import { TechBallsCanvas } from "./canvas";
import { SectionWrapper } from "../hoc";
import { technologies } from "../constants";

const Tech = () => {
  return (
    <div className='h-[60rem] w-full sm:h-[37.5rem] lg:h-[36rem]'>
      <TechBallsCanvas technologies={technologies} />
    </div>
  );
};

export default SectionWrapper(Tech, "");
