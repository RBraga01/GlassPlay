"""Local foreground word recognition using Qt capture and an offline Vosk worker.

No background service, cloud requests, or retained microphone recordings.
Only complete, standalone 'raven' utterances are accepted. Playback suspends
capture; generation tokens invalidate every result queued before DISARM.
"""
from __future__ import annotations
import json
import queue
import threading
from pathlib import Path
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices

MODEL = Path(__file__).resolve().parents[1]/"assets/voice/vosk-model-small-en-us-0.15"

def accepted_result(result: dict) -> bool:
    words=result.get("result",[])
    return (result.get("text","").strip().casefold()=="raven"
            and len(words)==1 and words[0].get("word")=="raven"
            and words[0].get("conf",0)>=.75
            and .15 <= words[0].get("end",0)-words[0].get("start",0) <= 1.8)

class OfflineRecognizer:
    """Synchronous worker primitive, also used by real-WAV integration tests."""
    def __init__(self, sample_rate=16000):
        from vosk import Model, KaldiRecognizer, SetLogLevel
        SetLogLevel(-1)
        self.model=Model(str(MODEL))
        self.decoder=KaldiRecognizer(self.model,sample_rate)
        self.decoder.SetWords(True)

    def reset(self):self.decoder.Reset()
    def feed(self, pcm: bytes) -> dict | None:
        if self.decoder.AcceptWaveform(pcm):
            return json.loads(self.decoder.Result())
        return None
    def finish(self):return json.loads(self.decoder.FinalResult())

class ForegroundVoice(QObject):
    word = Signal(str)
    state_changed = Signal(str)
    _recognized = Signal(int, object)
    _worker_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled=False
        self.suspended=True
        self.generation=0
        self.status="off"
        self.source=None
        self.device=None
        self._queue=queue.Queue(maxsize=40)
        self._thread=None
        self._closed=False
        self._timer=QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._read)
        self._recognized.connect(self._deliver)
        self._worker_error.connect(self._failed)

    def _state(self,text):
        self.status=text
        self.state_changed.emit(text)

    def _worker(self):
        try:
            decoder=OfflineRecognizer()
            if self._closed:return
            generation=-1
            while True:
                item=self._queue.get()
                if item is None:return
                token,pcm=item
                if generation!=token:
                    decoder.reset();generation=token
                result=decoder.feed(pcm)
                if result is not None and not self._closed:self._recognized.emit(token,result)
        except Exception as exc:
            if not self._closed:self._worker_error.emit(str(exc))

    def _failed(self,error):
        self._halt()
        self._state("Microphone unavailable")
        self.last_error=error

    def _deliver(self,token,result):
        if self.enabled and not self.suspended and token==self.generation and accepted_result(result):
            self.word.emit("raven")

    def set_armed(self,armed: bool):
        self.enabled=armed
        if not armed:
            self._halt();self._state("off")
        elif not self.suspended:self._start()

    def suspend(self,suspended: bool):
        self.suspended=suspended
        if suspended:self._halt()
        elif self.enabled:self._start()

    def _start(self):
        if self._closed or self.device is not None:return
        if self._thread is None:
            self._thread=threading.Thread(target=self._worker,name="Nevermore offline voice",daemon=True)
            self._thread.start()
        device=QMediaDevices.defaultAudioInput()
        if device.isNull():
            self._state("Microphone unavailable");return
        fmt=QAudioFormat();fmt.setSampleRate(16000);fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        if self.source is None:self.source=QAudioSource(device,fmt,self)
        self.device=self.source.start()
        if self.device is None:self._state("Microphone unavailable");return
        self._timer.start();self._state("listening")

    def _read(self):
        if self.device is None:return
        pcm=bytes(self.device.readAll())
        self.submit_pcm(pcm)

    def submit_pcm(self,pcm: bytes):
        """16 kHz mono PCM ingress shared by microphone and recorded-input QA.

        The normal app only calls this from the microphone reader. A review
        harness may supply recorded speech, never a pre-decoded keyword.
        """
        if not self.enabled or self.suspended or self._closed:return
        if pcm:
            try:self._queue.put_nowait((self.generation,pcm))
            except queue.Full:
                # Discard the entire recognition context after an overloaded
                # worker, rather than joining unrelated words across a gap.
                self.generation+=1
                self._drain()

    def _drain(self):
        while True:
            try:self._queue.get_nowait()
            except queue.Empty:return

    def _halt(self):
        self.generation+=1
        self._timer.stop()
        if self.source is not None:self.source.stop()
        self.device=None
        self._drain()

    def close(self):
        self.enabled=False;self._closed=True;self._halt()
        if self._thread is not None:self._queue.put_nowait(None)
