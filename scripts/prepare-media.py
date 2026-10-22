#!/usr/bin/env python3
"""Prepare Nevermore's private review media from a hash-pinned source allowlist.

Requires Python 3.11+, Pillow, OpenCV and imageio-ffmpeg (or --ffmpeg).
This command intentionally has no public-output option.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".private/media/nevermore"
BUNDLE = ROOT / ".private/nevermore-web-media.zip"
EDITORIAL_SOURCE = ROOT / ".private/art-source/nevermore"
SOURCE_REVISION = "81df295f6825189bfba05288aca76595b4c59437"
FPS = 24
SIZE = (960, 540)
SOURCES = {
    "room_product": ("docs/release/validation/product/simulator-room-with-audio.mp4", "5a48a74b6d592d01da9c25b30c68f4a1c3d05e080e13b78cc4a3a51694c6f3ac"),
    "room_catalogue": ("docs/release/validation/catalogue/simulator-room-with-audio.mp4", "ba4fd3da6496166579d7ae15c5e5c904a226bf1d158982350d0f7eb4b5c54129"),
    "product_report": ("docs/release/validation/product/capture-report.json", "0009f92d742dfb1b1a6c1405bbc606f52d3cecc25111de155e65469c4ab8cfe6"),
    "catalogue_report": ("docs/release/validation/catalogue/capture-report.json", "86f685f76696dfb3ae4418732ac7e24005e18fa7d9665b6026cd8f15212bfc54"),
    "host": ("assets/trick_or_treat/video/trick_or_treat.mp4", "0c31aa1dfed0a9edaa790c2c09f709fe0291b57542c18e2a440ccac340f6a698"),
    "host_audio": ("assets/trick_or_treat/audio/trick_or_treat.wav", "719a8339ca2f6ad5a1ac6a6bb5dec8d3dc52a3ba0342806256250d0684730c16"),
    "mimic": ("assets/trick_or_treat/video/trick_raven_box.mp4", "9417207cf86f59fb745bc18b79fc8b96f42e7de4c1f37d8b36b37e31cb59dc76"),
    "mimic_audio": ("assets/trick_or_treat/audio/trick_raven_box.wav", "501060faf30a21e8e333d58f57cac37ccb6674c22980f7ec6016936c8bd1c4f7"),
    "bride": ("assets/trick_or_treat/video/treat_ghost.mp4", "d5fcf29e232d59dad35c23d2757aaa5d38e49cd1c28a711b505ef5f55e6dc357"),
    "bride_audio": ("assets/trick_or_treat/audio/treat_ghost.wav", "9921c0256bc65d640ad157f65d4cdce8241a869ca9a3ccfc19e68ea2df695097"),
    "raven": ("assets/raven/video/raven_dive.mp4", "fc5b704d9b0bcdac15cd3a052aa766c13d918fdc830b43c5f660c97c8b788503"),
    "raven_audio": ("assets/production/audio/raven_dive.wav", "8ca9996c4e8c742e55c53a9cbd80baae758b03c135f6e18028cb12f14e5b1c62"),
}
STILLS = {
    "host": (0.625, "The Midnight Host extends a hand, wearing a hood and a chain of skulls."),
    "raven": (2.375, "The blue-black raven dives forward with its wings spread."),
    "bride": (1.625, "The Veiled Wraith Bride raises her approved open-hand gesture."),
    "mimic": (1.5, "The Ocular Maw Chest opens its toothed lid beneath a large central eye."),
}
# Every in/out point is a frame boundary; no animation is slowed or regenerated.
PROMO = [
    ("raven", 24, 66, "THE RAVEN", "runtime_render"),
    ("host", 0, 78, "THE MIDNIGHT HOST", "runtime_render"),
    ("mimic", 0, 70, "A MOST UNUSUAL TREAT", "runtime_render"),
    ("bride", 0, 78, "THE VEILED WRAITH BRIDE", "runtime_render"),
    ("room_product", 408, 559, "TRICK OR TREAT", "simulator_room"),
    ("room_product", 1084, 1171, "AN UNEXPECTED GUEST", "simulator_room"),
    ("room_catalogue", 343, 423, "THE RAVEN RETURNS", "simulator_room"),
]
TEASER = [
    ("raven", 24, 66, "", "runtime_render"),
    ("host", 12, 54, "", "runtime_render"),
    ("mimic", 18, 60, "", "runtime_render"),
    ("bride", 12, 60, "", "runtime_render"),
]
OUTPUT_FILES = sorted([
    *(name+suffix+".webp" for name in ["cover", "host", "raven", "bride", "mimic", "poster", "glassplay-social"] for suffix in ["", "-small"]),
    "promo.mp4", "teaser.mp4", "captions.vtt", "transcript.md", "CREDITS.txt",
])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])


def font(size: int, serif: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (["C:/Windows/Fonts/georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"] if serif else
                  ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError("Install Arial/Georgia or DejaVu Sans/Serif before preparing media.")


def frame(path: Path, seconds: float) -> Image.Image:
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, round(seconds * FPS))
    ok, bgr = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Cannot decode frame at {seconds}: {path.name}")
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def subject(im: Image.Image) -> Image.Image:
    """Crop black margins. Source pixels and color stay unaltered."""
    a = np.asarray(im)
    ys, xs = np.where(a.max(axis=2) > 12)
    if not len(xs):
        raise RuntimeError("Selected frame is empty")
    return im.crop((max(0, xs.min()-8), max(0, ys.min()-8), min(im.width, xs.max()+9), min(im.height, ys.max()+9)))


def place(canvas: Image.Image, im: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    im = im.copy()
    im.thumbnail((w, h), Image.Resampling.LANCZOS)
    # Upscale if necessary, keeping the character's proportions.
    ratio = min(w/im.width, h/im.height)
    im = im.resize((round(im.width*ratio), round(im.height*ratio)), Image.Resampling.LANCZOS)
    layer = Image.new("RGB", canvas.size)
    layer.paste(im, (x+(w-im.width)//2, y+(h-im.height)//2))
    canvas.paste(ImageChops.lighter(canvas, layer))


def save_image(name: str, im: Image.Image, small_width: int = 640) -> None:
    im.save(OUTPUT/f"{name}.webp", quality=88, method=6)
    small = im.resize((small_width, round(im.height*small_width/im.width)), Image.Resampling.LANCZOS)
    small.save(OUTPUT/f"{name}-small.webp", quality=84, method=6)


def editorial_art():
    """Load the Blender finalizer only when its private source renders exist."""
    if not all((EDITORIAL_SOURCE/f"{name}.png").exists() for name in ("hero", "cover", "poster", "glassplay-social")):
        return None
    spec = importlib.util.spec_from_file_location("nevermore_art", ROOT/"scripts/art/nevermore_art.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_images(paths: dict[str, Path]) -> Image.Image:
    subjects = {name: subject(frame(paths[name], timestamp)) for name, (timestamp, _) in STILLS.items()}
    for name, im in subjects.items():
        canvas = Image.new("RGB", (960, 720))
        place(canvas, im, (100, 45, 760, 630))
        save_image(name, canvas, 480)
    cover = Image.new("RGB", (1200, 630))
    place(cover, subjects["raven"], (310, 20, 400, 320))
    place(cover, subjects["host"], (650, 35, 360, 540))
    place(cover, subjects["bride"], (955, 170, 235, 405))
    place(cover, subjects["mimic"], (445, 335, 260, 260))
    save_image("cover", cover)
    poster = cover.copy()
    d = ImageDraw.Draw(poster)
    d.text((58, 296), "NEVERMORE", fill="#eee8dc", font=font(52, True))
    d.text((60, 372), "An invitation after dark.", fill="#a8a0b1", font=font(23))
    d.text((60, 555), "PRODUCTION ANIMATION + SIMULATOR ROOM", fill="#99909e", font=font(15))
    save_image("poster", poster)
    social = cover.copy()
    d = ImageDraw.Draw(social)
    d.text((58, 58), "GlassPlay", fill="#eee8dc", font=font(30))
    d.text((58, 296), "NEVERMORE", fill="#eee8dc", font=font(52, True))
    d.text((60, 372), "A little magic, right before your eyes.", fill="#b6adbe", font=font(22))
    d.text((60, 553), "INTERACTIVE EXPERIENCES FOR AR SMART GLASSES", fill="#99909e", font=font(15))
    save_image("glassplay-social", social)
    art = editorial_art()
    if art:
        art.encode_outputs()
    # Existing video edit keeps its original editorial end card and exact frames.
    return poster


def compose_video_frame(im: Image.Image, title: str, kind: str, teaser: bool) -> Image.Image:
    canvas = Image.new("RGB", SIZE)
    im.thumbnail(SIZE, Image.Resampling.LANCZOS)
    canvas.paste(im, ((SIZE[0]-im.width)//2, (SIZE[1]-im.height)//2))
    d = ImageDraw.Draw(canvas)
    # Matte labels are a deliberate editorial frame, not simulated headset UI.
    d.rectangle((0, 0, SIZE[0], 40), fill="#08080b")
    d.rectangle((0, SIZE[1]-38, SIZE[0], SIZE[1]), fill="#08080b")
    d.text((22, 11), "NEVERMORE", fill="#eee8dc", font=font(18, True))
    label = "PRODUCTION ANIMATION" if kind == "runtime_render" else "RAVEN SIMULATOR / ROOM"
    d.text((22, SIZE[1]-27), label, fill="#bcb2c5", font=font(13))
    note = "MUTED PREVIEW" if teaser else "WINDOWS PREVIEW"
    d.text((SIZE[0]-158, SIZE[1]-27), note, fill="#bcb2c5", font=font(13))
    if title and not teaser:
        w = d.textbbox((0, 0), title, font=font(13))[2]
        d.text((SIZE[0]-22-w, 13), title, fill="#bcb2c5", font=font(13))
    return canvas


def encode_video(ffmpeg: str, frames, destination: Path, size=SIZE, crf=23) -> None:
    args = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination)]
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for im in frames:
            p.stdin.write(im.tobytes())
        p.stdin.close()
        stderr = p.stderr.read().decode(errors="replace")
        if p.wait():
            raise RuntimeError(stderr)
    finally:
        if p.poll() is None:
            p.kill()


def segment_frames(path: Path, start: int, end: int, title: str, kind: str, teaser: bool):
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    try:
        for _ in range(start, end):
            ok, bgr = cap.read()
            if not ok:
                raise RuntimeError(f"Premature video end: {path.name}")
            im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            yield compose_video_frame(im, title, kind, teaser)
    finally:
        cap.release()


def prepare_video(paths: dict[str, Path], ffmpeg: str, poster: Image.Image, work: Path, teaser=False) -> list[dict]:
    decisions, parts, elapsed = [], [], 0.0
    segments = TEASER if teaser else PROMO
    for index, (key, start, end, title, kind) in enumerate(segments):
        duration = (end-start)/FPS
        video = work/f"{'teaser' if teaser else 'promo'}-{index}-silent.mp4"
        encode_video(ffmpeg, segment_frames(paths[key], start, end, title, kind, teaser), video, crf=25 if teaser else 22)
        part = video
        if not teaser:
            part = work/f"promo-{index}.mkv"
            audio = paths[key] if kind == "simulator_room" else paths[key+"_audio"]
            run([ffmpeg, "-y", "-loglevel", "error", "-i", str(video), "-ss", f"{start/FPS:.9f}", "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-t", f"{duration:.9f}", "-c:v", "copy", "-af", f"afade=t=in:d=0.015,afade=t=out:st={duration-0.035:.9f}:d=0.035", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(part)])
        parts.append(part)
        decisions.append({"source": key, "source_in_frame": start, "source_out_frame_exclusive": end, "output_start_s": round(elapsed, 6), "duration_s": round(duration, 6), "type": kind, "title": title})
        elapsed += duration
    if not teaser:
        endcard = ImageOps.pad(poster, SIZE, method=Image.Resampling.LANCZOS, color="black")
        end_silent = work/"end-silent.mp4"
        encode_video(ffmpeg, (endcard for _ in range(48)), end_silent)
        end_part = work/"end.mkv"
        run([ffmpeg, "-y", "-loglevel", "error", "-i", str(end_silent), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "2", "-c:v", "copy", "-c:a", "pcm_s16le", str(end_part)])
        parts.append(end_part)
        decisions.append({"source": "poster.webp", "output_start_s": round(elapsed, 6), "duration_s": 2, "type": "editorial_endcard", "title": "An invitation after dark."})
    listing = work/("teaser.txt" if teaser else "promo.txt")
    listing.write_text("\n".join("file '"+p.as_posix().replace("'", "'\\''")+"'" for p in parts), encoding="utf-8")
    destination = OUTPUT/("teaser.mp4" if teaser else "promo.mp4")
    # PCM intermediates avoid introducing AAC priming gaps between each segment.
    audio_args = ["-an"] if teaser else ["-c:a", "aac", "-b:a", "128k", "-af", "aresample=async=1:first_pts=0"]
    video_filter = "scale=640:360" if teaser else "null"
    total = sum(item["duration_s"] for item in decisions)
    run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-vf", video_filter, "-c:v", "libx264", "-preset", "medium", "-crf", "25" if teaser else "22", "-r", str(FPS), "-pix_fmt", "yuv420p", *audio_args, "-t", f"{total:.6f}", "-movflags", "+faststart", str(destination)])
    return decisions


def timestamp(seconds: float) -> str:
    milliseconds = round(seconds*1000)
    return f"{milliseconds//3600000:02}:{milliseconds//60000%60:02}:{milliseconds//1000%60:02}.{milliseconds%1000:03}"


def prepare_text(decisions: list[dict]) -> None:
    captions = [
        (0, 1.75, "[Wingbeats and a rushing raven]"),
        (1.75, 2.9, "[The Midnight Host appears]"),
        (2.9, 4.7, "MIDNIGHT HOST: Trick or Treat?"),
        (5, 7.916667, "[Wood creaks; the chest snaps open]"),
        (7.916667, 11.166667, "[A bell and soft cloth; the Bride raises her hand]"),
        (11.166667, 12.4, "[Raven Simulator Room demonstration]"),
        (12.4, 14.1, "MIDNIGHT HOST: Trick or Treat?"),
        (14.1, 17.458333, "[The toothed chest opens in the simulated room]"),
        (17.458333, 21.083333, "[The Bride appears with a bell and drifting cloth]"),
        (21.083333, 24.416667, "[The raven dives through the simulated room]"),
        (24.416667, 26.416667, "NEVERMORE. An invitation after dark."),
    ]
    (OUTPUT/"captions.vtt").write_text("WEBVTT\n\n"+"\n\n".join(f"{timestamp(a)} --> {timestamp(b)}\n{text}" for a,b,text in captions)+"\n", encoding="utf-8")
    transcript = """# Nevermore promotional preview — text alternative

