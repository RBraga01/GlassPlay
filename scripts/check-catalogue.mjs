import { readFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { parseCatalogue } from '../catalog/schema.mjs';
const catalogue = parseCatalogue(JSON.parse(readFileSync('catalog/experiences.json','utf8')));
for (const row of catalogue.experiences) {
  assert(existsSync(row.directory), `Missing experience directory: ${row.directory}`);
  assert(existsSync(`public/${row.cover}`), `Missing cover: ${row.cover}`);
}
const nevermore = catalogue.experiences.find(row => row.id === 'nevermore');
const provenance = JSON.parse(readFileSync('experiences/nevermore/export-manifest.json','utf8'));
assert.equal(nevermore.candidate.source_commit, provenance.source.commit, 'Nevermore source revision disagrees');
assert.equal(nevermore.candidate.version, provenance.latest_candidate.version, 'Nevermore version disagrees');
console.log(`PASS: ${catalogue.experiences.length} catalogue entries; availability and device validation separated.`);
