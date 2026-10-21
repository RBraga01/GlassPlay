"""Authored Trick or Treat media; selection and timing remain in events.py."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from .events import EVENTS, TRICK_IDS, TREAT_IDS


PACK_IDS = frozenset(("trick_or_treat", *TRICK_IDS, *TREAT_IDS))
PACK_ROOT = Path(__file__).resolve().parents[1] / "assets/trick_or_treat"


@dataclass(frozen=True)
class PackScene:
    event_id: str
    video: Path
    audio: Path
    frame_count: int

    @property
    def cue(self) -> str:
        return f"pack:{self.event_id}"


def load_pack(root: Path = PACK_ROOT) -> dict[str, PackScene]:
    """Read the small production manifest without overriding event mechanics."""
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (manifest["schema_version"] != 1 or manifest["fps"] != 24
            or manifest["resolution"] != [640, 640]):
        raise ValueError("Unsupported Trick or Treat media format")
    if set(manifest["scenes"]) != PACK_IDS:
        raise ValueError("Trick or Treat manifest must contain exactly the eight scenes")
    result = {}
    for event_id, entry in manifest["scenes"].items():
        duration = EVENTS[event_id].duration_ms
        if (entry["duration_ms"] != duration
                or entry["frame_count"] != math.ceil(duration * 24 / 1000)):
            raise ValueError(f"Media timing disagrees with the catalogue: {event_id}")
        paths = []
        for kind, extension in (("video", ".mp4"), ("audio", ".wav")):
            path = (root / entry[kind]).resolve()
            if not path.is_relative_to(root) or path.suffix.lower() != extension:
                raise ValueError(f"Invalid {kind} path for {event_id}")
            paths.append(path)
        result[event_id] = PackScene(event_id, *paths, entry["frame_count"])
    return result
