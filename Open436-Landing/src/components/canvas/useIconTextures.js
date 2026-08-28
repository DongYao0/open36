import { useEffect, useMemo, useState } from "react";
import { CanvasTexture, sRGBEncoding } from "three";

const COLUMNS = 6;
const TILE_SIZE = 128;

const loadImage = (src) =>
  new Promise((resolve, reject) => {
    const image = new Image();
    // 外链图（后台上传的 FileService URL）绘制到 canvas 需要 CORS 凭证模式
    image.crossOrigin = "anonymous";
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });

const drawIcon = (context, image, x, y) => {
  const scale = Math.min(TILE_SIZE / image.width, TILE_SIZE / image.height) * 0.82;
  const width = image.width * scale;
  const height = image.height * scale;
  context.drawImage(image, x + (TILE_SIZE - width) / 2, y + (TILE_SIZE - height) / 2, width, height);
};

export const useIconTextures = (icons) => {
  const key = icons.join("|");
  const [atlas, setAtlas] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setAtlas(null);
    if (!icons.length) return () => { cancelled = true; };

    Promise.all(icons.map((src) => loadImage(src).catch(() => null))).then((images) => {
      const rows = Math.ceil(images.length / COLUMNS);
      const canvas = document.createElement("canvas");
      canvas.width = COLUMNS * TILE_SIZE;
      canvas.height = rows * TILE_SIZE;
      const context = canvas.getContext("2d");

      images.forEach((image, index) => {
        if (image) drawIcon(context, image, (index % COLUMNS) * TILE_SIZE, Math.floor(index / COLUMNS) * TILE_SIZE);
      });

      const texture = new CanvasTexture(canvas);
      texture.encoding = sRGBEncoding;

      if (cancelled) texture.dispose();
      else setAtlas(texture);
    });

    return () => {
      cancelled = true;
    };
  }, [key]);

  useEffect(() => () => atlas?.dispose(), [atlas]);

  const textures = useMemo(() => {
    if (!atlas) return null;

    const rows = Math.ceil(icons.length / COLUMNS);
    return icons.map((_, index) => {
      const texture = atlas.clone();
      texture.repeat.set(1 / COLUMNS, 1 / rows);
      texture.offset.set((index % COLUMNS) / COLUMNS, 1 - (Math.floor(index / COLUMNS) + 1) / rows);
      texture.needsUpdate = true;
      return texture;
    });
  }, [atlas, key]);

  useEffect(() => () => textures?.forEach((texture) => texture.dispose()), [textures]);

  return textures;
};
