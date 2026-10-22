"""Produce the text-free GlassPlay hero plate and its delivery crops.

Source: owner-approved reference artwork (1672x941 PNG supplied 2026-10-22,
SHA-256 recorded in docs/assets/glassplay-hero-provenance.json). This script
only removes the baked-in wordmark/tagline/trademark sign and two faint
engraved strokes on the glasses' temple, then exports crops. It never redraws
characters, glasses or lighting.

  python scripts/art/glassplay_hero.py <source.png> <out-dir>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# Baked-in typography (wordmark, "TM", tagline) on the out-of-focus left wall.
TEXT_BOX = (100, 245, 668, 420)
# Two faint engraved strokes on the right temple, left of the hinge seam.
TEMPLE_MARKS = (1243, 455, 1273, 487)

DESKTOP_WIDTHS = (1672, 1200, 800)
# Mobile: a deliberate crop around the glasses and the small encounters.
MOBILE_BOX = (520, 0, 1672, 820)
MOBILE_WIDTHS = (1100, 840, 560)


def text_mask(image: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = TEXT_BOX
    value = image[y0:y1, x0:x1].max(axis=2).astype(np.float32)
    # White "Glass" and the blue-violet "Play" gradient are both much brighter
    # than the defocused wall around them: threshold local contrast, not hue.
    background = cv2.GaussianBlur(value, (0, 0), 18)
    letters = ((value - background > 28) & (value > 120)).astype(np.uint8) * 255
    letters = cv2.dilate(letters, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)), iterations=2)
    mask = np.zeros(image.shape[:2], np.uint8)
    mask[y0:y1, x0:x1] = letters
    return mask


def clean(image: np.ndarray) -> np.ndarray:
    mask = text_mask(image)
    x0, y0, x1, y1 = TEMPLE_MARKS
    mask[y0:y1, x0:x1] = 255
    result = cv2.inpaint(image, mask, 9, cv2.INPAINT_TELEA)
    # The wall behind the text is defocused: match that softness so the filled
    # area does not read as a smudge. Blend a blurred copy only inside the mask.
    soft = cv2.GaussianBlur(result, (0, 0), 7)
    alpha = cv2.GaussianBlur((mask > 0).astype(np.float32), (0, 0), 6)[..., None]
    alpha[y0 - 4:y1 + 4, x0 - 4:x1 + 4] *= 0.35  # keep the temple panel crisp
    return np.clip(result * (1 - alpha) + soft * alpha, 0, 255).astype(np.uint8)


def save_webp(image: np.ndarray, path: Path, width: int, quality: int) -> dict:
    height = round(image.shape[0] * width / image.shape[1])
    resized = image if width == image.shape[1] else cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".webp", resized, [cv2.IMWRITE_WEBP_QUALITY, quality])
    assert ok
    path.write_bytes(data.tobytes())
    return {"file": path.name, "width": width, "height": height, "bytes": len(data),
            "sha256": hashlib.sha256(data.tobytes()).hexdigest()}


def main() -> None:
    source, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    assert image.shape[:2] == (941, 1672), image.shape
    plate = clean(image)
    cv2.imwrite(str(out / "glassplay-hero-plate.png"), plate)
    x0, y0, x1, y1 = MOBILE_BOX
    mobile = plate[y0:y1, x0:x1]
    exports = [save_webp(plate, out / f"glassplay-hero-{w}.webp", w, 82) for w in DESKTOP_WIDTHS]
    exports += [save_webp(mobile, out / f"glassplay-hero-mobile-{w}.webp", w, 82) for w in MOBILE_WIDTHS]
    print(json.dumps({"source_sha256": hashlib.sha256(raw).hexdigest(), "text_box": TEXT_BOX,
                      "temple_marks": TEMPLE_MARKS, "mobile_box": MOBILE_BOX, "exports": exports}, indent=2))


if __name__ == "__main__":
    main()
