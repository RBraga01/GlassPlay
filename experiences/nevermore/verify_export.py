"""Verify the curated source preview against its immutable upstream Git blob IDs.
This does not validate media, licenses, device behavior, or the complete application.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
doc = json.loads((ROOT / "export-manifest.json").read_text(encoding="utf-8"))
assert doc["status"] == "source_preview_only" and not doc["media_included"]
assert not doc["runnable"] and not doc["framework_included"] and not doc["voice_model_included"]

expected = {"app/" + "README.md"}
for row in doc["files"]:
    relative = row["path"]
    assert relative.startswith("app/") and ".." not in Path(relative).parts
    path = ROOT / relative
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    sha = hashlib.sha1(header + payload).hexdigest()
    assert sha == row["source_git_blob_sha"], f"Original source changed: {relative}"
    assert len(payload) == row["bytes"], f"Size differs: {relative}"
    expected.add(relative)

actual = {path.relative_to(ROOT).as_posix()
          for path in (ROOT / "app").rglob("*") if path.is_file()
          and "__pycache__" not in path.parts}
assert expected == actual, f"Unexpected or missing files: {sorted(expected ^ actual)}"
print(f"OK: {len(doc['files'])} unmodified source files; no extras in app/")
