# Add an experience

An experience is a named, independently documented AR smart-glasses activity. Its theme can be seasonal or permanent.

## Steps

1. Choose a memorable lowercase kebab-case slug (e.g., `christmas`) and an explicit experience name.
2. Copy the starter from `templates/experience/` into `experiences/<slug>/`; replace every template placeholder.
3. Write a concise README: what the user sees, controls, privacy, installation, supported hardware, limitations and current status.
4. Add/update the entry in `catalog/experiences.json`. Keep `id` equal to the directory slug and `install_url: null` until an actual install/release page exists.
5. Add the experience to the root README.
6. When code/assets exist, place their build/test docs alongside them. Extract shared code only after a second real use.
7. Do not advertise a download until the applicable [release checklist](RELEASE_CHECKLIST.md) is complete.

## Catalogue fields

- `schema_version` (top level): currently `1`.
- `id`, `name`, `theme`, `summary`, `directory`.
- `status`: `concept` (idea only), `in_development`, `pilot_candidate_export_pending`, `pilot` (package exists, limited validation), or `released`.
- `targets`: array of `{ "name": "...", "validation": "simulator_only|device_verified|not_tested" }`. Document version and proof in the experience README.
- `install_url`: URL to a real approved install source, otherwise `null`.

For `concept`, keep `targets: []` and `install_url: null`. A released experience must also have a verified install route and explicit device support limits.
