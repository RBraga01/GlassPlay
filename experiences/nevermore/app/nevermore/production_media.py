"""Production media for the Raven family and ambient presences."""
from pathlib import Path
import json
import math
from .events import EVENTS
from .trick_or_treat_media import load_pack, PackScene

ASSETS=Path(__file__).resolve().parents[1]/"assets"

def load_catalogue() -> dict[str,PackScene]:
    scenes=load_pack()
    manifest=json.loads((ASSETS/"production/manifest.json").read_text(encoding="utf-8"))
    if (manifest["schema_version"],manifest["fps"],manifest["resolution"])!=(1,24,[640,640]):
        raise ValueError("Unsupported production media")
    for id_,entry in manifest["scenes"].items():
        if id_ in scenes:raise ValueError("Attempt to replace locked Midnight Host media")
        if entry["duration_ms"]!=EVENTS[id_].duration_ms:raise ValueError(f"Duration mismatch: {id_}")
        if entry["frame_count"]!=math.ceil(EVENTS[id_].duration_ms*24/1000):raise ValueError(id_)
        paths=[(ASSETS/entry[k]).resolve() for k in ("video","audio")]
        if any(not p.is_relative_to(ASSETS.resolve()) for p in paths):raise ValueError(id_)
        if paths[0].suffix!=".mp4" or paths[1].suffix!=".wav":raise ValueError(id_)
        scenes[id_]=PackScene(id_,*paths,entry["frame_count"])
    if set(scenes)!=set(EVENTS):raise ValueError("Incomplete production catalogue")
    return scenes
