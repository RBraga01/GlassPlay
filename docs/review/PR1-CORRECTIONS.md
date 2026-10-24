# PR #1 — owner-requested corrections

Prepared 2026-10-22 against the review of `17ed373`. **Changes are ready for owner visual review. No merge or publication is authorized.** The earlier “ship” verdict is superseded.

## Five review points

| Request | Correction |
| --- | --- |
| One GlassPlay identity | Restored the original navy/violet direction and an immediate AR-glasses subject. Manrope leads the season-neutral collection; Nevermore retains a separate cinematic atmosphere. Removed the mint/arch hero. |
| Professional rendered artwork | Separate media artists produced original Blender/Cycles conceptual glasses and feather artwork, and a Blender composition of exact approved Nevermore frames. Both README heroes, website hero/poster, responsive exports, icons and social images are replaced. The old Pillow illustration exporter is retired. |
| Public credits | Visitor-facing Meshy wording follows the owner's requested text. Uppercase audit labels remain only in internal records. Exported media credits were also corrected. |
| Private source, public site | The source stays private. The visitor footer and prominent creator links lead to the accessible public profile. Deployment documentation covers private-repository GitHub Pages, Cloudflare, and a separate approved static-artifacts repository; no hosting change was made. Site/media/application approvals remain separate and false. |
| Real-media review | Fresh full-size captures, actual video playback, responsive and accessibility checks, and separate Lighthouse runs for both build modes. No fallback score is represented as a real-media score. |

## New artwork

- [GlassPlay README banner](../assets/glassplay-hero.webp): 2400 × 720.
- [Nevermore README banner](../../experiences/nevermore/cover.webp): 2400 × 840.
- [Brand render provenance](../art/brand.json), [rebuild instructions](../../scripts/art/README.md).
- [Nevermore derivative provenance](../media/manifest.json), [processing and source-frame notes](../media/README.md).
- Editable Blender scenes are saved under `.private/art-source/` on the production workstation. Their hashes and paths are recorded; committed scripts reproduce them.

The glasses are original conceptual illustration, not a Prism product photograph. The Nevermore composition uses 640 × 640 source frames enlarged for the banner; it does not invent extra source detail or replace approved game scenes. The promo, teaser, source animation and audio remain byte-identical to the reviewed baseline. Original models and private ZIPs are not included in the website.

## Full-resolution owner review

These PNGs show the **actual private media review**, not the fallback. They were stored for review in this repository (then private), outside `public/`, and excluded from website builds. Public distribution still requires separate approval.

| Page | Desktop, 1440 px | Mobile, 390 px |
| --- | --- | --- |
| GlassPlay | [Full page](pr1/home-desktop.png) | [Full page](pr1/home-mobile.png) |
| Nevermore | [Full page](pr1/nevermore-desktop.png) | [Full page](pr1/nevermore-mobile.png) |

Independent internal review identified the mobile character crop, cramped status text and buried creator link. These were corrected. That review does not approve the design on behalf of the owner.

## Measured quality

Lighthouse 13.5.0 on Windows/Chromium 156, mobile emulation, three runs per page. Performance is the median; other categories use the minimum. Measurements record the pre-commit dirty tree plus exact built-tree, HTML and media hashes.

| Build / page | Performance | Accessibility | Best practices | SEO |
| --- | ---: | ---: | ---: | ---: |
| Actual media review / home | 99 | 100 | 100 | 66 |
| Actual media review / Nevermore | 95 | 100 | 100 | 66 |
| Public fallback / home | 100 | 100 | 100 | 100 |
| Public fallback / Nevermore | 98 | 100 | 100 | 100 |

[Actual-media measurements](pr1/lighthouse-review.json) · [Fallback measurements](pr1/lighthouse-public.json)

The review command exits **1** because private `noindex` fails `is-crawlable`, the only failed SEO audit. Scores and ≥95 SEO thresholds were not relaxed. `nonSeoThresholdsPassed=true`, `seoIndexabilityHeld=true`. This is deliberately **not a public SEO pass**. The default public build exits 0. Approved public media must still be validated at the chosen deployment destination before launch.

Lighthouse measures page navigation, not playback. The videos use `preload="none"`, so navigation requests no MP4. Playback was tested separately against the real MP4s:

- Full promo: 26.416667 s, 634 decoded frames, 0 dropped frames in the complete mobile-sized run, 11 caption cues, audio stream decoded, ended paused, no loop or restart.
- Teaser: 7.25 s, 174 decoded frames, 0 dropped frames, intentionally muted, ended once.
- Both media responses support HTTP 206 range requests. No automatic playback or failed resource request during the full runs.
- A separate short desktop playback advanced normally; 2 of 54 frames were dropped while Lighthouse ran concurrently. No zero-drop desktop claim is made.
- Simulated media failure shows a readable recovery message. Decoder evidence is not a new human listening review.

[Browser, media and capture evidence](pr1/browser-and-media.json) records the actual results and file hashes.

## Verification

- **33 Node tests** and **21 Python tests** pass. New coverage verifies review-build evidence, truthful noindex reporting and hash-checked brand WebP without admitting video into `public/brand`.
- Astro/TypeScript: 0 errors, warnings or hints. Authoring Python compilation passes.
- Both builds, catalogue and generated links/assets/metadata checks pass.
- 15 page/width combinations (320, 390, 768, 1024, 1440): no horizontal overflow, missing image, page JavaScript error or private-repository visitor link.
- Keyboard skip link, discovery navigation, disclosures and reduced motion pass.
- All 19 staged derivatives match the manifest; both MP4s decode and are unchanged. All 23 curated application source files remain exact.
- Public output: 26 files, 0 private media, 0 application links. Review: 45 files, including 19 hash-verified derivatives.
- Publication check correctly returns **HELD**. Repository visibility, main, Pages, application download policy and private release assets are unchanged.

## Remaining decisions

Owner visual approval of this corrected revision, exact promotional-media permission, and hosting authorization/eligibility. Application distribution remains a separate decision. Physical Prism remains **DEVICE-UNVERIFIED**. No merge, public deployment, source-visibility change or private release upload was performed.
