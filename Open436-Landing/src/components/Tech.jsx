import React from "react";

import { TechBallsCanvas } from "./canvas";
import { SectionWrapper } from "../hoc";
import { technologies as defaultTechnologies } from "../constants";
import { useHomepage } from "../context/HomepageContext";
import noimg from "../assets/noimg.svg";

const Tech = () => {
  const { get } = useHomepage();
  const list = get("technologies", defaultTechnologies);
  const defaultIcons = new Map(defaultTechnologies.map((t) => [t.name, t.icon]));
  const items = (Array.isArray(list) ? list : []).map((t, i) => ({
    name: t?.name || `tech-${i}`,
    icon: t?.icon || defaultIcons.get(t?.name) || noimg,
  }));

  return (
    <div className='h-[60rem] w-full sm:h-[37.5rem] lg:h-[36rem]'>
      <TechBallsCanvas technologies={items} />
    </div>
  );
};

export default SectionWrapper(Tech, "");
