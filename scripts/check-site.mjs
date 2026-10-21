import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { resolve, relative, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const SITE = 'https://rbraga01.github.io';
const BASE = '/GlassPlay/';
const REQUIRED_PAGES = ['index.html', 'experiences/nevermore/index.html', 'credits/index.html'];

function decode(value) {
  return value.replace(/&(?:#(\d+)|#x([\da-f]+)|(amp|quot|apos|lt|gt));/gi, (_, decimal, hex, named) => {
    if (decimal || hex) return String.fromCodePoint(Number.parseInt(decimal || hex, decimal ? 10 : 16));
    return { amp: '&', quot: '"', apos: "'", lt: '<', gt: '>' }[named.toLowerCase()];
  });
}

function attributes(source) {
  const result = {};
  for (const match of source.matchAll(/([\w:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g)) {
    result[match[1].toLowerCase()] = decode(match[2] ?? match[3] ?? match[4] ?? '');
  }
  return result;
}

function filesIn(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? filesIn(path) : [path];
  });
}

function imageDimensions(path) {
  const bytes = readFileSync(path);
  if (bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    return [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
  }
  if (bytes[0] === 0xff && bytes[1] === 0xd8) {
    for (let offset = 2; offset + 9 < bytes.length;) {
      if (bytes[offset] !== 0xff) break;
      const marker = bytes[offset + 1];
      if ([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf].includes(marker)) {
        return [bytes.readUInt16BE(offset + 7), bytes.readUInt16BE(offset + 5)];
      }
      const length = bytes.readUInt16BE(offset + 2);
      if (length < 2) break;
      offset += 2 + length;
    }
  }
  if (bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WEBP') {
    const kind = bytes.toString('ascii', 12, 16);
    if (kind === 'VP8X') return [bytes.readUIntLE(24, 3) + 1, bytes.readUIntLE(27, 3) + 1];
    if (kind === 'VP8 ') return [bytes.readUInt16LE(26) & 0x3fff, bytes.readUInt16LE(28) & 0x3fff];
    if (kind === 'VP8L') {
      const bits = bytes.readUInt32LE(21);
      return [(bits & 0x3fff) + 1, ((bits >>> 14) & 0x3fff) + 1];
    }
  }
  throw new Error('Social image must be a readable PNG, JPEG or WebP.');
}

/** Check generated files without making network requests or accessing private media. */
export function checkSite({ distDir = resolve(ROOT, 'dist'), cataloguePath = resolve(ROOT, 'catalog/experiences.json') } = {}) {
  distDir = resolve(distDir);
  cataloguePath = resolve(cataloguePath);
  const errors = [];
  const fail = (page, message) => errors.push(`${page}: ${message}`);
  if (!existsSync(distDir)) return ['dist/: no build found; run npm run build first.'];
  const files = filesIn(distDir);
  const pages = new Map();
  for (const path of files.filter((entry) => extname(entry) === '.html')) {
    const name = relative(distDir, path).split(sep).join('/');
    const html = readFileSync(path, 'utf8');
    const markup = html.replace(/<!--[\s\S]*?-->/g, '').replace(/(<script\b[^>]*>)[\s\S]*?<\/script>/gi, '$1</script>');
    const tags = [...markup.matchAll(/<([a-z][\w:-]*)\b([^>]*?)>/gi)].map((match) => ({ name: match[1].toLowerCase(), attrs: attributes(match[2]) }));
    pages.set(name, { html, tags, ids: new Set(tags.map((tag) => tag.attrs.id).filter(Boolean)) });
  }
  for (const name of REQUIRED_PAGES) if (!pages.has(name)) fail(name, 'required page missing');

  function localReference(value, page, { fragment = true } = {}) {
    if (/^(?:mailto:|tel:|data:|blob:)/i.test(value)) return null;
    let url;
    try { url = new URL(value, `${SITE}${BASE}${page.replace(/index\.html$/, '')}`); }
    catch { fail(page, `invalid URL: ${value}`); return null; }
    if (!['https:', 'http:'].includes(url.protocol)) { fail(page, `unsupported URL protocol: ${value}`); return null; }
    if (url.origin !== SITE) return null;
    if (!url.pathname.startsWith(BASE)) { fail(page, `local URL omits ${BASE}: ${value}`); return null; }
    let pathname;
    try { pathname = decodeURIComponent(url.pathname.slice(BASE.length)); }
    catch { fail(page, `invalid URL encoding: ${value}`); return null; }
    let path = resolve(distDir, pathname);
    if (path !== distDir && !path.startsWith(`${distDir}${sep}`)) { fail(page, `URL escapes build: ${value}`); return null; }
    if (existsSync(path) && statSync(path).isDirectory()) path = resolve(path, 'index.html');
    if (!existsSync(path) || !statSync(path).isFile()) { fail(page, `missing local target: ${value}`); return null; }
    const targetName = relative(distDir, path).split(sep).join('/');
    if (fragment && url.hash && pages.has(targetName)) {
      let id;
      try { id = decodeURIComponent(url.hash.slice(1)); } catch { id = url.hash.slice(1); }
      if (!pages.get(targetName).ids.has(id)) fail(page, `missing fragment: ${value}`);
    }
    return path;
  }

  for (const [page, { html, tags }] of pages) {
    const expectedUrl = `${SITE}${BASE}${page.replace(/index\.html$/, '')}`;
    const meta = (key) => tags.find((tag) => tag.name === 'meta' && (tag.attrs.name === key || tag.attrs.property === key))?.attrs.content;
    const canonical = tags.find((tag) => tag.name === 'link' && tag.attrs.rel === 'canonical')?.attrs.href;
    if (!/<title>[^<]+<\/title>/i.test(html)) fail(page, 'missing document title');
    if (!meta('description')?.trim()) fail(page, 'missing meta description');
    if (!tags.find((tag) => tag.name === 'html')?.attrs.lang) fail(page, 'missing document language');
    if (tags.filter((tag) => tag.name === 'h1').length !== 1) fail(page, 'expected one primary heading');
    if (canonical !== expectedUrl) fail(page, `canonical must be ${expectedUrl}`);
    for (const key of ['og:title', 'og:description', 'og:type', 'og:image', 'og:image:alt', 'twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']) {
      if (!meta(key)?.trim()) fail(page, `missing ${key}`);
    }
    if (meta('og:url') !== expectedUrl) fail(page, 'og:url must match canonical');
    if (meta('twitter:card') !== 'summary_large_image') fail(page, 'twitter:card must be summary_large_image');
    if (meta('og:image:width') !== '1200' || meta('og:image:height') !== '630') fail(page, 'OG image metadata must be 1200 × 630');
    for (const key of ['og:image', 'twitter:image']) {
      const value = meta(key);
      if (!value) continue;
      if (!value.startsWith(`${SITE}${BASE}`)) { fail(page, `${key} must be an absolute local production URL`); continue; }
      const path = localReference(value, page);
      if (path) {
        try { if (imageDimensions(path).join('x') !== '1200x630') fail(page, `${key} actual image is not 1200 × 630`); }
        catch (error) { fail(page, `${key}: ${error.message}`); }
      }
    }
    for (const { name, attrs } of tags) {
      for (const key of ['href', 'src', 'poster']) {
        if (attrs[key] !== undefined) localReference(attrs[key], page);
      }
      if (attrs.srcset && !attrs.srcset.startsWith('data:')) {
        for (const source of attrs.srcset.split(',')) localReference(source.trim().split(/\s+/)[0], page);
      }
      if (['video', 'audio'].includes(name) && 'autoplay' in attrs && !('muted' in attrs)) fail(page, `${name} can autoplay with sound`);
      if (name === 'video' && !('controls' in attrs)) fail(page, 'video requires explicit playback controls');
      if (name === 'img' && !('alt' in attrs)) fail(page, 'image is missing alt text');
    }
    for (const match of html.matchAll(/url\(\s*["']?([^)'"\s]+)["']?\s*\)/g)) localReference(decode(match[1]), page, { fragment: false });
  }

  for (const css of files.filter((path) => extname(path) === '.css')) {
    const name = relative(distDir, css).split(sep).join('/');
    for (const match of readFileSync(css, 'utf8').matchAll(/url\(\s*["']?([^)'"\s]+)["']?\s*\)/g)) localReference(match[1], name, { fragment: false });
  }
  const catalogue = JSON.parse(readFileSync(cataloguePath, 'utf8'));
  for (const experience of catalogue.experiences) {
    if (experience.status?.toLowerCase() !== 'concept') continue;
    if (experience.install_url || experience.release_url) fail('catalogue', `${experience.id} concept has an install/release URL`);
    if (pages.has(`experiences/${experience.id}/index.html`)) fail('catalogue', `${experience.id} concept has a product page`);
    for (const [page, { html }] of pages) {
      for (const link of html.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi)) {
        const attrs = attributes(link[1]);
        const label = decode(link[2].replace(/<[^>]*>/g, ' '));
        if (attrs.href && !attrs.href.startsWith('#') && label.toLowerCase().includes(experience.name.toLowerCase())) {
          fail(page, `${experience.name} concept must not be presented as an available link`);
        }
      }
    }
  }
  for (const name of ['robots.txt', 'sitemap-index.xml']) if (!existsSync(resolve(distDir, name))) fail(name, 'required discovery file missing');
  for (const path of files.filter((entry) => /sitemap.*\.xml$/.test(entry))) {
    for (const match of readFileSync(path, 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)) localReference(decode(match[1]), relative(distDir, path), { fragment: false });
  }
  return errors;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const errors = checkSite();
  if (errors.length) {
    console.error(`Site validation failed (${errors.length}):\n${errors.map((error) => `- ${error}`).join('\n')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS: required pages, local links/assets, base paths, metadata, social image dimensions, concept availability and media controls.');
  }
}
