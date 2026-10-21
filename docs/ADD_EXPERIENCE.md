# Add an experience

1. Pick a short, memorable name and a lowercase directory slug.
2. Copy `templates/experience/` to `experiences/<slug>/`.
3. Explain what users will see, how to start/stop, privacy and compatibility — or state **concept only**.
4. Add it to [the catalogue](../catalog/experiences.json) and update the root README.
5. Put code and tests alongside the experience. Only extract code into `shared/` after real reuse.
6. Publish an install link **only after** [the release checklist](RELEASE_CHECKLIST.md) passes.

Catalogue v2 uses these exact product states: `Concept`, `In development`, `Preview`, `Pilot`, `Released`. Availability remains separate: Nevermore's Preview candidate is `private_draft_only`; this does not imply a public download.

Declare device validation separately: `host_validated`, `device_unverified` or `device_validated`. Install/release URLs remain null until a real authorized public package exists. The schema rejects released private drafts, concepts with product pages/downloads, duplicate IDs, unsafe paths and unapproved preview URLs.

Provide a cover under public/brand, an experience directory and attribution. Concepts automatically appear on the homepage. When a real experience exists, add its authored route and set `page`; use the shared layout and media policy rather than a new engine. Run `npm run check:catalogue`, `npm test`, `npm run build` and `npm run check:site`. See catalog/schema.mjs and the template for the full contract.
