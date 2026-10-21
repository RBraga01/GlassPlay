# Website review evidence

Captured on Windows / Edge, 2026-10-21, from the actual static builds at the `/GlassPlay/` base path. These screenshots contain only original site title artwork. Screenshots and videos containing approved-but-private Nevermore production artwork stay in ignored `.private/` / `output/` locations.

| Surface | Desktop | Mobile |
| --- | --- | --- |
| Homepage | [First viewport](home-desktop.png) | [Full page](home-mobile.png) |
| Nevermore | [First viewport](nevermore-desktop.png) | [Full page](nevermore-mobile.png) |

## Actual measurements

Lighthouse 13.5.0 / Edge 155, mobile emulation and simulated throttling, three runs per page. Performance is the median; accessibility, best practices and SEO use the minimum of the three runs.

| Page | Performance | Accessibility | Best practices | SEO |
| --- | ---: | ---: | ---: | ---: |
| Homepage | 100 | 100 | 100 | 100 |
| Nevermore | 99 | 100 | 100 | 100 |

The [machine-readable result](lighthouse-summary.json) records the exact measurement time, browser and dirty-tree state. It was measured before the implementation commit; it is not a measurement of the starting Git revision alone. Full HTML reports remain local under `reports/lighthouse/`. GitHub CI runs its own measurements against the PR revision and retains reports as private artifacts.

The build measured here is the public title-art fallback. Private media review was exercised separately in the browser; no Lighthouse score is claimed for private gameplay media. A deployed-site measurement will be needed after an authorized launch.

GitHub independently measured the implementation in [quality run 39682749686](https://github.com/RBraga01/GlassPlay/actions/runs/39682749686): **98/100/100/100 for both pages**. [CI summary](lighthouse-ci-summary.json) is copied directly from that run's artifact. All five applicable workflows passed for implementation commit `dd8253cf94c497270217e02804929036785708ce`; the following documentation-only commit preserves the evidence without changing build inputs.

## Browser behavior

[Viewport checks](browser-review.json) cover 15 page/width combinations, including both media states: 320, 390, 768, 1024 and 1440 pixels. Image loading, overflow, local-only resource requests, no autoplay and reduced motion passed. One 320px title overflow was found and fixed before recording these results.

[Interaction checks](browser-interactions.json) verify keyboard skip-to-main, discovery navigation, native keyboard disclosure, real video advancement, 11 loaded caption cues, ended/nonlooping state, silent teaser and a visible recovery message on forced media network failure. The forced failure is intentional and is not a production console error. The browser decoded the audio/video stream; this is not a claim that a human listened or that a physical device played it.

## Visual review

A fresh independent reviewer inspected original-size desktop/mobile captures and the written direction. The first review requested two bounded corrections: move category metadata below the featured title, and use authored SVG breadcrumb/disclosure icons. Both were applied and recaptured. Final disposition: **ship**; no remaining findings or introduced regressions.

The review preserves the cinematic editorial direction, mint/lavender separation, authentic private media and deliberate publication-held artwork fallback. No public launch, hardware validation or independent license/account audit is implied by this disposition.
