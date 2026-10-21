"""Timed Qt scene surface; event choice and rendering live in separate modules."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget
from raven_framework.components.media_viewer import MediaViewer

from .events import EventSpec
from .production_media import load_catalogue


class HauntCanvas(QWidget):
    scene_finished = Signal(str)
    sound_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(640, 640)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._event: EventSpec | None = None
        self._elapsed_ms = 0
        self._started_at = 0.0
        self._sound_fired = False
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._dive_clip = Path(__file__).resolve().parent.parent / "assets/raven/video/raven_dive.mp4"
        if not self._dive_clip.is_file():
            raise FileNotFoundError(f"Missing Raven dive clip: {self._dive_clip} (fetch Git LFS assets)")
        self._dive_video = MediaViewer(
            media_path=str(self._dive_clip), parent=self, width=640, height=640,
            corner_radius=0, loop_video=False,
        )
        self._dive_video.move(0, 0)
        self._dive_video.pause_video()
        self._dive_video.hide()
        self.pack = load_catalogue()
        self._pack_video: MediaViewer | None = None
        self._pack_loaded_id: str | None = None
        self.hide()

    @property
    def active(self) -> bool:
        return self._timer.isActive()

    @property
    def current_id(self) -> str | None:
        return self._event.id if self._event else None

    def play(self, event: EventSpec) -> bool:
        if self.active:
            return False
        if event.id!="raven_dive" and event.id not in self.pack:
            raise ValueError(f"No production media for {event.id}")
        if event.id in self.pack and event.id != "raven_dive":
            self._prepare_pack(event.id)
        self._event = event
        self._elapsed_ms = 0
        self._started_at = time.monotonic()
        self._sound_fired = False
        self.show()
        self.raise_()
        if event.id == "raven_dive":
            self._rewind_dive()
            self._dive_video.show()
            self._dive_video.raise_()
            self._dive_video.play_video()
        elif event.id in self.pack:
            viewer = self._pack_video
            assert viewer is not None
            viewer.show()
            viewer.raise_()
            viewer.play_video()
        self._timer.start()
        if event.id in self.pack:
            # The complete authored WAV shares the video's scene time origin.
            # It replaces this scene's old fractional procedural sound cue.
            self._sound_fired = True
            self.sound_requested.emit(self.pack[event.id].cue)
        self.update()
        return True

    def stop(self) -> None:
        event = self._event
        self._timer.stop()
        self._dive_video.pause_video()
        self._dive_video.hide()
        if self._pack_video is not None:
            self._pack_video.pause_video()
            self._pack_video.hide()
        self._event = None
        self._elapsed_ms = 0
        self.hide()
        self.update()
        # Framework 1.0.6 releases its decoder at EOF for one-shot videos.
        # Reopen while hidden so a later valid trigger starts from a warm decoder.
        viewer = self._dive_video
        if (event is not None and event.id == "raven_dive"
                and viewer.cap is None and viewer._gst_pipeline is None):
            viewer.load_media(str(self._dive_clip))
            viewer.pause_video()
        if event is not None and event.id in self.pack and event.id != "raven_dive":
            self._prepare_pack(event.id)  # reopen EOF decoder while hidden

    def _tick(self) -> None:
        event = self._event
        if event is None:
            self._timer.stop()
            return
        # Keep the scene's real duration stable when the simulator drops ticks.
        # The nominal increment also lets deterministic tests drive the timer.
        wall_ms = (time.monotonic() - self._started_at) * 1000
        self._elapsed_ms = max(self._elapsed_ms + self._timer.interval(), wall_ms)
        progress = min(1.0, self._elapsed_ms / event.duration_ms)
        if event.sound and not self._sound_fired and progress >= event.sound_at:
            self._sound_fired = True
            self.sound_requested.emit(event.sound)
        self.update()
        if progress >= 1.0:
            event_id = event.id
            self.stop()
            self.scene_finished.emit(event_id)

    def paintEvent(self, event) -> None:  # noqa: N802
        # Every production event uses the authored one-shot media path.
        return

    def _rewind_dive(self) -> None:
        """Rewind the preloaded 1.0.6 MediaViewer without reopening its decoder."""
        viewer = self._dive_video
        if viewer.cap is not None:  # simulator software decode
            viewer.timer.setTimerType(Qt.TimerType.PreciseTimer)
            viewer.cap.set(viewer._cv2.CAP_PROP_POS_FRAMES, 0)
            viewer.next_frame()  # prime the first frame before showing the HUD
        elif viewer._gst_pipeline is not None:  # Raven hardware decode
            gst = viewer._gst_module
            viewer._gst_pipeline.seek_simple(gst.Format.TIME, gst.SeekFlags.FLUSH, 0)

    def _prepare_pack(self, event_id: str) -> None:
        """Reuse one non-looping player, with its first frame primed while hidden."""
        scene = self.pack[event_id]
        if not scene.video.is_file():
            raise FileNotFoundError(f"Missing Trick or Treat video: {scene.video}")
        if not scene.audio.is_file():
            raise FileNotFoundError(f"Missing Trick or Treat sound: {scene.audio}")
        viewer = self._pack_video
        if viewer is None:
            viewer = MediaViewer(
                media_path=str(scene.video), parent=self, width=640, height=640,
                corner_radius=0, loop_video=False,
            )
            viewer.move(0, 0)
            self._pack_video = viewer
        elif (self._pack_loaded_id != event_id
              or (viewer.cap is None and viewer._gst_pipeline is None)):
            viewer.load_media(str(scene.video))
        self._pack_loaded_id = event_id
        viewer.pause_video()
        viewer.hide()
        if viewer.cap is not None:
            # On Windows, the default coarse 41 ms timer can quantize to
            # ~46.9 ms, audibly separating a scene-length WAV from 24 fps video.
            # Keep the Framework decoder, but give only this pack accurate ticks.
            viewer.timer.setTimerType(Qt.TimerType.PreciseTimer)
            viewer.cap.set(viewer._cv2.CAP_PROP_POS_FRAMES, 0)
            viewer.next_frame()
        elif viewer._gst_pipeline is not None:
            gst = viewer._gst_module
            viewer._gst_pipeline.seek_simple(gst.Format.TIME, gst.SeekFlags.FLUSH, 0)
        else:
            raise RuntimeError(f"Could not decode Trick or Treat video: {scene.video}")
