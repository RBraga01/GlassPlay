"""Season concept banners: remove brand-like temple marks, export delivery crops.

Sources: owner-supplied artwork (1672x941 PNG each, 2026-10-22), kept privately
in .private/art-source/seasons/<id>-reference.png. Only two faint engraved
strokes on each right temple are inpainted; nothing else is redrawn. Season
names and copy are rendered as HTML on the website.

  python scripts/art/glassplay_seasons.py <source-dir> <out-dir>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# Faint engraved strokes on the right temple, left of the hinge seam.
TEMPLE_MARKS = {
    "christmas": (1183, 518, 1206, 552),
    "easter": (1249, 513, 1276, 542),
    "st-patricks": (1199, 493, 1224, 520),
}
DESKTOP_WIDTHS = (1672, 1200, 800)
# Mobile: the glasses and the small encounters, without the left-hand scenery.
MOBILE_BOX = (560, 80, 1672, 860)
MOBILE_WIDTHS = (1000, 660)
# Mobile variants are lighter: the banners sit below the fold and must not slow the hero (LCP).
MOBILE_QUALITY = 72


def clean(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    mask = np.zeros(image.shape[:2], np.uint8)
    mask[y0:y1, x0:x1] = 255
    return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)


def save_webp(image: np.ndarray, path: Path, width: int, quality: int = 80) -> dict:
    height = round(image.shape[0] * width / image.shape[1])
    resized = image if width == image.shape[1] else cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".webp", resized, [cv2.IMWRITE_WEBP_QUALITY, quality])
    assert ok
    path.write_bytes(data.tobytes())
    return {"file": path.name, "width": width, "height": height, "bytes": len(data),
            "sha256": hashlib.sha256(data.tobytes()).hexdigest()}


def main() -> None:
    source_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for season, marks in TEMPLE_MARKS.items():
        raw = (source_dir / f"{season}-reference.png").read_bytes()
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        assert image.shape[:2] == (941, 1672), (season, image.shape)
        plate = clean(image, marks)
        cv2.imwrite(str(out / f"season-{season}-plate.png"), plate)
        x0, y0, x1, y1 = MOBILE_BOX
        exports = [save_webp(plate, out / f"season-{season}-{w}.webp", w) for w in DESKTOP_WIDTHS]
        exports += [save_webp(plate[y0:y1, x0:x1], out / f"season-{season}-mobile-{w}.webp", w, MOBILE_QUALITY) for w in MOBILE_WIDTHS]
        report[season] = {"source_sha256": hashlib.sha256(raw).hexdigest(), "temple_marks": marks,
                          "mobile_box": MOBILE_BOX, "exports": exports}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
