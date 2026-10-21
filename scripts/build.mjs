import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, copyFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { publicationInputs, assertMediaApproval, assertBuildBoundary } from './publication-policy.mjs';

const review = process.argv.includes('--review');
const inputs = publicationInputs();
const approved = !review && inputs.policy.media.approved;
if (approved) {
  assertMediaApproval(inputs);
  execFileSync(process.env.PYTHON || 'python', ['scripts/ready-media.py'], { stdio: 'inherit' });
}
if (review && !existsSync('.private/media/nevermore/cover.webp')) {
  throw new Error('Private media is not staged. Run scripts/prepare-media.py first. The public build needs no private assets.');
}
execFileSync(process.execPath, ['scripts/check-catalogue.mjs'], { stdio: 'inherit' });
const pkg = JSON.parse(readFileSync('node_modules/astro/package.json', 'utf8'));
const bin = typeof pkg.bin === 'string' ? pkg.bin : pkg.bin.astro;
execFileSync(process.execPath, [path.join('node_modules/astro', bin), 'build'], {
  stdio: 'inherit', env: { ...process.env, GLASSPLAY_REVIEW: review ? '1' : '0', GLASSPLAY_PUBLIC_MEDIA: approved ? '1' : '0' },
});
const output = review ? '.private/site' : 'dist';
if (review || approved) {
  const source = review ? '.private/media/nevermore' : `.private/approved-media/${inputs.manifestHash}`;
  const destination = `${output}/media/nevermore`;
  mkdirSync(destination, { recursive: true });
  for (const {path: file} of inputs.manifest.assets) {
    copyFileSync(path.join(source, file), path.join(destination, file));
  }
}
writeFileSync(`${output}/glassplay-build.json`, JSON.stringify({ schema_version: 1, review, media_approved: approved,
  media_manifest_sha256: review || approved ? inputs.manifestHash : null }, null, 2));
console.log(assertBuildBoundary(output, review ? 'review' : 'public'));
if (review) {
  console.log('PRIVATE REVIEW ONLY: .private/site. Never upload this directory to Pages.');
} else {
  // A normal build must be reproducible without private or neighboring repositories.
  console.log(`Publication-safe build: dist (${approved ? 'explicitly approved media' : 'title artwork only'}). Publishing still requires explicit approval.`);
}
