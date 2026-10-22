# Nevermore — curated source preview

**Synchronized to the Nevermore production release candidate `1.0.0-rc.2` (`b4980cf`).**

This directory holds **23 selected upstream files**: production Python, two original media catalogue manifests, and five test files (four logic suites plus the discovery isolation fixture). The new `assets/production/manifest.json` tracks updated approved video hashes for Shadow and Glitch. Since rc.1 only `nevermore/app.py` changed: the unused procedural sound bank is built lazily.

> **Not a standalone runnable build.** The separately installed Raven Framework, the approved MP4/WAV media and the Vosk model are absent. The full package is still a **private draft in Nevermore**.

## Logic-only checks

Requires Python 3.10+ and pytest. From this `app/` directory:

```bash
python -m pip install pytest
python -m pytest -q tests/test_audio.py tests/test_director.py tests/test_events.py tests/test_scheduler.py
```

These checks don't test audio/video playback, voice capture, the SDK or hardware.

## For maintainers

- [Verbatim export inventory](../export-manifest.json) — upstream commit and per-file Git object IDs.
- [Rights, assets and hardware gates](../ASSETS_PENDING.md).
- Do not add intermediate renders, archived research, private blobs or credentials.
- No public source license is implied by this preview.
