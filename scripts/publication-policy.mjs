import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { isIP } from 'node:net';
import { fileURLToPath } from 'node:url';
import { parseCatalogue } from '../catalog/schema.mjs';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const HASH = /^[a-f0-9]{64}$/;
const ASSET_NAME = /^[A-Za-z0-9][A-Za-z0-9._-]*\.(?:webp|png|jpg|mp4|vtt|txt|md)$/;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requireValue = (condition, message) => { if (!condition) throw new Error(`PUBLICATION HELD: ${message}`); };
const reference = value => typeof value === 'string' && value.trim().length > 0;
const json = file => JSON.parse(readFileSync(file, 'utf8'));

export function publicHttpsUrl(value) {
  let url;
  try { url = new URL(value); } catch { throw new Error('PUBLICATION HELD: a valid public HTTPS URL is required.'); }
  const host = url.hostname.toLowerCase();
  requireValue(url.protocol === 'https:' && !url.username && !url.password && !url.hash
    && !url.port && !isIP(host.replace(/^\[|\]$/g, '')) && !/^(?:localhost|.*\.localhost|.*\.local|\d+(?:\.\d+)*)$/.test(host)
    && host.includes('.') && !/[\s\\]/.test(value), 'Only public HTTPS URLs without credentials, fragments or custom ports are allowed.');
  requireValue(![...url.searchParams.keys()].some(key => /^(?:token|access_token|api_key|authorization|password|secret)$/i.test(key)),
    'Credentials cannot be supplied in public URLs.');
  return url.href;
}

/** A private-repository bundle: flat ZIP under media-bundles/, verified by SHA-256. */
export function committedBundle(root, bundlePath, expectedHash) {
  requireValue(typeof bundlePath === 'string' && /^media-bundles\/[A-Za-z0-9][A-Za-z0-9._-]*\.zip$/.test(bundlePath),
    'Committed media bundles must be flat ZIP files under media-bundles/.');
  const full = path.join(root, bundlePath);
  requireValue(existsSync(full) && lstatSync(full).isFile() && !lstatSync(full).isSymbolicLink(),
    `Committed media bundle is missing or indirect: ${bundlePath}`);
  requireValue(sha(readFileSync(full)) === expectedHash, 'Committed media bundle SHA-256 differs from approval.');
  return full;
}

export function publicationInputs(options = {}) {
  const root = path.resolve(options.root ?? ROOT);
  const policy = options.policy ?? json(path.join(root, 'config/publication.json'));
  const catalogue = parseCatalogue(options.catalogue ?? json(path.join(root, 'catalog/experiences.json')));
  const manifestBytes = options.manifestBytes ?? readFileSync(path.join(root, 'docs/media/manifest.json'));
  const manifest = JSON.parse(manifestBytes.toString('utf8'));
  requireValue(policy.site && policy.media && policy.application
    && [policy.site, policy.media, policy.application].every(scope => typeof scope.approved === 'boolean'),
  'Site, media and application approval must be recorded in their own policy sections.');
  return { root, policy, catalogue, manifest, manifestBytes, manifestHash: sha(manifestBytes) };
}

export function mediaAssets(manifest) {
  requireValue(Array.isArray(manifest.assets) && manifest.assets.length > 0 && manifest.assets.length <= 64,
    'Media manifest must contain a bounded asset list.');
  const assets = new Map();
  let bytes = 0;
  for (const row of manifest.assets) {
    requireValue(typeof row.path === 'string' && ASSET_NAME.test(row.path) && !row.path.includes('..')
      && !assets.has(row.path.toLowerCase()), 'Media paths must be unique flat filenames.');
    requireValue(HASH.test(row.sha256) && Number.isSafeInteger(row.bytes) && row.bytes > 0 && row.bytes <= 10 * 1024 * 1024,
      `Invalid media hash or size: ${row.path}`);
    assets.set(row.path.toLowerCase(), row);
    bytes += row.bytes;
  }
  requireValue(bytes <= 20 * 1024 * 1024, 'Media bundle exceeds the 20 MiB uncompressed limit.');
  return assets;
}

