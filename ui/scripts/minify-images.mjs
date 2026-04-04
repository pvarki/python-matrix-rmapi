#!/usr/bin/env node
// Minifies PNG/JPEG images in-place using sharp (no external binaries needed).

import { readdirSync, statSync, renameSync, rmSync } from "fs";
import { join, extname } from "path";
import sharp from "sharp";

const PNG_EXTS = new Set([".png"]);
const JPG_EXTS = new Set([".jpg", ".jpeg"]);
const SEARCH_DIRS = ["src/assets", "public/assets"];

function findImages(dir) {
  const results = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findImages(full));
    } else {
      const ext = extname(entry.name).toLowerCase();
      if (PNG_EXTS.has(ext) || JPG_EXTS.has(ext)) results.push(full);
    }
  }
  return results;
}

const images = SEARCH_DIRS.filter((d) => {
  try {
    statSync(d);
    return true;
  } catch {
    return false;
  }
}).flatMap(findImages);

if (images.length === 0) {
  console.log("No images found.");
  process.exit(0);
}

console.log(`Minifying ${images.length} image(s)...\n`);

let totalBefore = 0;
let totalAfter = 0;

for (const src of images) {
  const tmp = `${src}.min-tmp`;
  try {
    const ext = extname(src).toLowerCase();
    const sizeBefore = statSync(src).size;

    if (PNG_EXTS.has(ext)) {
      await sharp(src).png({ compressionLevel: 9, effort: 10 }).toFile(tmp);
    } else {
      await sharp(src).jpeg({ quality: 82, mozjpeg: true }).toFile(tmp);
    }

    const sizeAfter = statSync(tmp).size;
    if (sizeAfter < sizeBefore) {
      renameSync(tmp, src);
      totalBefore += sizeBefore;
      totalAfter += sizeAfter;
      const pct = (((sizeBefore - sizeAfter) / sizeBefore) * 100).toFixed(1);
      console.log(
        `  ${src}: ${(sizeBefore / 1024).toFixed(0)} KB → ${(
          sizeAfter / 1024
        ).toFixed(0)} KB  (-${pct}%)`,
      );
    } else {
      rmSync(tmp);
      totalBefore += sizeBefore;
      totalAfter += sizeBefore;
      console.log(`  ${src}: already optimal, skipped`);
    }
  } catch (err) {
    try {
      rmSync(tmp, { force: true });
    } catch {}
    console.warn(`  SKIP ${src}: ${err.message}`);
  }
}

if (totalBefore > 0) {
  const totalPct = (((totalBefore - totalAfter) / totalBefore) * 100).toFixed(
    1,
  );
  console.log(
    `\nTotal: ${(totalBefore / 1024).toFixed(0)} KB → ${(
      totalAfter / 1024
    ).toFixed(0)} KB  (-${totalPct}%)`,
  );
}
