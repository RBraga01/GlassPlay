import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { buildEvidence, evaluatePage, qualityOptions, qualityOutcome, THRESHOLDS } from '../scripts/measure-quality.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function fixture(t, { review = false, video = review } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'glassplay-quality-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const options = qualityOptions(review ? ['--review'] : [], root);
  const put = (name, data) => {
    const path = join(options.dist, name);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, data);
  };
  const html = `<html><meta name="robots" content="${review ? 'noindex, nofollow' : 'index, follow'}">${video ? '<video controls><source src="/GlassPlay/media/nevermore/promo.mp4"></video>' : ''}</html>`;
  put('index.html', html);
  put('experiences/nevermore/index.html', html);
  put('glassplay-build.json', JSON.stringify({ schema_version: 1, review, media_approved: false, media_manifest_sha256: video ? 'a'.repeat(64) : null }));
  if (video) put('media/nevermore/promo.mp4', 'fixture video bytes');
  return { options, put };
}

const run = (overrides = {}) => ({ scores: { performance: 100, accessibility: 100, 'best-practices': 100, seo: 100, ...overrides },
  indexing_audit: { score: overrides.seo === 80 ? 0 : 1 }, failed_seo_audits: overrides.seo === 80 ? ['is-crawlable'] : [] });

test('review CLI isolates its build and reports from default output', () => {
  const root = resolve('fixture-root');
  const standard = qualityOptions([], root);
  const review = qualityOptions(['--review'], root);
  assert.equal(standard.dist, join(root, 'dist'));
  assert.equal(standard.reports, join(root, 'reports/lighthouse'));
  assert.equal(review.dist, join(root, '.private/site'));
  assert.equal(review.reports, join(root, 'reports/lighthouse-review'));
  assert.notEqual(standard.reports, review.reports);
  assert.throws(() => qualityOptions(['--dist=.private/site']), /Usage/);
  assert.throws(() => qualityOptions(['--review', '--review']), /Usage/);
  assert.throws(() => qualityOptions(['--review', '--output=reports/lighthouse']), /Usage/);
});

test('review evidence records exact media and HTML hashes without changing noindex', t => {
  const { options, put } = fixture(t, { review: true });
  const before = readFileSync(join(options.dist, 'index.html'));
  const evidence = buildEvidence(options);
  assert.equal(evidence.mode, 'review');
  assert.equal(evidence.directory, '.private/site');
  assert.equal(evidence.media_present, true);
  assert.equal(evidence.video_file_count, 1);
  assert.equal(evidence.media_files[0].sha256, sha('fixture video bytes'));
  assert.equal(evidence.pages[0].html_sha256, sha(before));
  assert.equal(evidence.pages[0].noindex, true);
  assert.deepEqual(evidence.pages[0].video_sources, ['/GlassPlay/media/nevermore/promo.mp4']);
  assert.deepEqual(readFileSync(join(options.dist, 'index.html')), before);
  put('media/nevermore/promo.mp4', 'different video bytes');
  assert.notEqual(buildEvidence(options).tree_sha256, evidence.tree_sha256);
});

test('fallback evidence explicitly records absent media', t => {
  const { options } = fixture(t);
  const evidence = buildEvidence(options);
  assert.equal(evidence.mode, 'public');
  assert.equal(evidence.media_present, false);
  assert.equal(evidence.video_file_count, 0);
  assert.deepEqual(evidence.media_files, []);
  assert.deepEqual(evidence.pages[0].video_sources, []);
});

test('wrong build mode cannot masquerade as review evidence', t => {
  const { options, put } = fixture(t, { review: true });
  put('glassplay-build.json', JSON.stringify({ schema_version: 1, review: false }));
  assert.throws(() => buildEvidence(options), /does not match/);
});

test('review mode refuses fallback without videos', t => {
  const { options } = fixture(t, { review: true, video: false });
  assert.throws(() => buildEvidence(options), /requires staged videos/);
});

test('review noindex remains a failing SEO score with an explicit limitation', () => {
  const result = evaluatePage('home', [run({ seo: 80 }), run({ seo: 80 }), run({ seo: 80 })], { review: true, noindex: true });
  assert.equal(THRESHOLDS.seo, 95);
  assert.equal(result.scores.seo, 80);
  assert.deepEqual(result.failures, ['home: seo 80 < 95']);
  assert.match(result.expected_limitations[0], /is-crawlable failed/);
});

test('public noindex failure is never excused as a review limitation', () => {
  const result = evaluatePage('home', [run({ seo: 80 }), run({ seo: 80 }), run({ seo: 80 })], { noindex: true });
  assert.deepEqual(result.failures, ['home: seo 80 < 95']);
  assert.deepEqual(result.expected_limitations, []);
});

test('review still enforces performance median and minimum accessibility/best-practices', () => {
  const result = evaluatePage('home', [run({ performance: 89, accessibility: 94, seo: 80 }), run({ performance: 88, 'best-practices': 94, seo: 80 }), run({ seo: 80 })], { review: true, noindex: true });
  assert.equal(result.scores.performance, 89);
  assert.equal(result.failures.length, 4);
  assert.throws(() => evaluatePage('home', [run(), run()]), /expected 3/);
});

test('indexability hold requires noindex and only is-crawlable failure in every completed run', () => {
  const summary = { build: { mode: 'review', pages: [{ noindex: true }, { noindex: true }] }, failures: ['home: seo 80 < 95', 'nevermore: seo 80 < 95'],
    pages: ['home', 'nevermore'].map(id => ({ id, scores: run({ seo: 80 }).scores, runs: [run({ seo: 80 }), run({ seo: 80 }), run({ seo: 80 })] })) };
  assert.deepEqual(qualityOutcome(summary), { passed: false, nonSeoThresholdsPassed: true, seoIndexabilityHeld: true });
  summary.pages[1].runs[1].failed_seo_audits.push('document-title');
  assert.equal(qualityOutcome(summary).seoIndexabilityHeld, false);
  summary.pages[0].scores.accessibility = 94;
  assert.equal(qualityOutcome(summary).nonSeoThresholdsPassed, false);
  summary.pages.pop();
  assert.equal(qualityOutcome(summary).seoIndexabilityHeld, false);
});
