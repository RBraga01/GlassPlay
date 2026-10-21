# Add an experience

1. Pick a short, memorable name and a lowercase directory slug.
2. Copy `templates/experience/` to `experiences/<slug>/`.
3. Explain what users will see, how to start/stop, privacy and compatibility — or state **concept only**.
4. Add it to [the catalogue](../catalog/experiences.json) and update the root README.
5. Put code and tests alongside the experience. Only extract code into `shared/` after real reuse.
6. Publish an install link **only after** [the release checklist](RELEASE_CHECKLIST.md) passes.

Catalogue statuses currently used:
- `concept`: idea only, no runnable application.
- `source_preview_only`: curated source exists but no distributable package.
- `in_development`: active work, not installable.
- `pilot`: a limited, explicitly tested installable build.
- `released`: available package, with hardware/support limits identified.

Declare devices separately from validation: `simulator_only`, `device_verified` or `not_tested`. An `install_url` is `null` unless a real package exists.