export function assertMediaApproval(inputs) {
  const { policy, manifestHash, manifest } = inputs;
  requireValue(policy.media.approved === true && reference(policy.media.approval_reference),
    'Promotional media needs its own owner approval and reference.');
  requireValue(HASH.test(policy.media.manifest_sha256) && policy.media.manifest_sha256 === manifestHash,
    'Owner media approval must name the exact committed media manifest SHA-256.');
  requireValue((policy.media.bundle_url == null) !== (policy.media.bundle_path == null),
    'Approved media needs exactly one source: bundle_url or a committed bundle_path.');
  if (policy.media.bundle_url != null) publicHttpsUrl(policy.media.bundle_url);
  else committedBundle(inputs.root, policy.media.bundle_path, policy.media.bundle_sha256);
  requireValue(HASH.test(policy.media.bundle_sha256) && policy.media.bundle_sha256 === manifest.bundle?.sha256,
    'Approved media bundle hash must match the committed manifest.');
  return mediaAssets(manifest);
}

export function assertApplicationApproval(inputs) {
  const { policy, catalogue } = inputs;
  const downloads = catalogue.experiences.filter(row => row.install_url || row.release_url);
  if (policy.application.approved || downloads.length) {
    const app = policy.application;
    requireValue(app.approved === true && ['approval_reference', 'code_license', 'art_license'].every(key => reference(app[key])),
      'Application downloads need their own owner approval and code/art terms.');
    // The owner's distribution approval covers the application only. Redistributing the
    // Raven Framework needs Raven's own permission; a package without it needs a notice.
    requireValue(typeof app.framework_included === 'boolean',
      'Application approval must state whether Raven Framework is included.');
    if (app.framework_included) requireValue(reference(app.framework_permission),
      'A package that includes Raven Framework needs a Raven permission reference.');
    else requireValue(reference(app.framework_notice),
      'A package without Raven Framework needs a notice that users obtain it separately.');
  }
  const urls = new Set();
  for (const row of downloads) {
    requireValue(row.candidate?.availability === 'public' && row.license_status === 'cleared'
      && row.status !== 'Concept' && row.install_url && row.release_url,
    `Both public install/release links and cleared rights are required: ${row.id}`);
    urls.add(publicHttpsUrl(row.install_url));
    urls.add(publicHttpsUrl(row.release_url));
  }
  return urls;
}

function filesIn(root) {
  requireValue(existsSync(root) && lstatSync(root).isDirectory() && !lstatSync(root).isSymbolicLink(), `Missing or indirect output directory: ${root}`);
  const result = [];
  function walk(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const full = path.join(directory, entry.name);
      const info = lstatSync(full);
      requireValue(!info.isSymbolicLink(), `Symlink in output: ${entry.name}`);
      if (info.isDirectory()) walk(full);
      else {
        requireValue(info.isFile(), `Non-regular output: ${entry.name}`);
        result.push(path.relative(root, full).split(path.sep).join('/'));
      }
    }
  }
  walk(root);
  return result;
}

function publicFiles(root) {
  return new Map(filesIn(path.join(root, 'public')).map(name => {
    requireValue(name === 'robots.txt' || /^brand\/[a-z0-9-]+\.(?:svg|png|webp)$/.test(name)
      || /^licenses\/[A-Za-z0-9-]+\.txt$/.test(name), `Unexpected public source file: ${name}`);
    return [name, sha(readFileSync(path.join(root, 'public', name)))];
  }));
}

function htmlRoutes(root) {
  return new Set(filesIn(path.join(root, 'src/pages')).map(name => {
    requireValue(/^[a-z0-9/-]+\.astro$/.test(name), `Unsupported static page path: ${name}`);
    if (name === 'index.astro') return 'index.html';
    if (name === '404.astro') return '404.html';
    return name.endsWith('/index.astro') ? name.replace(/\.astro$/, '.html') : name.replace(/\.astro$/, '/index.html');
  }));
}

