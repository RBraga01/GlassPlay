import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { assertBuildBoundary, assertPublication, publicHttpsUrl } from '../scripts/publication-policy.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const catalogue = JSON.parse(readFileSync(new URL('../catalog/experiences.json', import.meta.url), 'utf8'));
// Fixtures start without any application download; tests add one explicitly.
const withoutDownloads = doc => {
  for (const row of doc.experiences.filter(row => row.install_url)) {
    Object.assign(row, { status: 'Release candidate', install_url: null, release_url: null, download: null });
    row.candidate.availability = 'private_draft_only';
    row.targets = row.targets.map(target => ({ ...target, availability: 'not_offered' }));
  }
  return doc;
};

function fixture(t, { review = false, media = false, site = false } = {}) {
  const root = mkdtempSync(path.join(os.tmpdir(), 'glassplay-publication-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const payload = Buffer.from('approved video');
  const manifestBytes = Buffer.from(JSON.stringify({ assets: [{ path: 'promo.mp4', bytes: payload.length, sha256: sha(payload) }], bundle: { sha256: 'b'.repeat(64), bytes: 200 } }));
  const policy = {
    site: { approved: site, approval_reference: site ? 'owner/site' : null, pages_eligibility_confirmed: site },
    media: { approved: media, approval_reference: media ? 'owner/media' : null, manifest_sha256: media ? sha(manifestBytes) : null, bundle_url: media ? 'https://example.com/approved.zip' : null, bundle_sha256: media ? 'b'.repeat(64) : null },
    application: { approved: false, approval_reference: null, code_license: null, art_license: null, framework_included: false, framework_permission: null, framework_notice: null },
  };
  const mode = review ? 'review' : 'public';
  const directory = review ? '.private/site' : 'dist';
  const put = (name, data) => { const file = path.join(root, name); mkdirSync(path.dirname(file), { recursive: true }); writeFileSync(file, data); };
  put('public/robots.txt', 'User-agent: *\nAllow: /\n');
  put('public/brand/favicon.svg', '<svg/>');
  put('src/pages/index.astro', 'source');
  put('src/pages/404.astro', 'source');
  put(`${directory}/robots.txt`, 'User-agent: *\nAllow: /\n');
  put(`${directory}/brand/favicon.svg`, '<svg/>');
  put(`${directory}/index.html`, `<html><meta name="robots" content="${review ? 'noindex, nofollow' : 'index, follow'}"></html>`);
  put(`${directory}/404.html`, '<html><meta name="robots" content="noindex, nofollow"></html>');
  put(`${directory}/sitemap-index.xml`, '<sitemapindex/>');
  put(`${directory}/sitemap-0.xml`, '<urlset/>');
  put(`${directory}/_astro/site.hash.css`, 'body{color:white}');
  const marker = { schema_version: 1, review, media_approved: !review && media, media_manifest_sha256: review || media ? sha(manifestBytes) : null };
  put(`${directory}/glassplay-build.json`, JSON.stringify(marker));
  if (review || media) put(`${directory}/media/nevermore/promo.mp4`, payload);
  return { root, directory, mode, policy, marker, manifestBytes, put, options: { root, policy, catalogue: withoutDownloads(structuredClone(catalogue)), manifestBytes } };
}

test('safe build can be verified before site launch approval', t => {
  const f = fixture(t);
  assert.equal(assertBuildBoundary(f.directory, f.mode, f.options).media_files, 0);
  assert.throws(() => assertPublication(f.directory, f.options), /site approval/);
});

test('rendered brand WebP is hash checked and cannot admit a video', t => {
  const f = fixture(t);
  f.put('public/brand/glasses.webp', 'original rendered art');
  f.put('dist/brand/glasses.webp', 'original rendered art');
  assert.equal(assertBuildBoundary(f.directory, f.mode, f.options).media_files, 0);
  f.put('dist/brand/glasses.webp', 'changed art');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options));
  f.put('dist/brand/glasses.webp', 'original rendered art');
  f.put('public/brand/hidden.mp4', 'private video');
  f.put('dist/brand/hidden.mp4', 'private video');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /Unexpected public source/);
});

test('site-only approval deploys title artwork without application rights', t => {
  const f = fixture(t, { site: true });
  assert.equal(assertPublication(f.directory, f.options).application_links, 0);
});

test('promotional approval needs no application release approval', t => {
  const f = fixture(t, { site: true, media: true });
  assert.equal(assertPublication(f.directory, f.options).media_files, 1);
});

test('approval in the wrong scope cannot authorize promotional media', t => {
  const f = fixture(t, { site: true, media: true });
  f.policy.media.approved = false;
  f.policy.approved = true;
  assert.throws(() => assertPublication(f.directory, f.options), /marker/);
});

test('media approval must pin current manifest and explicit reference', t => {
  const f = fixture(t, { media: true });
  f.policy.media.manifest_sha256 = '0'.repeat(64);
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /exact committed/);
  f.policy.media.manifest_sha256 = sha(f.manifestBytes);
  f.policy.media.approval_reference = ' ';
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /owner approval/);
});

test('changed media bytes and extra assets fail the actual output check', t => {
  const f = fixture(t, { media: true });
  f.put('dist/media/nevermore/promo.mp4', 'tampered video');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /changed media/);
  f.put('dist/media/nevermore/private.mp4', 'extra');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options));
});

test('source, archive and secret files cannot enter the static tree', t => {
  for (const name of ['main.py', '.env', 'release.zip', '_astro/source.js.map']) {
    const f = fixture(t);
    f.put(`dist/${name}`, 'unapproved');
    assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /allowlist/);
  }
});

