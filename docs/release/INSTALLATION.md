# Nevermore Windows / Simulator candidate

This guide applies to the internally prepared **1.0.0-rc.1 application package**.
Public download remains disabled. `experiences/nevermore/app` is a source preview
without runtime assets and cannot be installed as the full experience.

## Requirements

- Windows host with Python 3.10 or newer, audio output and an authorized Raven
  Framework 1.0.6 installation at commit
  `791afd896cc646636ef906f5bf06c09c8fbb430a`.
- A microphone and Windows microphone permission for the optional spoken
  “Raven” interaction. On-screen controls remain available without it.
- Python packages required by the separately installed SDK, plus
  `vosk==0.3.45` from the candidate's `requirements.txt`.

The SDK is proprietary and external. Obtain applicable permission from Raven
Resonance before installing or distributing an application that depends on it.
The candidate includes the small English Vosk model and its Apache-2.0 notice;
no model download, Git LFS or Blender installation is needed to run it.
Installation may need internet access for Python dependencies; gameplay uses the
local model and media after installation.

## Internal installation and launch

Check the supplied ZIP before extraction using its matching `.sha256` file:

```powershell
(Get-FileHash -LiteralPath ./Nevermore-1.0.0-rc.1.zip -Algorithm SHA256).Hash.ToLower()
Get-Content -LiteralPath ./Nevermore-1.0.0-rc.1.sha256
```

For the refreshed candidate, the expected hash is
`d4fecf4cbafcc5c3c0060c4dcc7066434152bd5527466141937f76a17bec5179`.
Extract it into a fresh directory and open PowerShell inside its `Nevermore`
folder. Replace the SDK path with the authorized local installation:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e C:/path/to/authorized/raven-framework
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe main.py
```

The experience opens disarmed. Select **ARM** to start, interact with **Trick or
Treat**, and say **Raven** when armed and idle to request a raven encounter.
Use **DISARM** or **Escape** to stop. Voice listening pauses during playback.
`python main.py --demo` enables the faster demonstration/review mode.

Discoveries are stored in `%LOCALAPPDATA%/Nevermore/discoveries.json` on Windows.
`NEVERMORE_DATA_DIR` overrides that directory for tests.
`python main.py --reset-discoveries` resets the discovery journal.
Normal gameplay does not save microphone recordings or transcripts.

## Verify an extracted candidate

```powershell
.venv/Scripts/python.exe -m pip install pytest
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe tools/verify_release.py
```

The package verifier checks all 95 payload hashes and decodes the 20 video/audio
events. The GlassPlay verifier additionally checks the ZIP's exact file set,
checksum, manifest hash, source revision and unsafe/duplicate entries without
extracting it. Run this from GlassPlay using Python 3.11 or newer:

```powershell
python scripts/verify-release.py
python scripts/verify-release.py --source-repo E:/raven/Nevermore-main --archive E:/raven/releases/glassplay-ready/Nevermore-1.0.0-rc.1.zip
python scripts/verify-release.py --source-repo E:/raven/Nevermore-main --archive E:/raven/releases/public-ready/Nevermore-1.0.0-rc.1.zip --artifact private_draft
python -m unittest discover -s tests -p test_verify_release.py
```

Without private inputs, CI verifies only committed source and release metadata.
It explicitly reports upstream object/archive checks as `NOT_RUN`. Media decode
requires the extracted package's existing `tools/verify_release.py` and its
dependencies; the metadata check never substitutes for it.

## Rebuild with the existing packager

Use a clean, authorized Nevermore checkout at
`81df295f6825189bfba05288aca76595b4c59437`, with the runtime/model LFS payloads
available and its dependencies installed. Choose an output directory that does
not exist and is outside the source checkout:

```powershell
git rev-parse HEAD
git status --short
python tools/package_public.py E:/raven/releases/new-candidate/Nevermore-1.0.0-rc.1
```

The existing allowlist selects runtime Python, 34 unique runtime media files,
the offline voice model, application tests, public documentation and notices.
It excludes private history, experimental archives, original Meshy models,
authoring scenes, credentials, journals and the SDK. The packager writes a
`RELEASE_MANIFEST.json`, ZIP and adjacent SHA-256 file and never publishes them.

Verify the new package with its included verifier and application tests. Record
its new checksum before making any metadata change. ZIP timestamps and Windows
line endings mean the whole-archive checksum is not guaranteed identical across
rebuilds. Compare payload hashes and source provenance; do not copy an earlier
ZIP checksum onto a rebuilt file. Generated manifests and credits must be
reviewed whenever source/licensing metadata changes.

## Installation limits

The current verification used the existing pinned SDK environment. A fresh
Windows machine and physical Prism provisioning/display/speaker/microphone/
performance have not been tested. **DEVICE-UNVERIFIED** remains the device status.
No macOS/Linux support certification or standalone executable is supplied.
