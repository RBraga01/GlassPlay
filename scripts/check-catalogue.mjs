import { readFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { parseCatalogue } from '../catalog/schema.mjs';
const catalogue = parseCatalogue(JSON.parse(readFileSync('catalog/experiences.json','utf8')));
for (const row of catalogue.experiences) {
  assert(existsSync(row.directory), `Missing experience directory: ${row.directory}`);
  assert(existsSync(`public/${row.cover}`), `Missing cover: ${row.cover}`);
}
const nevermore = catalogue.experiences.find(row => row.id === 'nevermore');
// The catalogue must agree with the public release record (experiences/nevermore/ is the archived rc.2 preview).
const release = JSON.parse(readFileSync(`releases/nevermore-${nevermore.candidate.version}.json`,'utf8'));
assert.equal(nevermore.candidate.source_commit, release.source_commit, 'Nevermore source revision disagrees');
assert.equal(nevermore.candidate.version, release.version, 'Nevermore version disagrees');
assert.equal(nevermore.install_url, release.asset.url, 'Nevermore download URL disagrees');
assert.equal(nevermore.release_url, release.release_url, 'Nevermore release URL disagrees');
assert.deepEqual(nevermore.download, {file: release.asset.file, bytes: release.asset.bytes, sha256: release.asset.sha256}, 'Nevermore download file disagrees');
console.log(`PASS: ${catalogue.experiences.length} catalogue entries; availability and device validation separated.`);