function verifyHtml(html, name, mode, includeMedia, assets, downloads) {
  const robots = [...html.matchAll(/<meta\b[^>]*>/gi)].filter(match => /\bname\s*=\s*["']robots["']/i.test(match[0]));
  const noindex = robots.some(match => /\bnoindex\b/i.test(match[0]));
  requireValue(robots.length === 1 && (mode === 'review' || name === '404.html' ? noindex : !noindex),
    `Incorrect robots/review indexing policy: ${name}`);
  if (mode === 'public') requireValue(!/PRIVATE REVIEW|GLASSPLAY_REVIEW["']?\s*[:=]\s*["']?1|\.private\//i.test(html), `Private review content in public page: ${name}`);
  for (const match of html.matchAll(/\b(?:src|poster|href)\s*=\s*["']([^"']+)["']/gi)) {
    const raw = match[1].replace(/&amp;/g, '&');
    let decoded;
    try { decoded = decodeURIComponent(raw); } catch { throw new Error(`PUBLICATION HELD: Malformed URL in ${name}`); }
    requireValue(!/\.private|(?:^|\/)archive\/|(?:^|\/)local-data\//i.test(decoded), `Private path referenced by ${name}`);
    if (decoded.includes('/media/nevermore/')) {
      const file = decoded.split('/media/nevermore/')[1];
      requireValue(includeMedia && [...assets.values()].some(row => row.path === file), `Unapproved media reference: ${name}`);
    }
    if (/\.(?:mp4|webm|wav|mp3)(?:[?#]|$)/i.test(decoded)) {
      requireValue(includeMedia && decoded.startsWith('/GlassPlay/media/nevermore/')
        && [...assets.values()].some(row => `/GlassPlay/media/nevermore/${row.path}` === decoded), `External or unapproved media: ${name}`);
    }
    if (/\.(?:zip|exe|msi|dmg|tar|gz)(?:[?#]|$)/i.test(decoded) || /github\.com\/RBraga01\/Nevermore\/releases\//i.test(decoded)) {
      requireValue(downloads.has(decoded), `Unapproved application download: ${name}`);
    }
  }
  for (const match of html.matchAll(/<a\b(?=[^>]*\bdownload\b)[^>]*href=["']([^"']+)["'][^>]*>/gi)) {
    requireValue(downloads.has(match[1].replace(/&amp;/g, '&')), `Unapproved download control: ${name}`);
  }
}

/** Verify an output tree even when the owner has not approved deploying the site. */
export function assertBuildBoundary(distDir, mode = 'public', options = {}) {
  requireValue(mode === 'public' || mode === 'review', 'Unknown build mode.');
  const inputs = publicationInputs(options);
  const { root, policy, manifest, manifestHash } = inputs;
  const output = path.resolve(root, distDir);
  requireValue(output === path.join(root, mode === 'review' ? '.private/site' : 'dist'), 'Build output is outside its designated publication boundary.');
  const approved = mode === 'public' && policy.media.approved;
  const includeMedia = mode === 'review' || approved;
  const assets = approved ? assertMediaApproval(inputs) : mediaAssets(manifest);
  const downloads = assertApplicationApproval(inputs);
  const files = filesIn(output);
  const markerName = 'glassplay-build.json';
  requireValue(files.includes(markerName), 'Build marker missing; rebuild the site.');
  const marker = json(path.join(output, markerName));
  requireValue(marker.schema_version === 1 && marker.review === (mode === 'review')
    && marker.media_approved === approved && marker.media_manifest_sha256 === (includeMedia ? manifestHash : null),
  'Build marker does not match the requested mode and current media approval.');
  const originals = publicFiles(root);
  const pages = htmlRoutes(root);
  const required = new Set([...originals.keys(), ...pages, markerName, 'sitemap-index.xml', 'sitemap-0.xml']);
  if (includeMedia) for (const row of assets.values()) required.add(`media/nevermore/${row.path}`);
  for (const name of files) {
    const full = path.join(output, name);
    requireValue(required.has(name) || /^_astro\/[A-Za-z0-9_.-]+\.(?:css|js|woff2)$/.test(name), `File outside static output allowlist: ${name}`);
    const bytes = readFileSync(full);
    if (originals.has(name)) requireValue(sha(bytes) === originals.get(name), `Public source/output mismatch: ${name}`);
    if (name.startsWith('media/nevermore/')) {
      const row = [...assets.values()].find(asset => `media/nevermore/${asset.path}` === name);
      requireValue(includeMedia && row && bytes.length === row.bytes && sha(bytes) === row.sha256, `Unapproved or changed media payload: ${name}`);
    }
    if (/\.(?:html|js|css|json|txt|xml|svg|md|vtt)$/.test(name)) {
      const text = bytes.toString('utf8');
      requireValue(!/(?:gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|sk-(?:proj-)?[A-Za-z0-9_-]{32,})/.test(text), `Credential material in ${name}`);
      if (pages.has(name)) verifyHtml(text, name, mode, includeMedia, assets, downloads);
    }
  }
  for (const name of required) requireValue(files.includes(name), `Required output missing: ${name}`);
  return { mode, files: files.length, media_files: includeMedia ? assets.size : 0, application_links: downloads.size, site_approved: policy.site.approved };
}

/** Deployment gate: website approval is independent of application release rights. */
export function assertPublication(distDir = 'dist', options = {}) {
  const inputs = publicationInputs(options);
  requireValue(inputs.policy.site.approved === true && reference(inputs.policy.site.approval_reference)
    && inputs.policy.site.pages_eligibility_confirmed === true,
  'Owner site approval/reference and confirmed Pages eligibility are required.');
  return assertBuildBoundary(distDir, 'public', options);
}
