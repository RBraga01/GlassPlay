"""Procedural audio for Nevermore.

No binary assets are required for the demo. The functions in this module
return small mono WAV files as bytes, ready for Raven Framework's Speaker.
"""

from __future__ import annotations

import io
import math
import random
import wave
from typing import Iterable

SAMPLE_RATE = 22_050


def _wav_from_samples(
    samples: Iterable[float],
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    pcm = bytearray()
    for sample in samples:
        value = max(-1.0, min(1.0, float(sample)))
        integer = int(value * 32767.0)
        pcm.extend(integer.to_bytes(2, byteorder="little", signed=True))

    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(pcm))
    return output.getvalue()


def raven_caw(seed: int = 13) -> bytes:
    """Synthesize a short, rough raven-like caw."""
    rng = random.Random(seed)
    duration = 1.05
    total = int(SAMPLE_RATE * duration)
    samples: list[float] = []

    for i in range(total):
        t = i / SAMPLE_RATE
        pulse = 0.0
        for start, length, strength in (
            (0.04, 0.24, 1.0),
            (0.33, 0.20, 0.72),
            (0.62, 0.27, 0.55),
        ):
            local = (t - start) / length
            if 0.0 <= local <= 1.0:
                envelope = math.sin(math.pi * local) ** 1.4
                base = 390.0 - 155.0 * local
                rasp = math.sin(2.0 * math.pi * base * t)
                rasp += 0.42 * math.sin(
                    2.0 * math.pi * (base * 1.93) * t + 0.9
                )
                rasp += 0.23 * math.sin(
                    2.0 * math.pi * (base * 2.74) * t + 1.7
                )
                noise = rng.uniform(-1.0, 1.0)
                pulse += strength * envelope * (
                    0.58 * rasp + 0.42 * noise
                )
        samples.append(0.48 * pulse)

    return _wav_from_samples(samples)


def wing_rush(seed: int = 29) -> bytes:
    """Synthesize a brief wing rush."""
    rng = random.Random(seed)
    duration = 0.72
    total = int(SAMPLE_RATE * duration)
    samples: list[float] = []
    state = 0.0

    for i in range(total):
        t = i / SAMPLE_RATE
        x = t / duration
        envelope = math.sin(math.pi * x) ** 1.8
        white = rng.uniform(-1.0, 1.0)
        state = 0.86 * state + 0.14 * white
        flutter = 0.55 + 0.45 * math.sin(
            2.0 * math.pi * (8.0 + 5.0 * x) * t
        )
        samples.append(0.50 * envelope * flutter * state)

    return _wav_from_samples(samples)


def heartbeat() -> bytes:
    """Synthesize four low heartbeat-like thumps."""
    duration = 1.45
    total = int(SAMPLE_RATE * duration)
    samples: list[float] = []
    beats = (0.16, 0.39, 0.90, 1.12)

    for i in range(total):
        t = i / SAMPLE_RATE
        value = 0.0
        for n, start in enumerate(beats):
            local = t - start
            if 0.0 <= local <= 0.18:
                decay = math.exp(-20.0 * local)
                frequency = 76.0 if n % 2 == 0 else 62.0
                value += (
                    0.60
                    * decay
                    * math.sin(2.0 * math.pi * frequency * local)
                )
        samples.append(value)

    return _wav_from_samples(samples)


def soft_effect(kind: str, seed: int = 41) -> bytes:
    """Small restrained cues; output can later be replaced by authored WAVs."""
    if kind not in {"wind", "ghost", "impact", "jingle", "chime", "whisper"}:
        raise ValueError(kind)
    rng = random.Random(seed)
    durations = {"wind": 1.1, "ghost": 0.9, "impact": 0.42,
                 "jingle": 0.75, "chime": 0.45, "whisper": 0.85}
    duration = durations[kind]
    total = int(SAMPLE_RATE * duration)
    samples: list[float] = []
    filtered_noise = 0.0
    phase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        x = t / duration
        envelope = math.sin(math.pi * x) ** 1.5
        filtered_noise = 0.94 * filtered_noise + 0.06 * rng.uniform(-1, 1)
        if kind in {"wind", "whisper"}:
            value = filtered_noise * (0.42 if kind == "wind" else 0.25)
        elif kind == "ghost":
            phase += 2 * math.pi * (260 + 110 * math.sin(2 * math.pi * 2 * t)) / SAMPLE_RATE
            value = 0.18 * math.sin(phase) + 0.08 * filtered_noise
        elif kind == "impact":
            value = 0.36 * math.exp(-10 * x) * filtered_noise
        else:
            notes = (523, 659, 784) if kind == "jingle" else (740, 990)
            note = notes[min(len(notes) - 1, int(x * len(notes)))]
            phase += 2 * math.pi * note / SAMPLE_RATE
            value = 0.18 * math.sin(phase)
        samples.append(envelope * value)
    return _wav_from_samples(samples)


def build_sound_bank() -> dict[str, bytes]:
    return {
        "raven": raven_caw(),
        "wing": wing_rush(),
        "heartbeat": heartbeat(),
        **{kind: soft_effect(kind) for kind in
           ("wind", "ghost", "impact", "jingle", "chime", "whisper")},
    }
