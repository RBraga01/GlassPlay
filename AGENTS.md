# GlassPlay — repository guidance

GlassPlay is a curated **collection of AR smart-glasses experiences**, not a mirror of existing development repositories.

## Source of truth

- `README.md`: public-facing catalogue and current status.
- `catalog/experiences.json`: machine-readable index.
- `experiences/<slug>/README.md`: experience status and instructions.
- `docs/RELEASE_CHECKLIST.md`: explicit gates before a downloadable release.

## Non-negotiable boundaries

1. Do not copy or mirror `RBraga01/Nevermore` (or another private research repository) wholesale. Copy only audited, explicitly selected release files when instructed; keep private Git history, archives, experiments, raw source assets and credentials out.
2. Do not present concept directories as released products. Keep catalogue status consistent with evidence.
3. Never claim Prism hardware compatibility until tested on physical hardware. Simulator evidence must be labelled as simulator evidence.
4. Never redistribute Raven Framework or third-party media/models without verified permissions and notices. No invented legal approvals.
5. Keep experiences independent at first. Introduce `shared/` and `platforms/` code only to support real integrations rather than speculative abstractions.
6. No hardcoded app ID/key, access tokens, API keys or other secrets. Never record microphone samples or transcripts by default.
7. Maintain the project's clear user-facing naming and searchable AR/smart glasses descriptions.

## When adding or changing an experience

Update the experience README, `catalog/experiences.json`, and root README together. Follow `docs/ADD_EXPERIENCE.md`. Before publishing assets or binaries follow `docs/RELEASE_CHECKLIST.md`.
