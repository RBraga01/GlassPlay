// Render the GlassPlay app icons from the site's own brand mark (src/components/Logo.astro):
// the glasses outline in the "Play" blue-to-violet gradient on the hero's navy/violet night.
//   node scripts/art/glassplay_icons.mjs <out-dir>
// Requires a local Chrome/Chromium (CHROME_PATH or chrome-launcher discovery).
import { readFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';
import { Launcher } from 'chrome-launcher';

const out = process.argv[2];
mkdirSync(out, { recursive: true });
const logo = readFileSync('src/components/Logo.astro', 'utf8');
const markPath = logo.match(/<path d="([^"]+)"/)[1];  // single source of truth: the header mark

// [file, size, mark width as a share of the canvas, stroke width in mark units]
const icons = [
  ['glassplay-icon.png', 512, 0.70, 2.5],
  ['apple-touch-icon.png', 180, 0.70, 2.7],
  ['favicon.png', 64, 0.92, 3.9],  // larger and bolder so it reads in a browser tab
  ['favicon-32.png', 32, 0.94, 4.4],  // native tab size: no browser downscaling
];

const html = ([, size, share, stroke]) => {
  const w = size * share, h = w * 34 / 56;
  return `<!doctype html><html><head><style>
*{margin:0}html,body{width:${size}px;height:${size}px;overflow:hidden}
body{background:radial-gradient(circle at 50% 62%,rgba(140,112,255,.42) 0%,rgba(140,112,255,0) 58%),linear-gradient(160deg,#1c2150 0%,#0d1430 55%,#0a111d 100%);display:grid;place-items:center}
svg{width:${w}px;height:${h}px;filter:drop-shadow(0 0 ${Math.max(1, size / 40)}px rgba(166,184,255,.55))}
</style></head><body>
<svg viewBox="-1.5 0 59 34" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7fd6ff"/><stop offset=".45" stop-color="#a6b8ff"/><stop offset="1" stop-color="#c7a8ff"/></linearGradient></defs>
<path d="${markPath}" stroke="url(#g)" stroke-width="${stroke}" stroke-linecap="round" stroke-linejoin="round"/>
</svg></body></html>`;
};

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH || Launcher.getInstallations()[0], headless: true,
  args: ['--no-first-run', '--hide-scrollbars'],
});
for (const icon of icons) {
  const page = await browser.newPage();
  await page.setViewport({ width: icon[1], height: icon[1], deviceScaleFactor: 1 });
  await page.setContent(html(icon), { waitUntil: 'load' });
  await page.screenshot({ path: path.join(out, icon[0]) });
  await page.close();
}
await browser.close();
console.log(icons.map(i => `${i[0]} ${i[1]}x${i[1]}`).join('\n'));
