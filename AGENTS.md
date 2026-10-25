# GlassPlay — instructions for coding agents

Build a **simple, visual collection of interactive experiences for AR smart glasses**. The root README should be a short storefront rather than a development log. Keep evidence and rights documentation in experience folders.

## Nevermore state (2026-10-25)

- **Released:** Nevermore Halloween 1.1.0 (SOFT and HAUNTED), GitHub Release `nevermore-v1.1.0` in this repository: `Nevermore-Halloween-1.1.0.zip` (65,190,942 bytes, SHA-256 `f8b154d0cab073102b3604a01e297a6e4fe2134670f47739d5b3f937e6272937`) and its `.sha256`. Record: `releases/nevermore-1.1.0.json`; catalogue and `config/publication.json` (`application.approved=true`) agree with it (`npm run check:catalogue`).
- The ZIP lives only as a release asset; never commit it. Raven Framework is not included (`framework_included=false`, `framework_permission=null`): the owner's distribution approval is not a Raven permission.
- Physical Prism stays **DEVICE-UNVERIFIED**; never present the download as an official Prism installation.
- GlassPlay became public on 2026-10-25 after a security audit; RBraga01/Nevermore stays private.

## Archived rc.2 preview (2026-10-22)

- `experiences/nevermore/app/`: 23 curated, byte-identical source files from `RBraga01/Nevermore` commit `b4980cf` (rc.2), checked by `export-manifest.json`, `releases/nevermore-rc2.json` and CI.
- This directory is **not a runnable package**: 20-event media and offline Vosk model are not copied.
- `v1.0.0-rc.2` ZIP, checksum, two demo videos, validation JSON and Raven handoff exist only as a **private draft GitHub Release** in Nevermore.
- Host/Simulator PASS, real Prism **DEVICE-UNVERIFIED**.
- Licensing decided: code MIT; Nevermore-specific artwork/media All Rights Reserved; CC0/Apache-2.0 upstream terms kept; Meshy paid-account attestation and Guardian/Bride/Chest Meshy Community CC0 remix links recorded.
- External, not Nevermore defects: Raven's official public Framework/deployment process, Prism app identity/entitlements, physical Prism validation. Public application download stays held (`application.approved=false`).

## Rules

1. Never mirror Nevermore private history, archives, raw source media, tests from unrelated experiments, the LFS store or credentials. Curate by explicit release allowlist.
2. Keep byte-identical source exports traceable; changes to Python runtime need separate engineering validation.
3. The application ZIP is distributed only as the `nevermore-v1.1.0` release asset. The only approved public website media is the 19-file website bundle `media-bundles/nevermore-web-media.zip` (owner approval 2026-10-22, pinned in `config/publication.json` and `docs/media/manifest.json`). Do not add other MP4/WAV/model assets, the private-draft videos or the application ZIP without a new explicit decision.
4. Never claim physical Prism validation without device test evidence.
5. No invented install links or release statuses. Update root README, experience page and catalogue together.
6. No speculative general launcher or complex architecture; add shared components when real second use exists.
7. The owner approved the public website and its media on 2026-10-22 (Pages from this repository). On 2026-10-25 the owner approved making this repository public after a security audit; the Nevermore development repository stays private. Application downloads, code/art licensing and Raven Framework distribution remain unapproved (`application.approved=false`). Any change to approved media needs a new owner approval and manifest hash.

## Website

Astro7 / TypeScript / static CSS. Node24.15+ and npm. Catalogue authority: catalog/experiences.json; its schema separates availability from device validation.

```sh
npm ci
npm run dev
npm run typecheck
npm test
npm run build
npm run check:site
npm run quality
python scripts/verify-release.py
python -m unittest discover -s tests -p 'test_*.py'
```

One test: `node --test --test-name-pattern="duplicate IDs" tests/catalogue.test.mjs`.

The default build includes the approved website media from the committed bundle, verified by SHA-256. Other private media goes only in ignored .private/. `npm run build:review` creates .private/site for local owner review. Never upload that directory. Public media promotion requires exact manifest and ZIP approval; see docs/DEPLOYMENT.md. Never copy original models, the SDK or a full application ZIP into public/.

The immutable curated app files intentionally use -text in .gitattributes so upstream hashes remain exact on Windows. Do not reformat those files. Source integrity is different from full application, media or device validation.
