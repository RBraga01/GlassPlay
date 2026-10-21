import { createServer } from 'node:http';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, statSync, realpathSync, existsSync } from 'node:fs';
import { resolve, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, execFileSync } from 'node:child_process';
import { gzipSync } from 'node:zlib';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const DIST = resolve(ROOT, 'dist');
const REPORTS = resolve(ROOT, 'reports/lighthouse');
const BASE = '/GlassPlay/';
const RUNS = 3;
const THRESHOLDS = { performance: 90, accessibility: 95, 'best-practices': 95, seo: 95 };
const PAGES = [{ id: 'home', path: '' }, { id: 'nevermore', path: 'experiences/nevermore/' }];
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff', '.mp4': 'video/mp4', '.webm': 'video/webm', '.vtt': 'text/vtt; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml' };

if (!existsSync(resolve(DIST, 'index.html'))) throw new Error('Run npm run build before measuring quality.');
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
  node: process.version,
  platform: process.platform,
  profile: 'Lighthouse default mobile emulation with simulated throttling',
  runs_per_page: RUNS,
  evaluation: 'Median performance score; minimum accessibility, best-practices and SEO scores across three runs.',
  thresholds: THRESHOLDS,
  pages: [],
  failures: [],
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
      console.log(`Lighthouse: ${page.id}, mobile run ${index}/${RUNS}`);
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
      runs.push({ scores, lighthouse_version: report.lighthouseVersion, browser: report.environment?.hostUserAgent, report: `${page.id}-${index}.report.html` });
    }
    const scores = {};
    for (const [category, minimum] of Object.entries(THRESHOLDS)) {
      const values = runs.map((run) => run.scores[category]).sort((left, right) => left - right);
      scores[category] = category === 'performance' ? values[1] : values[0];
      if (scores[category] < minimum) summary.failures.push(`${page.id}: ${category} ${scores[category]} < ${minimum}`);
    }
    summary.pages.push({ id: page.id, path: `${BASE}${page.path}`, scores, runs });
    console.log(`${page.id}: ${Object.entries(scores).map(([name, value]) => `${name} ${Math.round(value)}`).join(' / ')}`);
  }
} catch (error) {
  summary.failures.push(error.message);
} finally {
  server.closeAllConnections();
  await new Promise((done) => server.close(done));
  summary.passed = summary.failures.length === 0 && summary.pages.length === PAGES.length;
  writeFileSync(resolve(REPORTS, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
  const table = [
    '# Measured website quality', '',
    `Measured ${summary.measured_at}; ${summary.profile}. ${summary.evaluation}`, '',
    '| Page | Performance ≥90 | Accessibility ≥95 | Best practices ≥95 | SEO ≥95 |',
    '| --- | ---: | ---: | ---: | ---: |',
    ...summary.pages.map((page) => `| ${page.id} | ${Math.round(page.scores.performance)} | ${Math.round(page.scores.accessibility)} | ${Math.round(page.scores['best-practices'])} | ${Math.round(page.scores.seo)} |`), '',
    summary.passed ? 'PASS: all measured targets met.' : `FAIL:\n${summary.failures.map((failure) => `- ${failure}`).join('\n')}`, '',
    'These are measurements of the local production build. A live Pages audit and human keyboard, screen-reader and device review remain separate checks.', '',
  ].join('\n');
  writeFileSync(resolve(REPORTS, 'summary.md'), table);
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, table);
}

if (!summary.passed) {
  console.error(summary.failures.join('\n'));
  process.exitCode = 1;
} else {
  console.log('PASS: mobile quality thresholds met. Reports: reports/lighthouse/');
}
