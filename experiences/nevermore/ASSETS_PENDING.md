# Nevermore — what's held back

The **source code is staged**, but **media and deployment are not approved for distribution**.

| Component | In GlassPlay? | Gate |
| --- | --- | --- |
| Production Python runtime (original, unmodified) | **Yes** | Source review / integration validation |
| Logic-only test subset | **Yes** | Runs without clips or device |
| Production and Trick/Treat JSON scene indexes | **Yes** | Indexes only; not media |
| 640 × 640 H.264 encounter videos | **No** | Confirm redistribution rights, select final assets, package |
| WAV soundtracks / authored speech | **No** | Verify provenance, attribution and media rights |
| Raven Dive clip and final mix | **No** | Verify exact approved source and rights |
| Vosk offline speech recognition model | **No** | Package under applicable Apache-2.0 terms and notices, verify size/runtime |
| Blender/GLB/FBX sources, raw recordings and research renders | **No** | Not needed for end users; keep in private research |
| Raven Framework | **No** | Obtain independently; obey Raven licensing |
| Raven Prism deployment app ID / key | **No** | Provision via Raven's approved process, never commit secrets |

## Release decisions still needed

1. Confirm media/model redistribution permissions, especially any Meshy-derived assets, and prepare `ASSET_LICENSES.md`.
2. Export **only** the final approved 20-event media set and its required voice model; check manifests, hashes, names, frame rate and playback.
3. Confirm the Raven Framework installation/deployment route and configure app identity securely.
4. Validate display, sound, mic, performance, battery/thermals on a physical Prism; keep **DEVICE-UNVERIFIED** until tested.
5. Make a clean, reproducible user package and only then publish an install link and release tag.

Source origin is recorded in [export-manifest.json](export-manifest.json). **Do not copy the private repository's history, archives, raw renders or entire LFS object store.**