The first eleven seconds show approved production animation on black. A raven
dives forward; the Midnight Host extends his hand and asks, “Trick or Treat?”;
a chest with one large eye opens its toothed mouth; the Veiled Wraith Bride
raises her hand. Wingbeats, wooden creaks, a bell and soft cloth accompany the
animations. These are the runtime artwork and scene audio, not hardware footage.

The second half shows edited excerpts of the current Windows Raven Simulator
Room capture. The Host asks “Trick or Treat?” again. The toothed chest, Bride and
raven appear over a simulated kitchen. These are arranged review triggers, not a
continuous play session. The last raven excerpt does not show or audibly contain
the voice input.

The final card reads “Nevermore. An invitation after dark.” Physical Raven Prism
has not been verified. No real glasses recording is presented. The 7.25-second
teaser contains the four production animations in the same order and no audio.

Captions identify the two spoken lines and describe important scene sounds.
Timing follows the source cue reports; a final owner listening review is pending.
"""
    (OUTPUT/"transcript.md").write_text(transcript, encoding="utf-8")
    (OUTPUT/"CREDITS.txt").write_text("Nevermore — RBraga01\nNevermore's character artwork was developed using 3D assets created with Meshy and animated for this project. Only finished rendered visuals are presented; original source models are not distributed.\nFictional Host voice: locally generated Qwen3-TTS performance, as recorded in the source voice manifest.\nSound effects: see assets/production/provenance.json and third-party notices in the source release.\nRaven Simulator Room: Raven Framework 1.0.6. No physical-device recording.\nPublic artwork/media licensing, framework permissions and publication approval remain pending.\n", encoding="utf-8")


def inspect_video(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    info = {"width": round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), "height": round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), "fps": cap.get(cv2.CAP_PROP_FPS), "frames": round(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
    cap.release()
    info["duration_s"] = round(info["frames"]/info["fps"], 6)
    return info


def build_bundle() -> dict:
    """Flat allowlisted delivery ZIP; fixed metadata makes identical inputs repeatable."""
    with zipfile.ZipFile(BUNDLE, "w", compression=zipfile.ZIP_STORED) as archive:
        for filename in OUTPUT_FILES:
            entry = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (OUTPUT/filename).read_bytes())
    return {"path": ".private/nevermore-web-media.zip", "sha256": sha(BUNDLE), "bytes": BUNDLE.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Local approved Nevermore checkout")
    parser.add_argument("--ffmpeg", help="ffmpeg executable; otherwise use imageio-ffmpeg")
    parser.add_argument("--images-only", action="store_true", help="Render stills without rewriting the complete media manifest")
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source/"assets/production/manifest.json").exists():
        parser.error("Source is not a Nevermore production checkout")
    ffmpeg = args.ffmpeg
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    paths = {key: source/rel for key,(rel,_) in SOURCES.items()}
    for key,(rel,expected) in SOURCES.items():
        if sha(paths[key]) != expected:
            raise RuntimeError(f"Approved source hash mismatch: {rel}. Review a changed release explicitly.")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ignored = subprocess.run(["git", "check-ignore", "--quiet", str(OUTPUT)], cwd=ROOT)
    if ignored.returncode:
        raise RuntimeError("Add .private/ to .gitignore before preparing private assets.")
    poster = prepare_images(paths)
    if args.images_only:
        print(f"Private stills prepared in {OUTPUT}")
        return
    with tempfile.TemporaryDirectory(prefix="media-build-", dir=OUTPUT) as temp:
        decisions = prepare_video(paths, ffmpeg, poster, Path(temp))
        teaser_decisions = prepare_video(paths, ffmpeg, poster, Path(temp), teaser=True)
    prepare_text(decisions)
    outputs = []
    for filename in OUTPUT_FILES:
        path = OUTPUT/filename
        info = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha(path)}
        if path.suffix == ".webp":
            with Image.open(path) as im:
                info.update(width=im.width, height=im.height)
        elif path.suffix == ".mp4":
            info.update(inspect_video(path))
        outputs.append(info)
    bundle = build_bundle()
    manifest = {
        "schema_version": 1,
        "status": "PRIVATE_REVIEW_ONLY",
        "public_distribution_approved": False,
        "source_repository": "https://github.com/RBraga01/Nevermore",
        "source_revision": SOURCE_REVISION,
        "release": "v1.0.0-rc.1",
        "device_validation": "Windows Host / Raven Simulator validated; physical Prism DEVICE-UNVERIFIED",
        "output_directory": ".private/media/nevermore",
        "sources": [{"id": k, "path": v[0], "sha256": v[1]} for k,v in SOURCES.items()],
        "stills": [{"file": key+".webp", "source": key, "timestamp_s": value[0], "frame_index": round(value[0]*FPS), "alt": value[1], "type": "runtime_render"} for key,value in STILLS.items()],
        "cover": {"file": "cover.webp", "type": "composite_of_runtime_render_stills", "sources": list(STILLS), "description": "Approved raven, Host, Bride and chest frames composed on black. An editorial montage, not a single gameplay scene."},
        "promo_edit": decisions,
        "teaser_edit": teaser_decisions,
        "audio": {"promo": "Original runtime WAVs and original synchronized Simulator Room audio. Tiny 15/35 ms edge fades only; no new score, normalization, pitch shift or time stretch.", "teaser": "No audio stream", "captions": "captions.vtt", "text_alternative": "transcript.md", "listening_review": "Pending owner review; no human listening approval is claimed."},
        "editorial_rules": ["Only the listed current production files were read.", "No archive or docs/prefinal imagery.", "Black-margin crop, proportional resize and WebP compression only for stills; no synthetic art, relighting or changes to approved poses.", "Runtime and Simulator clips have distinct burned-in labels.", "Montage clips remain at native 24 fps and original speed.", "No claim of a continuous session, microphone demo or physical-glasses capture.", "Responsive stills and muted teaser support lightweight mobile presentation."],
        "rights": {"mesh_model_status": "USER-ATTESTED-MESHY-PAID-ACCOUNT", "independent_account_inspection": False, "public_media_license": "Owner decision pending", "raven_framework_distribution": "Permission decision pending", "publication": "Owner approval required"},
        "attribution_reference_repository": "RBraga01/Nevermore",
        "attribution_references": ["assets/production/provenance.json", "assets/trick_or_treat/audio/voice/voice_manifest.json", "docs/release/public/THIRD_PARTY_NOTICES.md"],
        "outputs": outputs,
        "assets": [{"path": item["file"], "sha256": item["sha256"], "bytes": item["bytes"]} for item in outputs],
        "bundle": bundle,
    }
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2)+"\n"
    (OUTPUT/"review-manifest.json").write_text(encoded, encoding="utf-8")
    (ROOT/"docs/media").mkdir(parents=True, exist_ok=True)
    (ROOT/"docs/media/manifest.json").write_text(encoded, encoding="utf-8")
    art = editorial_art()
    if art:
        provenance = json.loads((EDITORIAL_SOURCE/"provenance.json").read_text(encoding="utf-8"))
        art.finalize_manifest(art.load_preparer(), provenance)
    print(json.dumps({"directory": str(OUTPUT), "files": len(outputs), "bytes": sum(item["bytes"] for item in outputs)}, indent=2))


if __name__ == "__main__":
    main()
