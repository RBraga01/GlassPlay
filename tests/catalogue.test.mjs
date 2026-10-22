import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseCatalogue } from '../catalog/schema.mjs';
const source=JSON.parse(readFileSync(new URL('../catalog/experiences.json',import.meta.url),'utf8'));
function changed(change) {const doc=structuredClone(source);change(doc);return ()=>parseCatalogue(doc);}
test('real catalogue distinguishes preview from physical-device validation',()=>assert.equal(parseCatalogue(source).experiences[0].targets[1].validation,'device_unverified'));
test('duplicate IDs rejected',()=>assert.throws(changed(d=>d.experiences.push(d.experiences[0]))));
test('private draft cannot gain install link',()=>assert.throws(changed(d=>d.experiences[0].install_url='https://example.com/download')));
test('concept cannot claim a working page',()=>assert.throws(changed(d=>d.experiences[1].page='experiences/christmas/')));
test('unapproved media cannot gain public video',()=>assert.throws(changed(d=>d.experiences[0].preview.video='https://example.com/video.mp4')));
test('released cannot mean private draft',()=>assert.throws(changed(d=>d.experiences[0].status='Released')));
test('asset traversal rejected',()=>assert.throws(changed(d=>d.experiences[0].cover='../private/file.webp')));
test('unknown device verification rejected',()=>assert.throws(changed(d=>d.experiences[0].targets[1].validation='probably_works')));
test('future concepts need no fake download',()=>assert(parseCatalogue(source).experiences.filter(x=>x.status==='Concept').every(x=>x.install_url===null)));
