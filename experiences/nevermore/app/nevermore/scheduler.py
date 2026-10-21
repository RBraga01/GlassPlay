"""Small deterministic-friendly scheduler helpers for Nevermore."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class HauntTiming:
    minimum_seconds: float = 20.0
    maximum_seconds: float = 60.0

    def validate(self) -> None:
        if self.minimum_seconds <= 0:
            raise ValueError("minimum_seconds must be > 0")
        if self.maximum_seconds < self.minimum_seconds:
            raise ValueError("maximum_seconds must be >= minimum_seconds")


class HauntSchedule:
    def __init__(
        self,
        timing: HauntTiming | None = None,
        seed: int | None = None,
    ) -> None:
        self.timing = timing or HauntTiming()
        self.timing.validate()
        self._rng = random.Random(seed)
        self.demo_mode = False

    def set_demo_mode(self, enabled: bool) -> None:
        self.demo_mode = enabled

    def next_delay_ms(self, *, recovery: bool = False, session_seconds: float = 0) -> int:
        timing = HauntTiming(5.0, 9.0) if self.demo_mode else self.timing
        if not self.demo_mode and recovery:
            timing = HauntTiming(max(60., timing.minimum_seconds),
                                max(90., timing.maximum_seconds))
        seconds = self._rng.uniform(timing.minimum_seconds, timing.maximum_seconds)
        if not self.demo_mode and session_seconds >= 20 * 60:
            seconds *= 1.5  # taper; remain armed, without a forced ending
        return max(1, int(round(seconds * 1000.0)))
