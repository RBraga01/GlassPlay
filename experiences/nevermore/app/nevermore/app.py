"""Nevermore's small foreground shell for Raven Prism."""

from __future__ import annotations

import os
import sys
import time

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from raven_framework.components.button import Button
from raven_framework.components.text_box import TextBox
from raven_framework.core.raven_app import RavenApp
from raven_framework.peripherals.speaker import Speaker

from .audio import build_sound_bank
from .audio_playback import InterruptibleAudioPlayer
from .choices import HostChoice
from .director import EventDirector
from .director import DIRECTIONS
from .discoveries import Discoveries, TITLES
from .voice import ForegroundVoice
from .events import EVENTS, MANUAL_IDS, EventSelector, EventSpec
from .scheduler import HauntSchedule
from .scenes import HauntCanvas
from .triggers import TriggerRouter
from .trick_or_treat_media import PACK_IDS


def _button(label: str, width: int, size: int = 19) -> Button:
    return Button(center_text=label, width=width, height=56,
                  text_size=size, text_color="#E9ECF2",
                  background_color="#000000", outline_color="#87909F",
                  outline_width=1, corner_radius=14)


class NevermoreApp(RavenApp):
    """Foreground HUD. Triggers and catalogue have no dependency on this UI."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._armed = False
        self._demo = "--demo" in sys.argv or os.environ.get("NEVERMORE_DEMO") == "1"
        self._discoveries = Discoveries()
        self._journal_open = False
        self._voice = ForegroundVoice(self)
        self._voice.word.connect(self._spoken_raven)
        self._selector = EventSelector()
        self._director = EventDirector(self._selector)
        self._director.discovered = set(self._discoveries.found)
        self._schedule = HauntSchedule()
        self._manual_index = 0
        self._prompt_pending = False
        self._intro_pending = False
        self._speaker = Speaker()
        self._audio_player = InterruptibleAudioPlayer(self._speaker)
        qt_app = QApplication.instance()
        if qt_app is not None:
            qt_app.aboutToQuit.connect(self._audio_player.close)
            qt_app.aboutToQuit.connect(self._voice.close)
        self._sounds: dict[str, bytes] | None = None  # legacy cues; built only if requested
        self._router = TriggerRouter(self._selector, self._start_event, self._director.summon)
        self._voice_resume = QTimer(self)
        self._voice_resume.setSingleShot(True)
        self._voice_resume.timeout.connect(self._resume_voice)
        self._discovery_timer = QTimer(self)
        self._discovery_timer.setSingleShot(True)
        self._discovery_timer.timeout.connect(lambda: self._discovery_note.hide())

        self._haunt_timer = QTimer(self)
        self._haunt_timer.setSingleShot(True)
        self._haunt_timer.timeout.connect(self._random_event)
        self._opening_timer = QTimer(self)
        self._opening_timer.setSingleShot(True)
        self._opening_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._opening_timer.timeout.connect(self._open_session)
        self._choice_timer = QTimer(self)
        self._choice_timer.setSingleShot(True)
        self._choice_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._choice_timer.timeout.connect(self._show_choices)

        self._title = TextBox(text="NEVERMORE", font_type="title",
                              width=600, alignment="center")
        self._status = TextBox(text="HALLOWEEN MODE  ·  OFF",
                               font_type="small", width=600, alignment="center")
        self._hint = TextBox(text='Silence is part of the haunting.\nSay “Raven” while armed.',
                             font_type="small", width=600, alignment="center")
        self.app.add(self._title, x=20, y=78)
        self.app.add(self._status, x=20, y=147)
        self.app.add(self._hint, x=20, y=208)

        self._canvas = HauntCanvas(self.app)
        self._pack_sounds: dict[str, bytes] = {}
        self.app.add(self._canvas, x=0, y=0)
        self._canvas.sound_requested.connect(self._play_sound)
        self._canvas.scene_finished.connect(self._scene_finished)

        self._arm = _button("ARM HALLOWEEN MODE", 340, 20)
        self._fast = _button("FAST: OFF", 165, 18)
        self._raven = _button("RAVEN", 165, 19)
        self._prompt = _button("TRICK / TREAT", 165, 17)
        self._next = _button("NEXT EVENT", 165, 18)
        self.app.add(self._arm, x=150, y=345)
        self.app.add(self._fast, x=145, y=427)
        self.app.add(self._raven, x=330, y=427)
        self.app.add(self._prompt, x=145, y=501)
        self.app.add(self._next, x=330, y=501)
        self._idle_widgets = [self._title, self._status, self._hint,
                              self._arm, self._fast, self._raven,
                              self._prompt, self._next]
        self._demo_widgets = [self._fast,self._raven,self._prompt,self._next]
        self._journal = _button("DISCOVERIES", 240, 17)
        self.app.add(self._journal,x=200,y=445 if not self._demo else 575)
        self._idle_widgets.append(self._journal)
        self._journal.on_clicked(self._toggle_journal)
        self._discovery_note = TextBox(text="",font_type="small",width=440,alignment="center")
        self._discovery_note.setStyleSheet(
            "color:#F3EADB;font-family:'Georgia';font-size:24px;font-weight:600;background:transparent;")
        self.app.add(self._discovery_note,x=100,y=515)
        self._discovery_note.hide()

        self._trick_choice = HostChoice("TRICK")
        self._treat_choice = HostChoice("TREAT")
        self._disarm_now = Button(center_text="DISARM", width=126, height=44,
                                  text_size=15, text_color="#89909B",
                                  background_color="#000000", outline_width=0,
                                  use_fill_dwell=False, use_gradient_border=False)
        self.app.add(self._trick_choice, x=120, y=415)
        self.app.add(self._treat_choice, x=340, y=415)
        self.app.add(self._disarm_now, x=484, y=562)
        for widget in (self._trick_choice, self._treat_choice, self._disarm_now):
            widget.hide()

        self._arm.on_clicked(self.toggle_armed)
        self._fast.on_clicked(self.toggle_fast_mode)
        self._raven.on_clicked(lambda: self.trigger_event("raven_sweep","demo preview"))
        self._prompt.on_clicked(lambda: self.trigger_event("trick_or_treat", "button"))
        self._next.on_clicked(self.next_event)
        self._trick_choice.on_clicked(lambda: self.choose_trick_or_treat("TRICK"))
        self._treat_choice.on_clicked(lambda: self.choose_trick_or_treat("TREAT"))
        self._disarm_now.on_clicked(self.disarm)

        shortcuts=[("H", self.toggle_armed),("Escape",self.disarm)]
        if self._demo:
            shortcuts += [("R", lambda: self.trigger_raven("shortcut") if self._armed
                            else self.trigger_event("raven_sweep","demo preview")),
                              ("N", self.next_event),
                              ("T", lambda: self.trigger_event("trick_or_treat", "shortcut")),
                              ("D", self.toggle_fast_mode)]
        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(callback)

        review_event = next(
            (arg.partition("=")[2] for arg in sys.argv[1:]
             if arg.startswith("--review-event=")),
            os.environ.get("NEVERMORE_REVIEW_EVENT"),
        )
        if review_event in EVENTS:
            def _start_review() -> None:
                started = self.trigger_event(review_event, "review launch")
                print(f"Nevermore review event {review_event}: {started}", flush=True)
            QTimer.singleShot(5000, _start_review)
        self._set_idle_visible(True)

    @property
    def armed(self) -> bool:
        return self._armed

    @property
    def active_event_id(self) -> str | None:
        return self._canvas.current_id

    def _set_idle_visible(self, visible: bool) -> None:
        for widget in self._idle_widgets:
            widget.setVisible(visible and (self._demo or widget not in self._demo_widgets))

    def _toggle_journal(self) -> None:
        if self._armed:return
        self._journal_open=not self._journal_open
        self._journal.set_text("RETURN" if self._journal_open else "DISCOVERIES")
        self._title.set_text("DISCOVERIES" if self._journal_open else "NEVERMORE")
        found=[TITLES[k] for k in self._discoveries.found]
        self._hint.set_text(("\n".join(found) or "The night has yet to reveal its secrets.")
                            if self._journal_open else 'Silence is part of the haunting.\nSay “Raven” while armed.')
        self._arm.setVisible(not self._journal_open)
        self._status.setVisible(not self._journal_open)

    def _spoken_raven(self, text: str) -> None:
        if self._router.keyword_detected(text):
            self._discoveries.unlock("raven_summon")

    def _resume_voice(self) -> None:
        if self._armed and not self._canvas.active and not self._intro_pending:
            self._voice.suspend(False)

    def _show_discovery(self, ids: list[str]) -> None:
        if not ids or not self._armed:return
        self._discovery_note.set_text("◇  "+TITLES[ids[0]])
        self._discovery_note.show()
        self._discovery_timer.start(2400)

    def toggle_armed(self) -> None:
        if self._armed:
            self.disarm()
            return
        if self._journal_open:self._toggle_journal()
        self._armed = True
        self._voice.set_armed(True)
        self._director.begin(time.monotonic())
        self._intro_pending = True
        self._arm.set_text("DISARM")
        self._status.set_text("HALLOWEEN MODE  ·  ARMED")
        self._set_idle_visible(False)
        self._disarm_now.show()
        self._disarm_now.raise_()
        if not self._canvas.active:
            self._opening_timer.start(2000)

    def _open_session(self) -> None:
        if self._armed and self._intro_pending and not self._canvas.active:
            self._start_event(EVENTS["trick_or_treat"], "onboarding")

    def _show_choices(self) -> None:
        if self._prompt_pending and self.active_event_id == "trick_or_treat":
            for widget in (self._trick_choice, self._treat_choice):
                widget.show()
                widget.raise_()

    def disarm(self) -> None:
        self._armed = False
        self._voice_resume.stop()
        self._voice.set_armed(False)
        self._voice.suspend(True)
        self._discovery_timer.stop()
        self._discovery_note.hide()
        self._haunt_timer.stop()
        self._opening_timer.stop()
        self._choice_timer.stop()
        self._intro_pending = False
        self._director.end()
        self._prompt_pending = False
        self._arm.set_text("ARM HALLOWEEN MODE")
        self._status.set_text("HALLOWEEN MODE  ·  OFF")
        if self._canvas.active:
            self._canvas.stop()
        self._audio_player.stop_audio()
        self._trick_choice.hide()
        self._treat_choice.hide()
        self._disarm_now.hide()
        self._set_idle_visible(True)

    def toggle_fast_mode(self) -> None:
        self._schedule.set_demo_mode(not self._schedule.demo_mode)
        self._fast.set_text("FAST: ON" if self._schedule.demo_mode else "FAST: OFF")
        if self._armed and not self._canvas.active:
            self._schedule_next()

    def _schedule_next(self) -> None:
        if self._armed and not self._canvas.active:
            if self._intro_pending:
                if not self._opening_timer.isActive():
                    self._opening_timer.start(2000)
                return
            self._haunt_timer.start(self._schedule.next_delay_ms(
                recovery=self._director.recovery,
                session_seconds=self._director.elapsed(time.monotonic()),
            ))

    def _random_event(self) -> None:
        if not self._armed or self._intro_pending or self._canvas.active:
            return
        event = self._director.choose(time.monotonic())
        if event is None or not self._start_event(event, "random"):
            self._schedule_next()

    def _start_event(self, event: EventSpec, source: str) -> bool:
        if source in {"random", "onboarding", "keyword"} and not self._armed:
            return False
        if self._canvas.active:
            return False
        if source=="keyword" and self._intro_pending:
            return False
        self._voice_resume.stop()
        self._voice.suspend(True)
        self._discovery_note.hide()
        self._discovery_timer.stop()
        if not self._canvas.play(event):
            return False
        self._haunt_timer.stop()
        self._opening_timer.stop()
        self._intro_pending = False
        self._choice_timer.stop()
        self._selector.record(event.id, time.monotonic())
        self._prompt_pending = event.requires_choice
        self._set_idle_visible(False)
        self._trick_choice.hide()
        self._treat_choice.hide()
        if event.requires_choice:
            # Approved spoken invitation begins at 1.20 s. The Host first
            # establishes presence, then the existing choices become available.
            self._choice_timer.start(1200)
        self._disarm_now.setVisible(self._armed)
        if self._armed:
            self._disarm_now.raise_()
        return True

    def _scene_finished(self, event_id: str) -> None:
        self._director.complete(event_id, time.monotonic())
        self._audio_player.stop_audio()
        if event_id == "trick_or_treat":
            self.choose_trick_or_treat(None)
            return
        self._trick_choice.hide()
        self._treat_choice.hide()
        self._disarm_now.setVisible(self._armed)
        self._set_idle_visible(not self._armed)
        self._schedule_next()
        if self._armed:
            direction=DIRECTIONS.get(event_id)
            rare=direction is not None and direction.rarity.value in ("rare","very rare")
            self._show_discovery(self._discoveries.encounter(event_id,rare=rare))
            self._director.discovered = set(self._discoveries.found)
            self._voice_resume.start(450)  # drain speaker/room tail before listening

    def closeEvent(self, event):
        self.disarm()
        self._voice.close()
        if hasattr(self._audio_player,"close"):self._audio_player.close()
        super().closeEvent(event)

    def choose_trick_or_treat(self, choice: str | None) -> bool:
        if not self._prompt_pending:
            return False
        if choice not in (None, "TRICK", "TREAT"):
            raise ValueError(choice)
        self._choice_timer.stop()
        if self._canvas.current_id == "trick_or_treat":
            self._director.complete("trick_or_treat", time.monotonic())
            self._canvas.stop()
        self._audio_player.stop_audio()
        self._prompt_pending = False
        self._trick_choice.hide()
        self._treat_choice.hide()
        result = self._selector.choose_outcome(
            choice, exclude=self._director.strong_blocked(time.monotonic()))
        self._director.choice_made(choice, result.id)
        return self._start_event(result, f"choice:{choice or 'auto'}")

    def trigger_event(self, event_id: str, source: str = "manual") -> bool:
        return self._router.trigger_event(event_id, source)

    def trigger_raven(self, source: str = "manual") -> bool:
        return self._router.trigger_raven(source)

    def next_event(self) -> bool:
        event_id = MANUAL_IDS[self._manual_index]
        if self.trigger_event(event_id, "manual cycle"):
            self._manual_index = (self._manual_index + 1) % len(MANUAL_IDS)
            return True
        return False

    def _play_sound(self, sound: str) -> None:
        if sound.startswith("pack:"):
            event_id = sound.removeprefix("pack:")
            if event_id not in self._canvas.pack:
                return
            if sound not in self._pack_sounds:
                self._pack_sounds[sound] = self._canvas.pack[event_id].audio.read_bytes()
            self._audio_player.play_audio(self._pack_sounds[sound])
            return
        if self._sounds is None:
            # Every production event plays authored pack audio. Keep the
            # procedural bank as a lazy fallback instead of a startup cost.
            self._sounds = build_sound_bank()
        wav = self._sounds.get(sound)
        if wav:
            self._audio_player.play_audio(wav)
