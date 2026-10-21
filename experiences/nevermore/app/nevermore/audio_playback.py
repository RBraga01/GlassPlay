"""Interruptible WAV playback for the Windows Simulator and Raven Speaker.

Windows' winsound cannot combine SND_ASYNC with in-memory WAV playback. The
Framework's synchronous SND_MEMORY fallback runs on a worker, but its purge
call can wait for that worker's entire clip. Filename playback with SND_ASYNC
is cancellable, so we cache each WAV in a private temporary directory. On a
Raven device, the existing Framework Speaker remains the playback backend.
"""

from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Callable

from raven_framework.peripherals.speaker import Speaker


class InterruptibleAudioPlayer:
    def __init__(self, speaker: Speaker, *, windows_backend: Any = None,
                 cache_directory: Path | None = None,
                 now: Callable[[], float] = time.monotonic) -> None:
        self._speaker = speaker
        self._now = now
        if windows_backend is None and sys.platform == "win32" and speaker.sensorlib_client is None:
            import winsound
            windows_backend = winsound
        self._windows = windows_backend
        self._temporary = (tempfile.TemporaryDirectory(prefix="nevermore-wav-")
                           if self._windows is not None and cache_directory is None else None)
        self._directory = (Path(self._temporary.name) if self._temporary else cache_directory)
        if self._directory is not None:
            self._directory.mkdir(parents=True, exist_ok=True)
        self._cached: dict[str, Path] = {}
        self._active = False
        self._deadline = 0.0
        self._closed = False

    @property
    def is_active(self) -> bool:
        """Whether the expected WAV duration is still in progress."""
        return self._active and self._now() < self._deadline

    def play_audio(self, wav_bytes: bytes) -> None:
        if self._closed:
            raise RuntimeError("Audio player is closed")
        if not isinstance(wav_bytes, bytes) or not wav_bytes:
            raise ValueError("Expected non-empty WAV bytes")
        with wave.open(io.BytesIO(wav_bytes), "rb") as source:
            duration = source.getnframes() / source.getframerate()
        self.stop_audio()
        if self._windows is not None:
            digest = hashlib.sha256(wav_bytes).hexdigest()
            path = self._cached.get(digest)
            if path is None:
                assert self._directory is not None
                path = self._directory / f"{digest}.wav"
                path.write_bytes(wav_bytes)
                self._cached[digest] = path
            flags = (self._windows.SND_FILENAME | self._windows.SND_ASYNC
                     | self._windows.SND_NODEFAULT)
            self._windows.PlaySound(str(path), flags)
        else:
            self._speaker.play_audio(wav_bytes)
        self._active = True
        self._deadline = self._now() + duration

    def stop_audio(self) -> None:
        if not self._active:
            return
        if self._windows is not None:
            self._windows.PlaySound(None, self._windows.SND_PURGE)
        else:
            self._speaker.stop_audio()
        self._active = False
        self._deadline = 0.0

    def close(self) -> None:
        if self._closed:
            return
        self.stop_audio()
        if self._temporary is not None:
            self._temporary.cleanup()
        self._closed = True
