# Install Nevermore Halloween 1.1.0 (Windows / Raven Simulator)

**Download:** [`Nevermore-Halloween-1.1.0.zip`](https://github.com/RBraga01/GlassPlay/releases/download/nevermore-v1.1.0/Nevermore-Halloween-1.1.0.zip) (65,190,942 bytes) from the
[`nevermore-v1.1.0` release](https://github.com/RBraga01/GlassPlay/releases/tag/nevermore-v1.1.0), not GitHub's automatic source archives.
SHA-256 `f8b154d0cab073102b3604a01e297a6e4fe2134670f47739d5b3f937e6272937`.

## Requirements

- Windows host with Python 3.10 or newer and audio output.
- **Raven Framework 1.0.6** (`791afd896cc646636ef906f5bf06c09c8fbb430a`), installed
  separately with `pip install -e`. It is **not included** or relicensed: obtain and use
  it under Raven Resonance's applicable terms (see the ZIP's `RAVEN_FRAMEWORK.md`).
  No SDK, app IDs, keys or credentials are included.
- A microphone only for the optional spoken "Raven".

## Install and launch

```powershell
(Get-FileHash -LiteralPath ./Nevermore-Halloween-1.1.0.zip -Algorithm SHA256).Hash.ToLower()
Expand-Archive ./Nevermore-Halloween-1.1.0.zip -DestinationPath .
cd Nevermore-Halloween
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -e <path-to-your-authorized-raven-framework-1.0.6>
python -m pip install -r requirements.txt
python main.py
```

On macOS/Linux shells, `sha256sum -c Nevermore-Halloween-1.1.0.sha256` checks the ZIP.
`python main.py` opens the Threshold: walk through SOFT or HAUNTED to arm it; DISARM
or Escape stops everything. After extracting, `python tools/verify_release.py` checks
every file hash, the 20 SOFT events and every HAUNTED clip.

## Boundaries

Validated on a Windows host with Raven Simulator (Python 3.10 and 3.12, clean installs).
Physical Raven Prism is **DEVICE-UNVERIFIED**; this is not an official Prism
installation. Code MIT; Nevermore-specific artwork and media All Rights Reserved;
third-party materials keep their own licenses.

---

# Archived: Nevermore 1.0.0-rc.2 Windows / Simulator candidate

*Historical record of the private rc.2 candidate; superseded by 1.1.0.*

This guide applies to the privately prepared **1.0.0-rc.2 application package**
(private draft `v1.0.0-rc.2` in the Nevermore repository). Public download
remains disabled. `experiences/nevermore/app` is a source preview without
runtime assets and cannot be installed as the full experience.

## Requirements

- Windows host with Python 3.10 or newer and audio output.
- Raven Framework, obtained separately. Nevermore does not include or relicense
  it; the package's `RAVEN_FRAMEWORK.md` is the single place describing how to
  obtain and deploy it. Verified compatibility: 1.0.6 at
  `791afd896cc646636ef906f5bf06c09c8fbb430a`.
- A microphone for the optional spoken “Raven” interaction. On-screen controls
  remain available without it.

The candidate includes the small English Vosk model and its Apache-2.0 notice;
no model download, Git LFS or Blender installation is needed to run it.

## Install and launch

Check the ZIP before extraction:

```powershell
(Get-FileHash -LiteralPath ./Nevermore-1.0.0-rc.2.zip -Algorithm SHA256).Hash.ToLower()
Get-Content -LiteralPath ./Nevermore-1.0.0-rc.2.sha256
```

Expected: `21f946888e59623f5b19539c76042379ceda9cfd1cdc01e14d25a00502f95edc`.
Extract into a fresh directory and open PowerShell inside `Nevermore`:

```powershell
python -m venv .venv
# Install Raven Framework into .venv as described in RAVEN_FRAMEWORK.md
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe main.py
```

The experience opens disarmed. Select **ARM**, answer **Trick or Treat**, and
say **Raven** when armed and idle. **DISARM** or **Escape** stops everything.
`python main.py --demo` enables the faster review mode;
`python main.py --reset-discoveries` resets the local discovery journal.

## Verify

```powershell
.venv/Scripts/python.exe -m pip install pytest
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe tools/verify_release.py
```

The package verifier checks all 98 payload hashes and decodes the 20 events.
From GlassPlay (Python 3.11+), the release verifier checks the ZIP's exact file
set, checksum, manifest hash and upstream Git objects without extracting it:

```powershell
python scripts/verify-release.py
python scripts/verify-release.py --source-repo <nevermore-checkout> --archive <path>/Nevermore-1.0.0-rc.2.zip --artifact private_draft
python -m unittest discover -s tests -p test_verify_release.py
```

Without private inputs, CI verifies committed source and metadata only and
reports upstream/archive checks as `NOT_RUN`.

## Rebuild

From a clean Nevermore checkout at `b4980cfc7c6c93838892d966c61284bfd0740214`
with LFS payloads available, write to a new directory outside the checkout:

```powershell
python tools/package_public.py <new-folder-outside-the-checkout>/Nevermore-1.0.0-rc.2
```

ZIP timestamps and checkout line endings mean a rebuilt archive's checksum can
differ; compare payload hashes and provenance, and never copy an earlier
checksum onto a rebuilt file.

## Limits

Physical Prism provisioning, display, speaker, microphone, performance and
thermals are **DEVICE-UNVERIFIED**. Raven's official third-party deployment
process is pending on Raven's side. No standalone executable is supplied.
