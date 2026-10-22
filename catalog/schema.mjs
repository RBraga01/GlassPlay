import { z } from 'zod';
const localPath = z.string().min(1).refine(v => !v.startsWith('/') && !v.includes('..') && !v.includes('\\') && !v.includes(':'), 'Expected a safe relative site path');
const httpsUrl = z.url().refine(v => v.startsWith('https://'), 'Use HTTPS');
const experience = z.object({
  id: z.string().regex(/^[a-z][a-z0-9-]*$/),
  name: z.string().min(1), theme: z.string().min(1), category: z.string().min(1), summary: z.string().min(1),
  status: z.enum(['Concept', 'In development', 'Preview', 'Release candidate', 'Pilot', 'Released']),
  directory: localPath, page: localPath.nullable(), cover: localPath,
  preview: z.object({poster: localPath, video: httpsUrl.nullable(), publication: z.enum(['held','approved'])}).strict().nullable(),
  candidate: z.object({version: z.string().min(1), availability: z.enum(['private_draft_only','public']), source_commit: z.string().regex(/^[a-f0-9]{40}$/)}).strict().nullable(),
  targets: z.array(z.object({name: z.string().min(1), validation: z.enum(['host_validated','device_unverified','device_validated']), label: z.string().min(1)}).strict()),
  install_url: httpsUrl.nullable(), release_url: httpsUrl.nullable(),
  attribution: z.array(localPath).min(1), license_status: z.enum(['owner_decision_pending','cleared','concept_only']),
}).strict().superRefine((row, ctx) => {
  const fail = (/** @type {string} */ message) => ctx.addIssue({code: 'custom', message});
  if(row.status === 'Concept' && (row.candidate || row.install_url || row.release_url || row.page || row.targets.length)) fail('Concepts cannot claim availability, devices or working product pages');
  if(row.candidate?.availability === 'private_draft_only' && (row.install_url || row.release_url)) fail('Private candidates cannot expose download links');
  if(row.preview?.publication !== 'approved' && row.preview?.video) fail('Unapproved preview media cannot be published');
  if(row.status === 'Released' && (!row.install_url || !row.release_url || row.license_status !== 'cleared' || row.candidate?.availability !== 'public')) fail('Released needs a public, licensed install and release');
  if(row.install_url && row.license_status !== 'cleared') fail('Installation needs cleared rights');
});
export const catalogueSchema = z.object({schema_version: z.literal(2), experiences: z.array(experience).min(1)}).strict().superRefine((doc, ctx) => {
  if(new Set(doc.experiences.map(row => row.id)).size !== doc.experiences.length) ctx.addIssue({code:'custom',message:'Duplicate experience id'});
});
export function parseCatalogue(/** @type {unknown} */ data) { return catalogueSchema.parse(data); }
