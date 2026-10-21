# GlassPlay — instructions for coding agents

**Product:** Simple, discoverable seasonal **experiences for AR smart glasses**. Prioritize a strong, honest product page and a curated, independently verifiable release path. Keep the root README short and understandable to non-developers.

## Current work

- `experiences/nevermore/app/` is a **source-only curated copy** of production code and logic tests. Do not call it a runnable release.
- `experiences/nevermore/export-manifest.json` pins the original source commit and blob IDs.
- `experiences/nevermore/ASSETS_PENDING.md` tracks withheld media, licenses, hardware and deploy gates.
- `catalog/experiences.json` is discovery metadata; future festivities are still ideas.

## Hard boundaries

1. Never mirror the private Nevermore repository, archive, source media, raw renders, entire LFS history or credentials. Export only reviewed, explicitly selected paths.
2. Preserve source-file integrity while staging; if changing runtime code, clearly separate new changes from the verbatim export and test them.
3. Do not distribute MP4/WAV/BLEND/GLB, offline Vosk weights or Raven Framework until permission/attribution checks and packaging gates pass.
4. Physical Prism remains **DEVICE-UNVERIFIED**. Simulator results are not physical-device results.
5. Do not invent install links, supported devices or published versions.
6. Keep the root README and Nevermore overview user-facing. Engineering details belong in `app/README.md`, `ASSETS_PENDING.md` and `docs/`.
7. Change status consistently in `README.md`, experience page and `catalog/experiences.json` after evidence exists.
8. No unused platform abstractions; extract reusable code only when two experiences share an actual need.
