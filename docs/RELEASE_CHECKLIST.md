# Release gate — an experience is not released until these are evidenced

Use this checklist separately for each experience.

## Code and security

- [ ] Curated source snapshot with traceable source commit; no blind history mirror.
- [ ] No secrets, tokens, `app_id`/`app_key` values or personal data embedded.
- [ ] Dependencies pinned; build/install instructions tested from a clean environment.
- [ ] Runtime, cancellation/lifecycle and relevant tests pass.
- [ ] App/package clearly identifies which hardware, OS and framework versions it targets.

## Media and rights

- [ ] Source code license explicitly selected.
- [ ] Asset inventory lists every redistributed media/model/audio dependency and its license or authorization.
- [ ] Required notices/attribution included.
- [ ] Third-party proprietary frameworks installed separately unless redistribution is explicitly authorized.
- [ ] No experimental/raw/rejected source media, private archives or unnecessary large files exported.

## Hardware and product

- [ ] Simulator results described accurately.
- [ ] Real device validation done for any **device verified** claim (display, audio, mic, performance and thermals as applicable).
- [ ] Deployment credentials/entitlements obtained via an authorized channel, not committed to source.
- [ ] Clear user actions to start, stop/disarm and uninstall.
- [ ] Privacy statement matches actual microphone, camera, network and persistence behavior.

## Publication

- [ ] README has requirements, install, use, troubleshooting and limitations.
- [ ] Release files and hashes/version are traceable.
- [ ] Catalogue status, platform validation and install URL updated only **after** publishing succeeds.

**Nevermore-specific outstanding gates (2026-10-21):** physical Raven Prism unverified; distribution/deploy credentials pending; confirm rights to derived Meshy media; curated production export not yet created.
