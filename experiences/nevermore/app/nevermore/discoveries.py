"""Small local encounter journal. No account, score, or microphone recordings."""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone

TITLES = {
    "first_trick":"MIDNIGHT GUEST", "first_treat":"A SWEET OFFERING",
    "raven_summon":"NEVERMORE", "raven_dive":"UNDER THE WING",
    "trick_behind_you":"DON'T LOOK BACK", "treat_ghost":"THE BRIDE",
    "trick_raven_box":"A HUNGRY GIFT", "first_rare":"BEYOND THE VEIL",
    "raven_duet":"TWO OMENS",
}

def data_directory() -> Path:
    override=os.environ.get("NEVERMORE_DATA_DIR")
    if override:return Path(override)
    base=Path(os.environ.get("LOCALAPPDATA", Path.home()/".local/share"))
    return base/"Nevermore"

class Discoveries:
    def __init__(self, path: Path | None = None):
        self.path=path or data_directory()/"discoveries.json"
        self.found: dict[str,str]={}
        self.error: str | None=None
        try:
            value=json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value,dict) or value.get("schema") != 1:
                raise ValueError("Unknown journal version")
            if not isinstance(value.get("found"),dict):raise ValueError("Invalid encounter journal")
            self.found={k:v for k,v in value["found"].items() if k in TITLES and isinstance(v,str)}
        except FileNotFoundError:pass
        except (OSError,ValueError,KeyError,TypeError) as exc:
            self.error=str(exc)  # keep the original for recovery; never crash ARM

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({"schema":1,"found":self.found},indent=2)+"\n",encoding="utf-8")
        os.replace(temp,self.path)
        self.error=None

    def unlock(self, *ids: str) -> list[str]:
        new=[x for x in dict.fromkeys(ids) if x in TITLES and x not in self.found]
        if not new:return []
        for id_ in new:self.found[id_]=datetime.now(timezone.utc).isoformat()
        try:self.save()
        except OSError as exc:self.error=str(exc)
        return new

    def encounter(self, event_id: str, *, rare: bool=False) -> list[str]:
        # The ambient ghost uses the same approved Bride performance, so her
        # first encounter counts even outside the interactive Treat result.
        ids=["treat_ghost" if event_id=="ghost" else event_id]
        if event_id.startswith("trick_") and event_id!="trick_or_treat":ids.append("first_trick")
        if event_id.startswith("treat_"):ids.append("first_treat")
        if rare:ids.append("first_rare")
        return self.unlock(*ids)

    def reset(self):
        self.found.clear()
        self.save()
