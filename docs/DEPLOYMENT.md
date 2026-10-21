# Website build and controlled publication

Target: `https://rbraga01.github.io/GlassPlay/`. Astro uses `site: https://rbraga01.github.io` and `base: /GlassPlay`, including internal links, assets and canonical URLs, as described in the [official Astro Pages guide](https://docs.astro.build/en/guides/deploy/github/).

The implementation brief authorizes preparing the website and deployment workflow. It does not authorize public launch. The normal build and pull request checks work while launch decisions remain pending. No workflow changes repository visibility, fetches private Nevermore release assets, or enables Pages automatically.

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

The quality script starts and stops its own server on loopback at the real `/GlassPlay/` path. It uses the locked Lighthouse CLI and installed Chrome/Chromium (`CHROME_PATH` can select a browser), default mobile emulation and simulated throttling. It measures homepage and Nevermore three times. The performance median must be at least 90; the minimum accessibility, best practices and SEO scores must each be at least 95. Reports include actual browser/Lighthouse versions, source revision and dirty-tree state. JSON, HTML and a summary are written to `reports/lighthouse/`. CI preserves them for 14 days, including failing runs. No score is estimated or skipped to obtain a pass.

`npm run build` produces the default public asset tree. Without media approval it uses the intentional title-art fallback. Approved media requires the explicit bundle configuration, SHA-256 checks and file allowlist; there is no automatic promotion from a private draft. Any optional internal review build that includes `.private/media/nevermore` writes to `.private/site` for local inspection only. Never upload that tree as a Pages artifact or general Actions artifact. Return to the default build before performing publication checks.

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

## Hosting eligibility and visibility

The repository is personal and private. The baseline account API inspection returned `plan: null`, and the Pages endpoint returned HTTP 404. These responses do **not** establish account eligibility; owner confirmation is still needed. GitHub documents Pages in private repositories for GitHub Pro, Team and Enterprise, with Pro being the applicable personal-account plan. A site published from private source can expose its generated content publicly. See [GitHub Pages availability](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

Private repositories on Pro can use environments and deployment branch restrictions. Required environment reviewers and wait timers are available only on public repositories under Free, Pro and Team. If an independent approval is required on each deployment, the owner must choose a setup that supports that protection before launch. See [GitHub environment availability](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments). This workflow checks for an existing environment with branch restrictions and a protected `main`; merely naming an environment in YAML would otherwise create an unprotected one automatically.

Do not change repository visibility to resolve an eligibility issue. A separate public site repository, if chosen, requires owner approval and would contain only the reviewed website assets.

## Owner launch procedure

Complete these steps only after the owner authorizes public deployment:

1. Review the exact website, attribution, approved asset hashes and publication decisions in `config/publication.json`. Approve the website and its content explicitly. The Nevermore application download, code license, artwork/media rights and Raven Framework distribution permission are separate decisions; a website approval must not silently enable a download.
2. For a media release, configure the owner-approved HTTPS media bundle, bundle SHA-256 and exact per-file allowlist through a reviewed change. The production build may fetch only that authorized bundle and must verify its contents before adding them to `dist/`. Record its provenance and authorization. Internal staged files and private draft assets do not gain publication permission by existing locally or by passing tests.
3. Run the commands above against the default build, followed by `npm run check:publication`. The publication check must enforce the committed policy and fail while approval or asset permission is missing.
4. Confirm private-repository Pages eligibility with the owner. Configure Pages to use GitHub Actions. This is a manual owner-authorized setup; no workflow enables Pages.
5. Protect `main` so website changes require reviewed pull requests and passing checks. Create the `github-pages` environment before enabling publication. Restrict deployment to `main` (or protected branches with `main` protected). Add required reviewers and disable bypass where the plan supports them. If stronger approval rules are required but unavailable, resolve that owner decision first.
6. Set repository Actions variable `PAGES_PUBLICATION_APPROVED` to the exact string `true` only after these decisions and settings are in place. Leave it unset or `false` beforehand.
7. Run **Publish approved website** from **main**, explicitly checking `confirm_publication`. The workflow validates the existing environment and protected main branch, rebuilds without private review media, enforces publication policy, then uploads only `dist/`. The deploy job runs under `github-pages` and its configured protections.
8. Verify the live homepage, Nevermore and credits routes, real asset responses, mobile navigation, metadata and Lighthouse results. Record the deployed commit and URL. Local measurements do not prove the live deployment works.

After launch approval, reviewed changes merged into `main` can update the site automatically while `PAGES_PUBLICATION_APPROVED` remains `true`; the committed policy and environment rules still apply. A manual run additionally requires the explicit confirmation checkbox. Feature branches and pull requests cannot deploy.

To stop future deployments, set `PAGES_PUBLICATION_APPROVED` to `false`. This does not remove an already public site. Removing a live site or reverting published material is a separate owner decision. For a content regression, revert the reviewed site change, rerun checks, and publish the approved correction through the same gate.
