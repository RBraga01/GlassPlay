# Nevermore — distribution gates

**Source preview in GlassPlay:** 23 verbatim source/manifest/test files, updated to Nevermore commit `81df295`. **No audiovisual media or SDK is present here.**

**Complete release candidate in Nevermore:** Private GitHub **draft** `v1.0.0-rc.1` contains the ~55 MB Python ZIP, checksum, two new simulator videos and validation JSON. It has **not been published**.

| Item | Actual status |
| --- | --- |
| Curated 20-event runtime media and model | **Packaged and checked in the private RC ZIP; not copied to GlassPlay** |
| Windows-host / Simulator Room testing | **PASS** — 79 application tests in clean export; 87 in private repo, 20 events and new captures |
| Meshy-derived production character assets | **USER-ATTESTED-MESHY-PAID-ACCOUNT** — owner declaration recorded; account documents not independently inspected |
| Code and authored-art public license | **Owner decision still required** — no automatic MIT/open license |
| Raven Framework 1.0.6 | Proprietary dependency **excluded from the package**; confirm authorization for public distribution/use |
| Prism deployment IDs/keys | Not embedded or published; authorized provisioning required |
| Real Raven Prism validation | **DEVICE-UNVERIFIED** — display, speakers, microphone, frame delivery and thermals |
| Live speech reliability across users/noise | Not established; recorded voice test passed through actual Vosk pipeline |
| Blender/GLB/FBX source, raw audio, archives and private history | **Excluded** from production export and GlassPlay |

## Next release decisions

1. Choose the license/permissions for original code and artwork; retain third-party notices and Meshy owner-attestation wording.
2. Confirm with Raven the permitted framework use and Prism deployment path.
3. If releasing a **Windows / Simulator preview**, label its scope explicitly and verify installation with a separately authorized SDK. This does not require claiming physical Prism compatibility.
4. For **Prism compatibility**, run device acceptance tests; keep `DEVICE-UNVERIFIED` until then.
5. Publish only approved demo media, credits, downloads and checksums; then set a real install URL in the GlassPlay catalogue.

The [source manifest](export-manifest.json) pins every copied file. Do **not** mirror the private history or export the large research archive.
