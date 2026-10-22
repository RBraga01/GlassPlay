# Nevermore integration baseline

## Current candidate: 1.0.0-rc.2

Verified on 22 October 2026; machine-readable evidence in
[`releases/nevermore-rc2.json`](../../releases/nevermore-rc2.json).

| Item | Verified state |
| --- | --- |
| Integrated Nevermore source | `b4980cfc7c6c93838892d966c61284bfd0740214` (in Nevermore `main`) |
| Package | `Nevermore-1.0.0-rc.2.zip`, 54,802,288 bytes, SHA-256 `21f946888e59623f5b19539c76042379ceda9cfd1cdc01e14d25a00502f95edc`; 98 pinned payload files |
| Distribution | Private GitHub **draft** release `v1.0.0-rc.2` in Nevermore (ZIP, checksum, two Room videos, validation JSON, Raven handoff) |
| Curated source | 23 files, byte-identical to upstream Git objects |
| Licensing | Code MIT; Nevermore artwork/media All Rights Reserved; CC0/Apache-2.0 upstream terms kept |
| Raven Framework | External, not included or relicensed; verified with 1.0.6 / `791afd896cc646636ef906f5bf06c09c8fbb430a` |
| Physical Raven Prism | **DEVICE-UNVERIFIED** |

Verify with `python scripts/verify-release.py --source-repo <Nevermore checkout> --archive <rc.2 ZIP> --artifact private_draft`.
The sections below record the earlier rc.1 baseline for history.

## Earlier baseline: 1.0.0-rc.1

Verified on 21 October 2026. Machine-readable evidence, individual source SHA-256s,
all runtime SHA-256s and both complete package file lists are in
[`releases/nevermore-rc1.json`](../../releases/nevermore-rc1.json).

| Item | Verified state |
| --- | --- |
| GlassPlay starting revision | `167be9491ad54e7b177450d69234adbedc3d3fc3` |
| Integrated Nevermore source | `81df295f6825189bfba05288aca76595b4c59437` |
| Original private draft package source | `a5f12176953e04d23018609666e5d16ee5f035fc` |
| Refreshed local package source | `81df295f6825189bfba05288aca76595b4c59437` |
| Curated source | 23 files, byte-identical to upstream Git objects |
| Runtime catalogue | 20 events; 17 unique MP4/WAV pairs, including 3 approved aliases |
| Package contents | 95 manifest-pinned payload files plus `RELEASE_MANIFEST.json` |
| Raven Framework | External version 1.0.6, commit `791afd896cc646636ef906f5bf06c09c8fbb430a`; absent from both ZIPs |
| Physical Raven Prism | **DEVICE-UNVERIFIED** |

The local Nevermore checkout was clean on `main` at `a5f1217` and was fast-forwarded
to the already published `origin/main` revision `81df295`. No runtime change,
new upstream commit, push, draft replacement or publication was made.

## Changes since the original ZIP

Seven upstream commits refine the owner's Meshy attestation, production
provenance, its generator and integration documentation. Neither application
Python, runtime media, approved animations nor the two media catalogues changed.
The exact seven changed paths are recorded in `source_delta.changed_paths`.

The original ZIP remains an immutable baseline. Its credits say
`USER-ATTESTED-MESHY-LICENSE`. The refreshed local ZIP was built with the existing,
unchanged `tools/package_public.py` and includes the precise current status
`USER-ATTESTED-MESHY-PAID-ACCOUNT`. Its manifest records `81df295`.
Ten documentation/tool payloads also differ only through Windows CRLF checkout
conversion. Runtime application/media bytes remain unchanged between ZIPs.

The 23 GlassPlay source files were restored to the exact LF bytes of their
upstream Git objects after detecting local checkout conversion. Their committed
source content did not change. `.gitattributes` preserves these bytes on Windows.
The source preview contains no media, speech model or SDK and is not runnable.

## Candidate checksums

Both archives are named `Nevermore-1.0.0-rc.1.zip` in separate private locations.
The updated candidate has **not** replaced the existing private GitHub draft.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Original private draft | 54,795,276 | `9b7a2f3547a64740314830eafe97bc2e7ae0587bef1ac930ff8997f2995d97c9` |
| Refreshed local candidate | 54,795,473 | `d4fecf4cbafcc5c3c0060c4dcc7066434152bd5527466141937f76a17bec5179` |

Maintainer locations on the preparation workstation:

- Original: `E:/raven/releases/public-ready/Nevermore-1.0.0-rc.1.zip`.
- Updated: `E:/raven/releases/glassplay-ready/Nevermore-1.0.0-rc.1.zip`.
- Updated extracted application: `E:/raven/releases/glassplay-ready/Nevermore-1.0.0-rc.1/`.
- Matching `.sha256` files are beside the archives.

These are internal filesystem locations, not download links. No ZIP, original
model, runtime MP4/WAV, SDK or offline model was added to GlassPlay.

## Verification executed

| Check | Actual result |
| --- | --- |
| Existing curated source verifier | PASS: 23 exact Git blobs, no extra application files |
| Curated logic tests | 16 passed |
| Current upstream application and packaging tests | 87 passed in 20.64 seconds |
| Original clean package application tests | 79 passed in 24.03 seconds |
| Refreshed clean package application tests | 79 passed in 20.91 seconds |
| Both archive checksums and closed payload lists | PASS: 95 pinned payload files plus manifest, each archive |
| Upstream provenance for packaged source/model/media/docs | PASS: 92 upstream-origin payloads per archive; 3 generated payloads verified by package SHA-256 |
| Runtime pins against exact latest Git/LFS objects | PASS: all 34 unique runtime files |
| Original and refreshed package media decode | PASS: all 20 events, 640×640 at 24 fps, black final frames, stereo 16-bit WAV without clipping |
| Refreshed application/tests/verifier compilation | PASS; bytecode cache outside the package |
| Integrity verifier regression tests | 10 passed, including mutation, extra files, symlinks, duplicates, traversal and Python `-O` |

Tests ran on Windows with Python 3.14.4, pytest 8.4.2, OpenCV 5.0.0,
NumPy 2.5.3 and the existing Raven Framework checkout at the pinned commit.
Qt application tests use offscreen rendering; the controller tests substitute
the audio device where specified by upstream tests. These runs do not establish
physical hardware behavior, a fresh microphone accuracy result or a clean-machine
installation result. Earlier Windows/Simulator capture evidence remains upstream
in `docs/release/validation`; no new hardware capture is claimed here.

Remote CI status, website/browser checks and deployment eligibility are separate
delivery evidence. Successful local package checks do not imply those checks ran.
