# Nevermore media package

The promotional package is prepared for **private review**. The binary files live
only in the ignored `.private/media/nevermore/` directory. This document and
`manifest.json` contain edit decisions and hashes; they do not publish the media.

## Contents

| File | Purpose | Dimensions / length |
| --- | --- | --- |
| `promo.mp4` | Main preview, with original scene and captured Simulator audio | 960 × 540, 24 fps, 26.42 seconds |
| `teaser.mp4` | Lightweight production-animation montage, no audio stream | 640 × 360, 24 fps, 7.25 seconds |
| `cover.webp` | Blender composition of the approved raven, Host and Bride frames, with space for website copy | 1200 × 630 |
| `host.webp`, `raven.webp`, `bride.webp`, `mimic.webp` | Four visual highlights | 960 × 720 |
| `poster.webp` | Main video poster with Nevermore title | 1200 × 630 |
| `glassplay-social.webp` | GlassPlay social card featuring Nevermore | 1200 × 630 |
| `*-small.webp` | Responsive cover/poster/social and character variants | 640 × 336 or 480 × 360 |
| `captions.vtt` | English spoken lines and relevant sound descriptions | WebVTT |
| `transcript.md` | Visual description, speech and provenance context | Plain Markdown |
| `CREDITS.txt` | Attribution pointers and current rights status | Plain text |
| `review-manifest.json` | Private copy of the checked-in manifest | JSON |

The private repository review also includes `docs/assets/nevermore-hero.webp`
and `experiences/nevermore/cover.webp` at **2400 × 840**. These branded README
images are the same Blender render. Their presence in the private repository
does not approve public distribution. Authentic character artwork is never
copied to `public/` by the art preparation commands.

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

The replacement cover, poster, social card and README art were rendered in
Blender 5.2.2 LTS using exact approved video frames: Azure Night raven frame 57,
Midnight Host frame 15 and Veiled Wraith Bride frame 39. The raven overlaps the
larger Host portrait; the Bride is a distant accent. Exterior alpha mattes,
proportional scaling and a gentle cool color response integrate the plates with
procedural midnight atmosphere, subtle particles and rendered type. Character
identity, geometry and poses are retained. These are editorial compositions,
not screenshots of simultaneous gameplay or a physical device.

All three input frames are **640 × 640** before cropping. The large README
composition enlarges those plates; it does not imply additional source detail.
Four private `.blend` files and the decoded plates are saved in
`.private/art-source/nevermore/`; exact plate crops, hashes, source frame
dimensions, script hash and render hashes are recorded in the manifest's
`editorial_art` section. System Baskerville and Source Sans Pro fonts are
rendered into the image and remain external font dependencies of the `.blend`.
Final visual approval remains with the owner.

The four gallery stills retain their original black-margin crops, proportional
resizing and WebP compression. The existing main video and teaser are unchanged;
the main video's original end card is retained. No soundtrack was added. Audio has only
15 ms/35 ms edge fades, resampling and delivery compression. PCM intermediates
avoid adding AAC priming gaps between cuts.

Recommended visible image caption: **“Editorial composition of approved Nevermore runtime artwork.”**
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

Render or revise the replacement art with Blender, then encode all derivatives
and refresh the exact output and bundle hashes:

```powershell
python scripts/art/nevermore_art.py --source E:/raven/Nevermore-main --blender E:/raven/nevermore-review/gate1b/blender-portable/blender-5.2.2-windows-x64/blender.exe
```

`--finalize-only` re-encodes existing Blender PNGs and refreshes delivery hashes
without rendering again. The art command leaves video/audio bytes untouched.
When the four private Blender renders exist, `prepare-media.py` preserves their
cover/poster/social derivatives and restores their provenance after preparation.
Its existing video edit continues to use the original end card. Without those
private renders, the legacy still composition is available for source-only
rebuilds; run the art command to restore the reviewed art direction.

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
The replacement Blender hero, cover and small poster were inspected after
rendering, including the lower silhouette transition and mobile text legibility.
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
