# Nevermore media package

The promotional package is prepared for **private review**. The binary files live
only in the ignored `.private/media/nevermore/` directory. This document and
`manifest.json` contain edit decisions and hashes; they do not publish the media.

## Contents

| File | Purpose | Dimensions / length |
| --- | --- | --- |
| `promo.mp4` | Main preview, with original scene and captured Simulator audio | 960 × 540, 24 fps, 26.42 seconds |
| `teaser.mp4` | Lightweight production-animation montage, no audio stream | 640 × 360, 24 fps, 7.25 seconds |
| `cover.webp` | Four approved character frames composed on black | 1200 × 630 |
| `host.webp`, `raven.webp`, `bride.webp`, `mimic.webp` | Four visual highlights | 960 × 720 |
| `poster.webp` | Main video poster with Nevermore title | 1200 × 630 |
| `glassplay-social.webp` | GlassPlay social card featuring Nevermore | 1200 × 630 |
| `*-small.webp` | Responsive cover/poster/social and character variants | 640 × 336 or 480 × 360 |
| `captions.vtt` | English spoken lines and relevant sound descriptions | WebVTT |
| `transcript.md` | Visual description, speech and provenance context | Plain Markdown |
| `CREDITS.txt` | Attribution pointers and current rights status | Plain text |
| `review-manifest.json` | Private copy of the checked-in manifest | JSON |

Exact sizes and SHA-256 values are in [manifest.json](manifest.json). There are no
fonts, raw audio, original 3D models or source videos copied into this package.

The final nineteen assets are also packaged in
`.private/nevermore-web-media.zip`, with flat filenames. The ZIP excludes
`review-manifest.json`, contact sheets, intermediates and original source files.
The machine-readable `assets` array contains `{path, sha256, bytes}` for every
flat member; `bundle` records the ZIP's local path, SHA-256 and byte size. Its
fixed timestamps, order and file permissions produce the same archive from
identical deliverables. The ZIP is ignored by Git and is not published.

## Editorial decisions

The opening uses actual approved runtime renders: the frozen Raven Dive, Midnight
Host, Ocular Maw Chest and the Bride's approved hand gesture. Their original
scene audio remains synchronized. The main video then shows excerpts from the
two current release-candidate Simulator Room demonstrations. Both types of image
have distinct burned-in labels. Native speed and 24 fps are retained.

| Main preview time | Content | Source interval |
| --- | --- | --- |
| 0.00–1.75 | Raven Dive production animation | Frames 24–65 |
| 1.75–5.00 | Midnight Host production animation | Frames 0–77 |
| 5.00–7.92 | Ocular Maw Chest production animation | Frames 0–69 |
| 7.92–11.17 | Bride production animation | Frames 0–77 |
| 11.17–17.46 | Host and chest in Simulator Room | Product capture, frames 408–558 |
| 17.46–21.08 | Bride in Simulator Room | Product capture, frames 1084–1170 |
| 21.08–24.42 | Raven Dive in Simulator Room | Catalogue capture, frames 343–422 |
| 24.42–26.42 | Nevermore end card | Composition of the selected stills |

This is an edited montage of review-triggered encounters. It is not a continuous
play session, a demonstration of live microphone input, or physical-device
footage. Room excerpts use the exact current draft captures under
`docs/release/validation/`; nothing from `docs/prefinal/` or `archive/` is used.
The final raven excerpt is labelled “The Raven Returns”; it makes no claim that
the voice command is shown in that cut.

The cover and social card combine frames of several encounters on black. They
are editorial artwork compositions, not screenshots of simultaneous gameplay.
Gallery stills use a crop of the original black margins, proportional resizing
and WebP compression. There is no synthetic imagery, pose replacement,
relighting, color grading or new soundtrack. The main video's audio has only
15 ms/35 ms edge fades, resampling and delivery compression. PCM intermediates
avoid adding AAC priming gaps between cuts.

Recommended visible image caption: **“Approved Nevermore runtime artwork.”**
Recommended video caption: **“Production animation and Raven Simulator Room
footage. Physical Raven Prism testing is pending.”** The surrounding page should
identify the montage and provide the transcript. Video playback should require
an explicit user action for sound; a teaser may be muted, with reduced-motion
preferences respected.

## Rebuild

Use a local checkout of `RBraga01/Nevermore` at
`81df295f6825189bfba05288aca76595b4c59437` with the current runtime assets and RC1
captures available. The script pins all twelve input hashes, including the
approved Raven Dive SHA-256
`fc5b704d9b0bcdac15cd3a052aa766c13d918fdc830b43c5f660c97c8b788503`.
A different source hash stops the build and requires a new media review.

```powershell
python scripts/prepare-media.py --source E:/raven/Nevermore-main
```

On the preparation workstation, Python is available at
`E:/Projectos/raven-framework/.venv/Scripts/python.exe`. The script requires
Pillow, OpenCV, NumPy, and `imageio-ffmpeg`, or an explicit `--ffmpeg` executable.
It uses system Arial/Georgia on Windows and DejaVu fonts on Linux. Those system
fonts are rendered into the editorial titles and are never copied. Pixel hashes
can differ across font and encoder versions; the pinned source selection and
edit timeline are reproducible. `--images-only` rebuilds the stills without
rewriting the complete delivery manifest.

Output is deliberately fixed to `.private/media/nevermore/`, with its final ZIP
at `.private/nevermore-web-media.zip`. The script verifies
that Git ignores that directory before writing deliverables. It never copies
anything to `public/`, commits files or publishes a release. Intermediate video
files are written to a temporary private directory and removed after encoding.

## Verification and review

The package was generated from the pinned inputs, decoded with FFmpeg, and
inspected through source contact sheets, final stills and representative frames
throughout the main preview. The main output has an H.264 video stream and stereo
48 kHz AAC audio. The teaser has an H.264 video stream and no audio stream.
Responsive dimensions, output hashes and file sizes were checked. The files are
ignored by Git. ZIP member names, sizes and SHA-256 hashes were checked against
the complete allowlist; the archive contains only the nineteen finished assets.

Captions follow the source voice cue metadata and include the Host's two
“Trick or Treat?” lines. The transcript supplies a complete text alternative.
Automated decoding and source timing verification do not constitute a human
listening review; that review remains part of owner approval.

## Rights and publication gate

Model provenance remains **USER-ATTESTED-MESHY-PAID-ACCOUNT**. No independent
account or contract inspection is claimed. Original source credits and sound
attribution remain in Nevermore's `assets/production/provenance.json`,
`assets/trick_or_treat/audio/voice/voice_manifest.json` and
`docs/release/public/THIRD_PARTY_NOTICES.md`, at the pinned revision.

Public artwork/media licensing, applicable Raven Framework permissions and the
publication decision remain outstanding. Physical Prism is **DEVICE-UNVERIFIED**.
The presence of completed promotional files does not authorize their public
distribution. An approved deployment must explicitly select authorized assets;
the default build must continue using its public-safe fallback until then.
