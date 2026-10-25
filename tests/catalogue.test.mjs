import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseCatalogue } from '../catalog/schema.mjs';
const source=JSON.parse(readFileSync(new URL('../catalog/experiences.json',import.meta.url),'utf8'));
function changed(change) {const doc=structuredClone(source);change(doc);return ()=>parseCatalogue(doc);}
test('real catalogue distinguishes preview from physical-device validation',()=>assert.equal(parseCatalogue(source).experiences[0].targets[1].validation,'device_unverified'));
test('duplicate IDs rejected',()=>assert.throws(changed(d=>d.experiences.push(d.experiences[0]))));
test('private draft cannot keep an install link',()=>assert.throws(changed(d=>{d.experiences[0].status='Release candidate';d.experiences[0].candidate.availability='private_draft_only';})));
test('concept cannot claim a working page',()=>assert.throws(changed(d=>d.experiences[1].page='experiences/christmas/')));
test('unapproved media cannot gain public video',()=>assert.throws(changed(d=>d.experiences[0].preview.video='https://example.com/video.mp4')));
test('released cannot mean private draft',()=>assert.throws(changed(d=>d.experiences[0].candidate.availability='private_draft_only')));
test('released Nevermore offers the verified Windows/Simulator download, not Prism',()=>{const row=parseCatalogue(source).experiences[0];assert.equal(row.status,'Released');assert.deepEqual(row.targets.map(t=>[t.validation,t.availability]),[['host_validated','public_download'],['device_unverified','not_offered']]);assert(row.install_url.endsWith('/'+row.download.file));});
test('unverified device cannot become a download target',()=>assert.throws(changed(d=>d.experiences[0].targets[1].availability='public_download')));
test('install link needs its recorded file, size and hash',()=>{assert.throws(changed(d=>d.experiences[0].download=null));assert.throws(changed(d=>d.experiences[0].install_url='https://example.com/other.zip'));assert.throws(changed(d=>d.experiences[0].download.sha256='nothex'));});
test('download target cannot exist without an install link',()=>assert.throws(changed(d=>{const r=d.experiences[0];r.install_url=null;r.download=null;r.status='Release candidate';})));
test('asset traversal rejected',()=>assert.throws(changed(d=>d.experiences[0].cover='../private/file.webp')));
test('unknown device verification rejected',()=>assert.throws(changed(d=>d.experiences[0].targets[1].validation='probably_works')));
test('future concepts need no fake download',()=>assert(parseCatalogue(source).experiences.filter(x=>x.status==='Concept').every(x=>x.install_url===null)));
