# Nevermore — curated source preview

This folder contains the **original production Python runtime**, two media index manifests and **selected pure-logic tests**. The code is copied verbatim from an identified source commit. Research history, rendered clips, raw media, offline speech model and third-party frameworks are **not included**.

**This is not an installable build.** Running `main.py` without the approved media and separately installed Raven Framework will fail. Do not interpret the presence of `manifest.json` as media being distributed.

## Run the logic-only checks

Requires Python 3.10+ and pytest. From this `app/` directory:

```bash
python -m pip install pytest
python -m pytest -q tests/test_audio.py tests/test_director.py tests/test_events.py tests/test_scheduler.py
```

These checks do **not** exercise playback, voice capture, the physical device or the complete production suite. When media, licenses and Raven deployment support are ready, installation instructions will be provided here.

## Provenance and missing dependencies

- [Export inventory](../export-manifest.json): source commit and original Git blob SHAs of every copied file.
- [Media and device gates](../ASSETS_PENDING.md): what is deliberately excluded.
- `assets/production/manifest.json` and `assets/trick_or_treat/manifest.json`: original indexes preserved for traceability; referenced MP4/WAV files are absent.
- `main.py`: still expects Raven Framework and its deployment configuration; no app credentials are embedded.
- Voice uses Vosk, but the model weights are **not** included here.
- No standalone source license has been granted in this export. Code and media licensing must be explicitly decided before a public release.

The source code remains organized under `nevermore/` so the original runtime paths are not artificially rewritten.
