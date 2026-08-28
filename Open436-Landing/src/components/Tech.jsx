import React from "react";

import { TechBallsCanvas } from "./canvas";
import { SectionWrapper } from "../hoc";
import { technologies as defaultTechnologies } from "../constants";
import { useHomepage } from "../context/HomepageContext";

const Tech = () => {
  const { get } = useHomepage();
  const list = get("technologies", defaultTechnologies);
  const items = (Array.isArray(list) ? list : []).map((t, i) => ({
    name: t?.name || `tech-${i}`,
    icon: t?.icon || "",
  }));

  return (
    <div className='h-[60rem] w-full sm:h-[37.5rem] lg:h-[36rem]'>
      <TechBallsCanvas technologies={items} />
    </div>
  );
};

export default SectionWrapper(Tech, "");
