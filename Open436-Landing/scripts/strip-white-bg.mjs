#!/usr/bin/env node
// 抠图脚本：把 assets/advantages/*.png 中的白底像素设为完全透明。
//
// 算法（v2，边缘背景识别）：
// 1. 采样图像四条边的 RGB 值，找到出现最多的颜色作为"背景色"（通常是白底）。
// 2. 只清与背景色足够接近的像素（每个通道差异 < tolerance）。
// 3. 已透明的像素（alpha=0）直接跳过，保证幂等。
//
// 用法：
//   npm run prepare-assets
//   node scripts/strip-white-bg.mjs [dir] [--tolerance=N] [--edge=N]
//
// 默认参数：
//   dir        = src/assets/advantages
//   tolerance  = 12 (每通道允许的偏差)
//   edge       = 30  (边缘采样宽度，px)
//
// 跳过规则：
//   - 文件名以 _ 开头（备份/预览）
//   - 已经是 RGBA 模式且 > 80% 像素 alpha=0（已抠图）

import { readdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const args = process.argv.slice(2);
const numArg = (name, fallback) => {
  const a = args.find((x) => x.startsWith(`--${name}=`));
  return a ? Number(a.split('=')[1]) : fallback;
};
const TOLERANCE = numArg('tolerance', 12);
const EDGE = numArg('edge', 30);
const positional = args.find((a) => !a.startsWith('--'));
const DIR = resolve(__dirname, '..', positional || 'src/assets/advantages');

// 选 PNG 库：优先 pngjs（纯 JS），否则 sharp（原生，但可能没装）
let PNG;
try {
  const { PNG: pngjs } = await import('pngjs');
  PNG = await importPngjs(pngjs);
} catch {
  console.error('需要 pngjs 依赖。运行:  npm i -D pngjs');
  process.exit(1);
}

function importPngjs(pngjs) {
  return {
    async load(path) {
      const buf = await readFile(path);
      return new Promise((res, rej) => {
        new pngjs().parse(buf, (err, png) => {
          if (err) return rej(err);
          res({ data: Uint8Array.from(png.data), width: png.width, height: png.height });
        });
      });
    },
    async save(path, { data, width, height }) {
      const png = new pngjs({ width, height });
      png.data = Buffer.from(data);
      const buf = await PNG.pack(png);
      await writeFile(path, buf);
    },
    pack(png) {
      return new Promise((res, rej) => {
        const chunks = [];
        png
          .pack()
          .on('data', (c) => chunks.push(c))
          .on('end', () => res(Buffer.concat(chunks)))
          .on('error', rej);
      });
    },
  };
}

// ── 主流程 ──────────────────────────────────────────────

function sampleEdges(data, width, height) {
  // 在四条边采样，统计出现最多的 RGB 颜色
  const counter = new Map();
  const put = (key, r, g, b) => counter.set(key, (counter.get(key) || 0) + 1);

  const xRange = (fn) => { for (let x = 0; x < width; x++) fn(x); };
  const yRange = (fn) => { for (let y = 0; y < height; y++) fn(y); };

  const samplePixel = (x, y) => {
    const i = (y * width + x) << 2;
    const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3];
    if (a === 0) return; // 已透明，跳过
    put(`${r},${g},${b}`, r, g, b);
  };

  // 上下两边
  xRange((x) => { samplePixel(x, 0); samplePixel(x, height - 1); });
  // 左右两边
  yRange((y) => { samplePixel(0, y); samplePixel(width - 1, y); });

  if (!counter.size) return null;
  let bestKey = null, bestCount = 0;
  for (const [k, c] of counter) {
    if (c > bestCount) { bestCount = c; bestKey = k; }
  }
  const [r, g, b] = bestKey.split(',').map(Number);
  return { r, g, b, count: bestCount, total: counter.size };
}

function isAlreadyTransparent(data) {
  // 如果 > 50% 像素 alpha=0，认为已抠图，跳过（避免反复处理）
  let t = 0;
  for (let i = 3; i < data.length; i += 4) if (data[i] === 0) t++;
  return t / (data.length / 4) > 0.5;
}

const entries = await readdir(DIR, { withFileTypes: true });
const files = entries
  .filter((e) => e.isFile() && /\.png$/i.test(e.name))
  .filter((e) => !/^_/.test(e.name))
  .map((e) => join(DIR, e.name));

if (!files.length) {
  console.log(`[strip-white-bg] 未在 ${DIR} 找到 PNG，跳过。`);
  process.exit(0);
}

console.log(`[strip-white-bg] 目录: ${DIR}`);
console.log(`[strip-white-bg] 容差: ±${TOLERANCE}/通道, 边缘采样: ${EDGE}px（实际采样整个四条边）`);
console.log(`[strip-white-bg] 文件数: ${files.length}\n`);

let touched = 0, skipped = 0;
for (const path of files) {
  const { data, width, height } = await PNG.load(path);

  if (isAlreadyTransparent(data)) {
    skipped++;
    console.log(`  ⏭  ${path.replace(DIR, '.')}  (已抠图,跳过)`);
    continue;
  }

  let bg = sampleEdges(data, width, height);
  if (!bg || bg.count < 50) {
    // 边缘已被大量抠图（如半透明状态），无法可靠采样 → 用默认白底 + 容差
    bg = { r: 255, g: 255, b: 255, count: 0, total: 0, fallback: true };
  }

  // 全图清：每个通道与背景色差 < tolerance → alpha=0
  let cleared = 0;
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3];
    if (a === 0) continue;
    if (
      Math.abs(r - bg.r) < TOLERANCE &&
      Math.abs(g - bg.g) < TOLERANCE &&
      Math.abs(b - bg.b) < TOLERANCE
    ) {
      data[i + 3] = 0;
      cleared++;
    }
  }

  const total = width * height;
  await PNG.save(path, { data, width, height });
  touched++;
  console.log(
    `  ✓  ${path.replace(DIR, '.')}  ${bg.fallback ? '回退' : '边缘'}背景 RGB=(${bg.r},${bg.g},${bg.b}) ${bg.fallback ? '' : `(${bg.count}/${bg.total} 样本)`} | 清除 ${cleared}/${total} px (${((100 * cleared) / total).toFixed(1)}%)`
  );
}

console.log(`\n[strip-white-bg] 处理 ${touched} 个,跳过 ${skipped} 个。`);