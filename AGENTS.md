# GlassPlay — instructions for coding agents

Build a **simple, visual collection of interactive experiences for AR smart glasses**. The root README should be a short storefront rather than a development log. Keep evidence and rights documentation in experience folders.

## Nevermore state (2026-10-21)

- `experiences/nevermore/app/`: 23 curated, byte-identical source files from `RBraga01/Nevermore` commit `81df295`, checked by `export-manifest.json` and CI.
- This directory is **not a runnable package**: 20-event media and offline Vosk model are not copied.
- The complete `v1.0.0-rc.1` ZIP, checksums and two demo videos exist only as **private draft GitHub Release** assets in Nevermore.
- Host/Simulator PASS, real Prism **DEVICE-UNVERIFIED**.
- Meshy status: **USER-ATTESTED-MESHY-PAID-ACCOUNT**, no independent account inspection. Do not regress this back to an unresolved request, but do not claim independent verification.
- Public source/art license and use/distribution permission for proprietary Raven Framework **remain outstanding**.

## Rules

1. Never mirror Nevermore private history, archives, raw source media, tests from unrelated experiments, the LFS store or credentials. Curate by explicit release allowlist.
2. Keep byte-identical source exports traceable; changes to Python runtime need separate engineering validation.
3. The only approved public media is the 19-file website bundle `media-bundles/nevermore-web-media.zip` (owner approval 2026-10-22, pinned in `config/publication.json` and `docs/media/manifest.json`). Do not add other MP4/WAV/model assets, the private-draft videos or the application ZIP without a new explicit decision.
4. Never claim physical Prism validation without device test evidence.
5. No invented install links or release statuses. Update root README, experience page and catalogue together.
6. No speculative general launcher or complex architecture; add shared components when real second use exists.
7. The owner approved the public website and its media on 2026-10-22 (GitHub Pro, Pages from this private repository). The repository stays private. Application downloads, code/art licensing and Raven Framework distribution remain unapproved (`application.approved=false`). Any change to approved media needs a new owner approval and manifest hash.

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
