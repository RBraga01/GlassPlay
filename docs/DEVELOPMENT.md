# Build and review GlassPlay

Node24.15+ and npm are required. This is an Astro static website, not the Nevermore runtime.

```sh
npm ci
npm run dev
# http://localhost:4321/GlassPlay/
npm run typecheck
npm test
npm run build
npm run check:site
npm run preview
```

The public-safe build at dist/ is self-contained: no sibling checkout, credentials, private media or app package is needed. Publishing it still requires explicit approval.

## Private media review

Prepare the authentic package from the approved upstream source using [the media instructions](media/README.md), then run:

```sh
npm run build:review
# PowerShell
$env:GLASSPLAY_REVIEW='1'
npm run preview -- --port 4322
# Bash: GLASSPLAY_REVIEW=1 npm run preview -- --port 4322
```

The private build lives in `.private/site`, includes noindex, and must never be uploaded as a Pages artifact. Its media sources, composition, exact hashes and licensing state are recorded separately from the public catalogue. Clear `GLASSPLAY_REVIEW` before previewing the ordinary build again.

## Quality

`npm run quality` measures the actual static dist/ build with Lighthouse mobile emulation: three runs each for the homepage and Nevermore. It requires Chrome/Chromium or CHROME_PATH (Edge can be used on Windows). Reports stay in reports/lighthouse; CI retains them privately. A successful build never enables publication.

`python scripts/verify-release.py` verifies committed source/release metadata. Supply `--source-repo` and `--archive` to verify exact upstream Git/LFS objects and a local ZIP. No private repository access is required for ordinary CI. `python -m unittest discover -s tests -p 'test_*.py'` exercises verifier rejection paths.

## Structure

- `src/`: Astro pages, components and styling.
- `catalog/`: schema-validated discovery data; no separate hardcoded experience list.
- `public/`: distributable site-only artwork, fonts' notices and robots.
- `config/publication.json`: explicit site/media/application approvals, held by default.
- `experiences/nevermore/app/`:23 byte-identical curated upstream files, not a runnable package.
- `releases/` and `docs/media/`: pinned release/media evidence and source traceability.
- `.private/`: ignored local authentic-media preparation and review. Never deployed implicitly.

Brand/share images are rendered in Blender/Cycles; see [the art pipeline](../scripts/art/README.md). `scripts/brand-images.py` is retired and cannot overwrite the new assets. Nevermore README/poster artwork is rendered from pinned approved frames using `scripts/art/nevermore_art.py`; see [media provenance](media/README.md). Authoring tools are not runtime dependencies.