test('static title artwork must remain identical to public source', t => {
  const f = fixture(t);
  f.put('dist/brand/favicon.svg', '<svg>injected</svg>');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /source\/output mismatch/);
});

test('private review passes its own boundary but cannot pass publication', t => {
  const f = fixture(t, { review: true, site: true });
  assert.equal(assertBuildBoundary(f.directory, 'review', f.options).media_files, 1);
  assert.throws(() => assertPublication(f.directory, f.options), /designated publication boundary/);
});

test('noindex review HTML fails even if marker is falsified as public', t => {
  const f = fixture(t, { site: true });
  f.put('dist/index.html', '<html><meta name="robots" content="noindex, nofollow"></html>');
  assert.throws(() => assertPublication(f.directory, f.options), /robots\/review/);
});

test('manifest path traversal is rejected before reading assets', t => {
  const f = fixture(t);
  const manifest = JSON.parse(f.manifestBytes);
  manifest.assets[0].path = '../secret.mp4';
  f.options.manifestBytes = Buffer.from(JSON.stringify(manifest));
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /flat filenames/);
});

function withDownload(f) {
  const row = f.options.catalogue.experiences[0];
  Object.assign(row, { install_url: 'https://example.com/Nevermore.zip', release_url: 'https://example.com/release',
    download: { file: 'Nevermore.zip', bytes: 1, sha256: 'a'.repeat(64) } });
  row.candidate.availability = 'public'; row.license_status = 'cleared';
  return row;
}

test('application download requires its own approval and code/art terms', t => {
  const f = fixture(t, { site: true });
  withDownload(f);
  assert.throws(() => assertPublication(f.directory, f.options), /Application downloads/);
  Object.assign(f.policy.application, { approved: true, approval_reference: 'owner/release', code_license: 'owner/code', art_license: 'owner/art', framework_notice: 'users obtain Raven Framework separately' });
  assert.equal(assertPublication(f.directory, f.options).application_links, 2);
  f.policy.application.art_license = ' ';
  assert.throws(() => assertPublication(f.directory, f.options), /code\/art terms/);
});

test('owner distribution approval is not Raven Framework permission', t => {
  const f = fixture(t, { site: true });
  withDownload(f);
  Object.assign(f.policy.application, { approved: true, approval_reference: 'owner/release', code_license: 'owner/code', art_license: 'owner/art' });
  // A package without the framework needs no Raven permission, but must say users obtain it separately.
  assert.throws(() => assertPublication(f.directory, f.options), /obtain it separately/);
  f.policy.application.framework_notice = 'users obtain Raven Framework separately';
  assert.equal(f.policy.application.framework_permission, null);
  assert.equal(assertPublication(f.directory, f.options).application_links, 2);
  // Bundling the framework would need Raven's own permission; the owner's approval does not cover it.
  f.policy.application.framework_included = true;
  assert.throws(() => assertPublication(f.directory, f.options), /Raven permission/);
  delete f.policy.application.framework_included;
  assert.throws(() => assertPublication(f.directory, f.options), /whether Raven Framework is included/);
});

test('the real policy offers the download without claiming Raven permission', () => {
  const policy = JSON.parse(readFileSync(new URL('../config/publication.json', import.meta.url), 'utf8'));
  assert.equal(policy.application.approved, true);
  assert.equal(policy.application.framework_included, false);
  assert.equal(policy.application.framework_permission, null);
  assert.match(policy.application.framework_notice, /not included/);
});

test('external private media or unapproved ZIP links cannot hide in HTML', t => {
  const f = fixture(t);
  f.put('dist/index.html', '<html><meta name="robots" content="index, follow"><video src="https://example.com/private.mp4"></video></html>');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /unapproved media/);
  f.put('dist/index.html', '<html><meta name="robots" content="index, follow"><a href="https://example.com/private.zip">Download</a></html>');
  assert.throws(() => assertBuildBoundary(f.directory, f.mode, f.options), /application download/);
});

test('unsafe protocols and credential-bearing bundle URLs fail closed', () => {
  for (const url of ['http://example.com/a.zip', 'file:///private.zip', 'https://user:password@example.com/a.zip', 'https://127.0.0.1/a.zip', 'https://localhost/a.zip', 'https://example.com/a.zip?token=secret']) {
    assert.throws(() => publicHttpsUrl(url));
  }
});

test('a committed private-repository bundle replaces the public URL only when its hash matches', t => {
  const { root, put, policy, options } = fixture(t, { media: true });
  const bundle = Buffer.from('approved bundle bytes');
  put('media-bundles/approved.zip', bundle);
  const manifest = JSON.parse(options.manifestBytes.toString('utf8'));
  manifest.bundle.sha256 = sha(bundle);
  const manifestBytes = Buffer.from(JSON.stringify(manifest));
  put('dist/glassplay-build.json', JSON.stringify({ schema_version: 1, review: false, media_approved: true, media_manifest_sha256: sha(manifestBytes) }));
  const media = { ...policy.media, bundle_url: null, bundle_path: 'media-bundles/approved.zip', bundle_sha256: sha(bundle), manifest_sha256: sha(manifestBytes) };
  const run = override => assertBuildBoundary('dist', 'public', { ...options, manifestBytes, policy: { ...policy, media: { ...media, ...override } } });
  assert.equal(run({}).media_files, 1);
  assert.throws(() => run({ bundle_url: 'https://example.com/approved.zip' }), /exactly one source/);
  assert.throws(() => run({ bundle_path: '../escape.zip' }), /media-bundles/);
  put('media-bundles/approved.zip', 'tampered');
  assert.throws(() => run({}), /differs from approval/);
  assert.ok(root);
});
