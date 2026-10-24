# Website build and controlled publication

Live GitHub Pages site: `https://rbraga01.github.io/GlassPlay/` (launched 2026-10-22). Astro uses `site: https://rbraga01.github.io` and `base: /GlassPlay`, including internal links, assets and canonical URLs, as described in the [official Astro Pages guide](https://docs.astro.build/en/guides/deploy/github/). On 2026-10-25 the owner approved making this repository public after a security audit; the Nevermore development repository stays private.

The owner approved the website launch and its media on 2026-10-22; see the launch record below. No workflow changes repository visibility, fetches private Nevermore release assets, or changes Pages settings.

## Local verification

Use Node.js 24 and the committed npm lockfile:

```sh
npm ci
npm run check:catalogue
npm run typecheck
npm test
npm run build
npm run check:site
node scripts/measure-quality.mjs
python scripts/verify-release.py
python -m unittest discover -s tests -p 'test_*.py'
```

The site checker examines the generated `dist/` tree: required routes, local links and fragments, asset references, `/GlassPlay/` paths, canonical/OG/Twitter metadata, actual 1200 × 630 social images, concept availability, image alternatives and explicit video controls. It rejects media that can autoplay with sound. It makes no external requests; external-link availability and human interaction checks remain part of review.

The quality script starts and stops its own server on loopback at the real `/GlassPlay/` path. It uses the locked Lighthouse CLI and installed Chrome/Chromium (`CHROME_PATH` can select a browser), default mobile emulation and simulated throttling. It measures homepage and Nevermore three times. The performance median must be at least 90; the minimum accessibility, best practices and SEO scores must each be at least 95. Reports include actual browser/Lighthouse versions, source revision, dirty-tree state, build mode, an exact output-tree SHA-256, per-file media hashes and each page's video references. JSON, HTML and a summary are written to `reports/lighthouse/`. CI preserves these default-build reports for 14 days, including failing runs. No score is estimated or skipped to obtain a pass.

`npm run build` produces the default public asset tree. Without media approval it uses the intentional title-art fallback. Approved media requires the explicit bundle configuration, SHA-256 checks and file allowlist; there is no automatic promotion from a private draft. Any optional internal review build that includes `.private/media/nevermore` writes to `.private/site` for local inspection only. Never upload that tree as a Pages artifact or general Actions artifact. Return to the default build before performing publication checks.

To measure the actual local version with authentic staged promotional videos:

```sh
npm run build:review
node scripts/measure-quality.mjs --review
```

This command validates the review build boundary and writes only to `reports/lighthouse-review/`, leaving default quality reports separate. It rejects a review build without staged videos and page references. Keep these reports local too: Lighthouse HTML can contain screenshots of private media. The review pages intentionally retain `noindex, nofollow`; the summary records the real `is-crawlable` audit and all failing SEO audit IDs. SEO remains subject to the same ≥95 target, so an intentional indexing failure still returns a failing exit code and an explicit limitation. It must never be described as public SEO passing.

In the JSON summary, `nonSeoThresholdsPassed` reports whether both pages meet performance, accessibility and best-practices targets. `seoIndexabilityHeld` is true only for a complete review run where the actual pages have `noindex` and `is-crawlable` is the sole failing weighted SEO audit in every run. `passed` and the exit code continue to enforce all four categories. A missing measurement or another SEO defect cannot be reported as only the expected indexing hold.

Lighthouse measures navigation load. The summary distinguishes staged videos from video requests observed during navigation; `preload="none"` may correctly mean no video bytes were requested. Record separate browser evidence of intentional playback, transfer, captions, pause/end behavior and failure recovery. Rebuild and rerun responsiveness, visual review, accessibility, media behavior and quality measurements after the final rendered art or promotional media changes. A fallback report cannot approve the version with videos, and private review evidence does not authorize publication. The approved public build and live destination need their own checks.

## Workflows

| Workflow | Purpose | Public publication permission |
| --- | --- | --- |
| `site.yml` | TypeScript/Astro validation, tests, production build and generated site checks | None |
| `catalogue.yml` | Catalogue schema and availability consistency | None |
| `quality.yml` | Actual mobile Lighthouse measurements on both representative pages | None |
| `nevermore-source.yml` | Existing immutable source hashes and Python logic regression tests | None |
| `release-integrity.yml` | Curated source and committed release evidence; verifier rejection tests | None |
| `pages.yml` | Approved production build, publication policy check and Pages deployment | Gated |

Integrity CI does not have private release ZIPs or the complete Nevermore repository. The verifier reports those unavailable checks as `NOT_RUN`; it does not represent them as passed. Full private archive and media validation must be recorded separately before approving a downloadable release. Source/logic success is not physical Prism verification.

## Private source, public site: owner hosting choice

**Chosen route (2026-10-22): GitHub Pages from this repository**, then private, after the owner confirmed GitHub Pro. The repository became public on the owner's approval of 2026-10-25. The alternatives below are kept for reference only.

| Route | Source and public output | Decision and implementation needed |
| --- | --- | --- |
| GitHub Pages from this private repository | GlassPlay stays private; only the approved generated website is public | Confirm personal GitHub Pro eligibility; then use the existing gated Pages workflow and procedure below |
| Cloudflare Pages with this private GitHub repository | GlassPlay stays private; Cloudflare receives access to this selected repository and publishes only approved `dist/` | Approve Cloudflare as host, repository integration and URL; implement and review the host-specific publication gate and URL configuration before connecting/deploying |
| Separate public repository containing build artifacts only | GlassPlay stays private; only the reviewed static output and required notices enter the new public repository | Explicitly approve creating that public repository and its content; add a narrow approved-output transfer and Pages setup for its URL |

GitHub supports Pages from private repositories on Pro, Team and Enterprise; personal GitHub Pro is the relevant plan here. GitHub Free supports Pages from public repositories, which makes a separate artifacts repository an option without publishing GlassPlay source. [GitHub Pages availability](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

Private repositories on Pro can use environments and deployment branch restrictions. Required environment reviewers and wait timers are available only on public repositories under Free, Pro and Team. If an independent approval is required on each deployment, the owner must choose a setup that supports that protection before launch. See [GitHub environment availability](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments). This workflow checks for an existing environment with branch restrictions and a protected `main`; merely naming an environment in YAML would otherwise create an unprotected one automatically.

Cloudflare Pages supports private GitHub repositories through its Git integration. Limit the app's access to the selected GlassPlay repository. Its Free plan currently allows 500 builds per month and assets up to 25 MiB each; verify the final media package against the chosen host's limits. [Cloudflare Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/), [GitHub integration access](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/).

For Cloudflare, the proposed static build uses Node 24.15+ and the lockfile, `npm run build`, and output `dist/`, followed by the adapted site/media publication check before any upload. This project needs no SSR adapter. Cloudflare normally creates production and preview deployments from Git pushes; configure production to `main` and disable preview deployments so an unapproved branch cannot become a public preview. Do not connect the current branch before the gate is implemented. [Cloudflare Astro deployment](https://developers.cloudflare.com/pages/framework-guides/deploy-an-astro-site/), [branch deployment controls](https://developers.cloudflare.com/pages/configuration/branch-build-controls/).

The current publication checker explicitly requires GitHub Pages eligibility, and the Astro config, URL helper and site checker use the GitHub origin and `/GlassPlay/` path. An alternative host therefore needs a reviewed change that selects the actual destination, makes the eligibility gate host-specific, and updates base paths, canonical/social URLs, sitemap, robots and the hosting privacy notice together. Do not mark `pages_eligibility_confirmed=true` to bypass this for Cloudflare. Validate the adapted default build and its exact approved media before owner-authorized deployment.

For the public artifacts repository option, transfer only the checked `dist/` contents and required website notices after site/media approval. Never copy repository history, `experiences/nevermore/app/`, `.private/`, source models, reports or the application ZIP. A different repository name changes the Pages path, so rebuild for that destination before publishing. This is an owner-approved publication of static artifacts, with reuse terms recorded separately; it is not a source visibility change.

## Site-first scope for the Raven introduction

The intended Oct 28 introduction can present GlassPlay, an accurately labelled independent Nevermore Windows/Simulator demo, approved promotional visuals, credits and the working [RBraga01 public profile](https://github.com/RBraga01). The profile is the available public contact destination; no email address or separate contact site has been provided. It does not imply Raven endorsement or physical Prism testing.

The owner must approve the final visual result, hosting destination, exact site revision and each promotional-media hash after the relevant rights review. Record website approval in `site` and promotional-media approval in `media` independently. Keep `application.approved=false`, `install_url=null` and `release_url=null` for this launch. A decision about publishing application source, its license, the ZIP or application SDK distribution can follow separately. Promotional use still needs its own applicable artwork/audio/SDK permissions. Current state: `site` and `media` are approved (2026-10-22); `application` remains `false`, and physical Prism remains `DEVICE-UNVERIFIED`.

## Launch record

On 2026-10-22 the owner confirmed GitHub Pro, approved the website and its 19-file media bundle, and asked for Pages publication while the repository stays private. The bundle is committed as `media-bundles/nevermore-web-media.zip` (`bundle_path`), so the build needs no public download host or credentials. Application downloads remain unapproved. Physical Prism remains `DEVICE-UNVERIFIED`.

## Owner launch procedure for the prepared GitHub Pages route

Complete these steps only after the owner authorizes public deployment:

1. Review the exact website, attribution, approved asset hashes and publication decisions in `config/publication.json`. Approve the website and its content explicitly. The Nevermore application download, code license, artwork/media rights and Raven Framework distribution permission are separate decisions; a website approval must not silently enable a download.
2. For a media release, configure the owner-approved media bundle (a public HTTPS `bundle_url`, or a ZIP committed to this private repository under `media-bundles/` as `bundle_path` — exactly one), bundle SHA-256 and exact per-file allowlist through a reviewed change. The production build may fetch only that authorized bundle and must verify its contents before adding them to `dist/`. Record its provenance and authorization. Internal staged files and private draft assets do not gain publication permission by existing locally or by passing tests.
3. Run the commands above against the default build, followed by `npm run check:publication`. The publication check must enforce the committed policy and fail while approval or asset permission is missing.
4. Confirm private-repository Pages eligibility with the owner. Configure Pages to use GitHub Actions. This is a manual owner-authorized setup; no workflow enables Pages.
5. Protect `main` so website changes require reviewed pull requests and passing checks. Create the `github-pages` environment before enabling publication. Restrict deployment to `main` (or protected branches with `main` protected). Add required reviewers and disable bypass where the plan supports them. If stronger approval rules are required but unavailable, resolve that owner decision first.
6. Set repository Actions variable `PAGES_PUBLICATION_APPROVED` to the exact string `true` only after these decisions and settings are in place. Leave it unset or `false` beforehand.
7. Run **Publish approved website** from **main**, explicitly checking `confirm_publication`. The workflow validates the existing environment and protected main branch, rebuilds without private review media, enforces publication policy, then uploads only `dist/`. The deploy job runs under `github-pages` and its configured protections.
8. Verify the live homepage, Nevermore and credits routes, real asset responses, mobile navigation, metadata and Lighthouse results. Record the deployed commit and URL. Local measurements do not prove the live deployment works.

After launch approval, reviewed changes merged into `main` can update the site automatically while `PAGES_PUBLICATION_APPROVED` remains `true`; the committed policy and environment rules still apply. A manual run additionally requires the explicit confirmation checkbox. Feature branches and pull requests cannot deploy.

To stop future deployments, set `PAGES_PUBLICATION_APPROVED` to `false`. This does not remove an already public site. Removing a live site or reverting published material is a separate owner decision. For a content regression, revert the reviewed site change, rerun checks, and publish the approved correction through the same gate.
