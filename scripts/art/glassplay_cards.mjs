// Render the GlassPlay social card and README banner from the text-free hero
// plate, using the website's own Manrope type (no baked-in reference text).
//   node scripts/art/glassplay_cards.mjs <plate.png> <out-dir>
// Requires a local Chrome/Chromium (CHROME_PATH or chrome-launcher discovery).
import { readFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';
import { Launcher } from 'chrome-launcher';

const [plate, out] = process.argv.slice(2);
mkdirSync(out, { recursive: true });
const font = `data:font/woff2;base64,${readFileSync('node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2').toString('base64')}`;
const image = `data:image/png;base64,${readFileSync(plate).toString('base64')}`;

const cards = [
  // [file, width, height, text column width, wordmark px, tagline px, object-position]
  ['glassplay-social.png', 1200, 630, 340, 88, 26, '50% 40%'],
  ['glassplay-banner.png', 1672, 941, 470, 124, 34, '50% 50%'],
];

const html = ([, width, height, column, mark, tag, position]) => `<!doctype html><html><head><style>
@font-face{font-family:Manrope;src:url(${font}) format('woff2');font-weight:200 800}
*{margin:0;box-sizing:border-box}
body{width:${width}px;height:${height}px;overflow:hidden;background:#0a111d;font-family:Manrope,sans-serif;color:#f3f4fa}
img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:${position}}
.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,17,40,.7) 0%,rgba(10,17,40,.38) 32%,rgba(10,17,40,0) 54%)}
.copy{position:absolute;left:${Math.round(width * 0.058)}px;top:50%;transform:translateY(-58%);width:${column}px}
.mark{font-size:${mark}px;font-weight:700;letter-spacing:-.06em;line-height:.95;text-shadow:0 4px 30px rgba(10,17,40,.35)}
.mark span{background:linear-gradient(90deg,#7fd6ff 0%,#a6b8ff 45%,#c7a8ff 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.tag{margin-top:${Math.round(mark * 0.22)}px;font-size:${tag}px;font-weight:500;letter-spacing:-.02em;line-height:1.3;text-shadow:0 2px 16px rgba(10,17,40,.6)}
</style></head><body><img src="${image}"><div class="shade"></div>
<div class="copy"><div class="mark">Glass<span>Play</span></div><div class="tag">A little magic,<br>right before your eyes.</div></div></body></html>`;

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH || Launcher.getInstallations()[0], headless: true,
  args: ['--no-first-run', '--hide-scrollbars'],
});
for (const card of cards) {
  const page = await browser.newPage();
  await page.setViewport({ width: card[1], height: card[2], deviceScaleFactor: 1 });
  await page.setContent(html(card), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(out, card[0]) });
  await page.close();
}
await browser.close();
console.log(cards.map(c => `${c[0]} ${c[1]}x${c[2]}`).join('\n'));
