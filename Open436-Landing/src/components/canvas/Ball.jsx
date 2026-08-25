import React, { Suspense, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Decal, Float, Preload, useTexture } from "@react-three/drei";

import CanvasLoader from "../Loader";

const Ball = ({ icon, position }) => {
  const dragRef = useRef(null);
  const [rotation, setRotation] = useState([0, 0, 0]);

  const startDrag = (event) => {
    event.stopPropagation();
    dragRef.current = { x: event.clientX, y: event.clientY };
    event.target.setPointerCapture(event.pointerId);
  };

  const rotateBall = (event) => {
    if (!dragRef.current) return;

    event.stopPropagation();
    const deltaX = event.clientX - dragRef.current.x;
    const deltaY = event.clientY - dragRef.current.y;
    dragRef.current = { x: event.clientX, y: event.clientY };
    setRotation(([x, y, z]) => [x + deltaY * 0.01, y + deltaX * 0.01, z]);
  };

  const endDrag = (event) => {
    if (!dragRef.current) return;

    event.stopPropagation();
    dragRef.current = null;
    event.target.releasePointerCapture(event.pointerId);
  };

  return (
    <group position={position}>
      <Float speed={1.75} rotationIntensity={0} floatIntensity={0.4}>
        <ambientLight intensity={0.25} />
        <directionalLight position={[0, 0, 0.05]} />
        <mesh
          scale={0.72}
          rotation={rotation}
          onPointerDown={startDrag}
          onPointerMove={rotateBall}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
        >
          <icosahedronGeometry args={[1, 1]} />
          <meshStandardMaterial
            color='#fff8eb'
            flatShading
            polygonOffset
            polygonOffsetFactor={-5}
          />
          <Decal
            position={[0, 0, 1]}
            rotation={[2 * Math.PI, 0, 6.25]}
            scale={1.1}
          >
            <meshBasicMaterial
              map={icon}
              transparent
              toneMapped={false}
              polygonOffset
              polygonOffsetFactor={-10}
            />
          </Decal>
        </mesh>
      </Float>
    </group>
  );
};

const TechBalls = ({ technologies }) => {
  const width = useThree((state) => state.size.width);
  const decals = useTexture(technologies.map((technology) => technology.icon));
  const columns = width >= 1024 ? 7 : width >= 640 ? 5 : 3;
  const rows = Math.ceil(technologies.length / columns);
  const spacing = 2;

  return technologies.map((technology, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    const position = [
      (column - (columns - 1) / 2) * spacing,
      ((rows - 1) / 2 - row) * spacing,
      0,
    ];

    return <Ball key={technology.name} icon={decals[index]} position={position} />;
  });
};

const TechBallsCanvas = ({ technologies }) => {
  return (
    <Canvas dpr={[1, 1.5]} orthographic camera={{ position: [0, 0, 10], zoom: 60 }}>
      <Suspense fallback={<CanvasLoader />}>
        <TechBalls technologies={technologies} />
      </Suspense>
      <Preload all />
    </Canvas>
  );
};

export default TechBallsCanvas;
