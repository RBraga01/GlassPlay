import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, readdirSync, statSync, realpathSync, existsSync } from 'node:fs';
import { resolve, relative, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, execFileSync } from 'node:child_process';
import { gzipSync } from 'node:zlib';
import { assertBuildBoundary } from './publication-policy.mjs';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const BASE = '/GlassPlay/';
const RUNS = 3;
export const THRESHOLDS = Object.freeze({ performance: 90, accessibility: 95, 'best-practices': 95, seo: 95 });
const PAGES = [{ id: 'home', path: '' }, { id: 'nevermore', path: 'experiences/nevermore/' }];
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff', '.mp4': 'video/mp4', '.webm': 'video/webm', '.vtt': 'text/vtt; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml' };

const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export function qualityOptions(args = [], root = ROOT) {
  if (args.length > 1 || (args.length === 1 && args[0] !== '--review')) {
    throw new Error('Usage: node scripts/measure-quality.mjs [--review]');
  }
  const review = args[0] === '--review';
  return { root, review, mode: review ? 'review' : 'public',
    dist: resolve(root, review ? '.private/site' : 'dist'),
    reports: resolve(root, review ? 'reports/lighthouse-review' : 'reports/lighthouse') };
}

function filesIn(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const full = resolve(directory, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Indirect build file: ${full}`);
    return entry.isDirectory() ? filesIn(full) : [full];
  });
}

/** Identify the actual output, including the media that a fallback build lacks. */
export function buildEvidence({ root, dist, review, mode }) {
  if (!existsSync(resolve(dist, 'index.html'))) {
    throw new Error(`Run npm run ${review ? 'build:review' : 'build'} before measuring ${mode} quality.`);
  }
  const markerBytes = readFileSync(resolve(dist, 'glassplay-build.json'));
  const marker = JSON.parse(markerBytes);
  if (marker.schema_version !== 1 || marker.review !== review) {
    throw new Error('Build marker does not match the requested quality mode. Rebuild the selected output.');
  }
  const files = filesIn(dist).map(full => {
    const bytes = readFileSync(full);
    return { path: relative(dist, full).split(sep).join('/'), bytes: bytes.length, sha256: sha(bytes) };
  }).sort((left, right) => left.path < right.path ? -1 : left.path > right.path ? 1 : 0);
  const media = files.filter(file => file.path.startsWith('media/'));
  const videos = media.filter(file => /\.(mp4|webm)$/i.test(file.path));
  const pages = PAGES.map(page => {
    const html = readFileSync(resolve(dist, page.path, 'index.html'), 'utf8');
    const robots = [...html.matchAll(/<meta\b[^>]*>/gi)]
      .filter(match => /\bname\s*=\s*["']robots["']/i.test(match[0])).map(match => match[0]);
    const videoSources = [...html.matchAll(/<(?:video|source)\b[^>]*\bsrc\s*=\s*["']([^"']+)["']/gi)]
      .map(match => match[1]);
    return { id: page.id, html_sha256: sha(html), noindex: robots.some(tag => /\bnoindex\b/i.test(tag)),
      robots_meta: robots, video_sources: [...new Set(videoSources)] };
  });
  if (review && (!videos.length || !pages.some(page => page.video_sources.length))) {
    throw new Error('Private review quality requires staged videos and a page that references them.');
  }
  return { mode, directory: relative(root, dist).split(sep).join('/'), marker,
    marker_sha256: sha(markerBytes), tree_sha256: sha(JSON.stringify(files)), file_count: files.length,
    media_present: media.length > 0, media_file_count: media.length, video_file_count: videos.length,
    media_bytes: media.reduce((sum, file) => sum + file.bytes, 0), media_files: media, pages };
}

/** Keep all failures, including SEO failure caused by the deliberate review noindex. */
export function evaluatePage(id, runs, { review = false, noindex = false } = {}) {
  if (runs.length !== RUNS) throw new Error(`${id}: expected ${RUNS} measurements.`);
  const scores = {};
  const failures = [];
  for (const [category, minimum] of Object.entries(THRESHOLDS)) {
    const values = runs.map(run => run.scores[category]);
    if (values.some(score => typeof score !== 'number' || !Number.isFinite(score))) {
      throw new Error(`${id}: ${category} did not produce a numeric score`);
    }
    values.sort((left, right) => left - right);
    scores[category] = category === 'performance' ? values[1] : values[0];
    if (scores[category] < minimum) failures.push(`${id}: ${category} ${scores[category]} < ${minimum}`);
  }
  const expectedLimitations = review && noindex && runs.some(run => run.indexing_audit?.score === 0)
    ? [`${id}: intentional private-review noindex; Lighthouse is-crawlable failed. SEO score and threshold are unchanged; this is not a public SEO pass.`] : [];
  return { scores, failures, expected_limitations: expectedLimitations };
}

export function qualityOutcome({ pages, failures, build }) {
  const complete = pages.length === PAGES.length;
  return {
    passed: failures.length === 0 && complete,
    nonSeoThresholdsPassed: complete && pages.every(page => Object.entries(THRESHOLDS)
      .filter(([category]) => category !== 'seo').every(([category, minimum]) => page.scores[category] >= minimum)),
    seoIndexabilityHeld: build.mode === 'review' && complete && build.pages.every(page => page.noindex)
      && pages.every(page => page.runs.length === RUNS && page.runs.every(run => run.indexing_audit?.score === 0
        && run.failed_seo_audits?.length === 1 && run.failed_seo_audits[0] === 'is-crawlable')),
  };
}

export async function measureQuality(args = process.argv.slice(2)) {
  const options = qualityOptions(args);
  const { review, mode, dist: DIST, reports: REPORTS } = options;
  assertBuildBoundary(DIST, mode);
  const build = buildEvidence(options);
  const distRealPath = realpathSync(DIST);
  const lighthouseCli = fileURLToPath(import.meta.resolve('lighthouse/cli/index.js'));
  mkdirSync(REPORTS, { recursive: true });

  // Serve only this build under its real Pages base path. Bind to loopback, use
  // gzip and the short static cache lifetime normally used by GitHub Pages.
  const server = createServer((request, response) => {
    try {
      const url = new URL(request.url, 'http://127.0.0.1');
      if (!['GET', 'HEAD'].includes(request.method) || !url.pathname.startsWith(BASE)) {
        response.writeHead(404).end('Not found'); return;
      }
      let path = resolve(DIST, decodeURIComponent(url.pathname.slice(BASE.length)));
      if (path !== DIST && !path.startsWith(`${DIST}${sep}`)) { response.writeHead(404).end(); return; }
      if (statSync(path).isDirectory()) path = resolve(path, 'index.html');
      const real = realpathSync(path);
      if (!real.startsWith(`${distRealPath}${sep}`)) { response.writeHead(404).end(); return; }
      const type = TYPES[extname(path)] || 'application/octet-stream';
      let payload = readFileSync(path);
      const headers = { 'Content-Type': type, 'Cache-Control': 'public, max-age=600', 'X-Content-Type-Options': 'nosniff' };
      if (request.headers['accept-encoding']?.includes('gzip') && /^(text\/|application\/(json|xml)|image\/svg)/.test(type)) {
        payload = gzipSync(payload);
        headers['Content-Encoding'] = 'gzip';
        headers.Vary = 'Accept-Encoding';
      }
      headers['Content-Length'] = String(payload.length);
      response.writeHead(200, headers).end(request.method === 'HEAD' ? undefined : payload);
    } catch {
      response.writeHead(404).end('Not found');
    }
  });

  function runLighthouse(url, outputPath) {
    return new Promise((done, reject) => {
      const child = spawn(process.execPath, [
        lighthouseCli, url, '--quiet', '--no-enable-error-reporting',
        '--chrome-flags=--headless=new --disable-gpu --no-first-run',
        '--only-categories=performance,accessibility,best-practices,seo',
        '--form-factor=mobile', '--throttling-method=simulate',
        '--output=json', '--output=html', `--output-path=${outputPath}`,
      ], { cwd: ROOT, env: process.env, stdio: 'inherit', windowsHide: true });
      child.once('error', reject);
      child.once('exit', (code, signal) => code === 0 ? done() : reject(new Error(`Lighthouse exited with ${signal || code}. Check CHROME_PATH and the saved reports.`)));
    });
  }

  function git(command) {
    try { return execFileSync('git', command, { cwd: ROOT, encoding: 'utf8', windowsHide: true }).trim(); }
    catch { return null; }
  }

  const summary = {
    measured_at: new Date().toISOString(),
    source_revision: git(['rev-parse', 'HEAD']),
    working_tree_dirty: Boolean(git(['status', '--porcelain'])),
    build,
    node: process.version,
    platform: process.platform,
    profile: 'Lighthouse default mobile emulation with simulated throttling',
    runs_per_page: RUNS,
    evaluation: 'Median performance score; minimum accessibility, best-practices and SEO scores across three runs.',
    scope: review ? 'PRIVATE REVIEW ONLY: authentic staged media, not approved for public distribution.' : 'Default public build; publication approval is a separate gate.',
    media_measurement_scope: 'Navigation load only. Presence and references do not prove playback; intentional playback and media transfer require separate browser evidence.',
    thresholds: THRESHOLDS,
    pages: [],
    failures: [],
    expected_limitations: [],
  };

  try {
    await new Promise((done, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', done);
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    for (const page of PAGES) {
      const url = `${origin}${BASE}${page.path}`;
      const runs = [];
      for (let index = 1; index <= RUNS; index += 1) {
        console.log(`Lighthouse (${mode}): ${page.id}, mobile run ${index}/${RUNS}`);
        const reportPath = resolve(REPORTS, `${page.id}-${index}`);
        await runLighthouse(url, reportPath);
        const report = JSON.parse(readFileSync(`${reportPath}.report.json`, 'utf8'));
        if (report.runtimeError) throw new Error(`${page.id}: ${report.runtimeError.message}`);
        const scores = {};
        for (const category of Object.keys(THRESHOLDS)) {
          const score = report.categories[category]?.score;
          if (typeof score !== 'number') throw new Error(`${page.id}: ${category} did not produce a numeric score`);
          scores[category] = score * 100;
        }
        const indexing = report.audits?.['is-crawlable'];
        runs.push({ scores, indexing_audit: indexing ? { id: 'is-crawlable', score: indexing.score, title: indexing.title, details: indexing.details } : null,
          failed_seo_audits: (report.categories.seo.auditRefs ?? []).filter(ref => ref.weight > 0 && report.audits[ref.id]?.score !== null && report.audits[ref.id]?.score < 1).map(ref => ref.id),
          media_requests: (report.audits?.['network-requests']?.details?.items ?? []).filter(item => /\.(mp4|webm)(?:[?#]|$)/i.test(item.url ?? '')).map(item => ({ url: item.url, status_code: item.statusCode, transfer_size: item.transferSize, resource_size: item.resourceSize })),
          lighthouse_version: report.lighthouseVersion, browser: report.environment?.hostUserAgent, report: `${page.id}-${index}.report.html` });
      }
      const evidence = build.pages.find(item => item.id === page.id);
      const { scores, failures, expected_limitations } = evaluatePage(page.id, runs, { review, noindex: evidence.noindex });
      summary.failures.push(...failures);
      summary.expected_limitations.push(...expected_limitations);
      summary.pages.push({ id: page.id, path: `${BASE}${page.path}`, scores, runs });
      console.log(`${page.id}: ${Object.entries(scores).map(([name, value]) => `${name} ${Math.round(value)}`).join(' / ')}`);
    }
    if (buildEvidence(options).tree_sha256 !== build.tree_sha256) {
      summary.failures.push('Build changed during measurement; rebuild and rerun before using these results.');
    }
  } catch (error) {
    summary.failures.push(error.message);
  } finally {
    server.closeAllConnections();
    if (server.listening) await new Promise((done) => server.close(done));
    Object.assign(summary, qualityOutcome(summary));
    writeFileSync(resolve(REPORTS, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
    const table = [
      `# Measured website quality — ${mode}`, '', summary.scope, '',
      `Measured ${summary.measured_at}; ${summary.profile}. ${summary.evaluation}`, '',
      `Build: \`${build.directory}\`; SHA-256 \`${build.tree_sha256}\`. Media: ${build.media_file_count} files, ${build.video_file_count} videos, ${build.media_bytes} bytes. Exact media hashes are in summary.json.`, '',
      '| Page | Performance ≥90 | Accessibility ≥95 | Best practices ≥95 | SEO ≥95 |',
      '| --- | ---: | ---: | ---: | ---: |',
      ...summary.pages.map((page) => `| ${page.id} | ${Math.round(page.scores.performance)} | ${Math.round(page.scores.accessibility)} | ${Math.round(page.scores['best-practices'])} | ${Math.round(page.scores.seo)} |`), '',
      summary.passed ? 'PASS: all measured targets met.' : `FAIL:\n${summary.failures.map((failure) => `- ${failure}`).join('\n')}`, '',
      `Non-SEO thresholds: ${summary.nonSeoThresholdsPassed ? 'PASS' : 'FAIL or incomplete'}. Intentional review indexing is the only failing SEO audit in every run: ${summary.seoIndexabilityHeld ? 'yes' : 'no'}. The overall exit code still follows all four thresholds.`, '',
      ...summary.expected_limitations.map(limitation => `- ${limitation}`), '', summary.media_measurement_scope, '',
      'These measurements describe only the fingerprinted local build. Public SEO, live hosting, owner visual approval and human keyboard, screen-reader and device review remain separate checks.', '',
    ].join('\n');
    writeFileSync(resolve(REPORTS, 'summary.md'), table);
    // Private HTML reports can embed staged images. Keep this review evidence local.
    if (!review && process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, table);
  }

  console.log(`Reports: ${relative(ROOT, REPORTS).split(sep).join('/')}/`);
  if (!summary.passed) console.error([...summary.failures, ...summary.expected_limitations].join('\n'));
  else console.log('PASS: mobile quality thresholds met.');
  return summary;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (!(await measureQuality()).passed) process.exitCode = 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
