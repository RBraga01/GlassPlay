"""Session rhythm, independent of Qt, rendering and input routing.

The selector still owns Trick/Treat's 65/35 draw. This director only decides
what may happen spontaneously, and how the session recovers afterwards.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from enum import Enum, IntEnum

from .events import EVENTS, RARITY_WEIGHT, EventSelector, EventSpec, Rarity


class Family(str, Enum):
    PRESENCE = "presence"
    CREATURE = "creature"
    INTERACTIVE = "interactive"


class Intensity(IntEnum):
    QUIET = 0
    PRESENCE = 1
    INTERACTION = 2
    PEAK = 3


@dataclass(frozen=True)
class Direction:
    family: Family
    rarity: Rarity
    minimum_level: Intensity
    cooldown_s: float
    strong: bool = False
    earliest_s: float = 0


P, C, I = Family.PRESENCE, Family.CREATURE, Family.INTERACTIVE
Q, L1, L2, L3 = Intensity

# Use the approved pack for spontaneous Bride, Spider and Pumpkin encounters.
# Their old Qt prototype IDs remain available through the manual review route.
DIRECTIONS = {
    "eyes": Direction(P, Rarity.COMMON, Q, 70),
    "shadow": Direction(P, Rarity.COMMON, Q, 70),
    "nevermore": Direction(P, Rarity.COMMON, L1, 110),
    "raven_shadow": Direction(P, Rarity.COMMON, L1, 100),
    "glitch": Direction(P, Rarity.RARE, L2, 180),
    "raven_sweep": Direction(C, Rarity.COMMON, L1, 100),
    "raven_perch": Direction(C, Rarity.UNCOMMON, L2, 180),
    "raven_dive": Direction(C, Rarity.RARE, L3, 300, True, 300),
    "raven_duet": Direction(C, Rarity.VERY_RARE, L3, 600, True, 600),
    "trick_or_treat": Direction(I, Rarity.UNCOMMON, L2, 240),
    "trick_raven_box": Direction(C, Rarity.RARE, L3, 240, True),
    "trick_behind_you": Direction(C, Rarity.RARE, L3, 240, True),
    "trick_spider": Direction(C, Rarity.UNCOMMON, L2, 150),
    "treat_candy": Direction(C, Rarity.COMMON, L2, 180),
    "treat_ghost": Direction(C, Rarity.UNCOMMON, L2, 180),
    "treat_pumpkin": Direction(C, Rarity.COMMON, L1, 120),
    "treat_badge": Direction(C, Rarity.UNCOMMON, L2, 240),
}

# Minimum time between the end of one strong event and the start of another.
STRONG_RECOVERY_S = 180

# Family weights are applied before event weights. A large number of creature
# assets must not crowd out quiet signals or make the Host a frequent prompt.
FAMILY_WEIGHTS = {
    Q: {P: 1, C: 0, I: 0},
    L1: {P: 4, C: 2, I: 0},
    L2: {P: 3, C: 3, I: .45},
    L3: {P: 2.5, C: 3, I: .55},
}


class EventDirector:
    """A fresh, opt-in session; no persistent scores or hidden voice listener."""

    def __init__(self, selector: EventSelector, seed: int | None = None) -> None:
        self.selector = selector
        self._rng = random.Random(seed)
        self.started_at: float | None = None
        self.completed: list[tuple[str, float]] = []
        self.last_choice: str | None = None
        self.last_outcome: str | None = None
        self._calm_completions = 0
        self._peak_visits = 0
        self._last_strong_at: float | None = None
        self.recovery = False
        self.discovered: set[str] = set()

    def begin(self, now: float) -> None:
        self.started_at = now
        self.selector.history.clear()
        self.completed.clear()
        self.last_choice = self.last_outcome = None
        self._calm_completions = self._peak_visits = 0
        self._last_strong_at = None
        self.recovery = False

    def end(self) -> None:
        self.started_at = None

    def elapsed(self, now: float) -> float:
        return max(0., now - self.started_at) if self.started_at is not None else 0.

    def level(self, now: float) -> Intensity:
        if self.started_at is None or self._calm_completions == 0:
            return Q
        if self._calm_completions < 4 or self.elapsed(now) < 90:
            return L1
        if self._calm_completions < 7 or self.elapsed(now) < 180:
            return L2
        # Extended sessions become quieter without terminating the haunting.
        if self.elapsed(now)>1200:
            return L2
        return L3

    def summon(self, now: float) -> EventSpec | None:
        """Foreground invocation shares event and strong-event cooldowns.

        Summoning may invite a Raven earlier than its spontaneous debut, but
        never bypasses the recovery after a strong event or active playback.
        The app/Router owns active-playback and invocation-rate guards.
        """
        if self.started_at is None or self.recovery:
            return None
        weighted={"raven_sweep":70,"raven_perch":24,"raven_dive":5,"raven_duet":1}
        candidates=[]
        for id_ in weighted:
            event=EVENTS[id_];direction=DIRECTIONS[id_]
            if not self.selector.available(event,now):continue
            if any(e==id_ and now-t<direction.cooldown_s for e,t in self.selector.history):continue
            if direction.strong and self._last_strong_at is not None and now-self._last_strong_at<STRONG_RECOVERY_S:continue
            candidates.append(event)
        if not candidates:return None
        if not any(e in weighted for e,_ in self.selector.history):
            return next((e for e in candidates if e.id=="raven_sweep"),candidates[0])
        return self._rng.choices(candidates,[weighted[e.id] for e in candidates],k=1)[0]

    def strong_blocked(self, now: float) -> set[str]:
        """Strong events still inside the 180 s recovery after the last one."""
        if self._last_strong_at is None or now - self._last_strong_at >= STRONG_RECOVERY_S:
            return set()
        return {id_ for id_, direction in DIRECTIONS.items() if direction.strong}

    @staticmethod
    def family(event_id: str) -> Family:
        if event_id in DIRECTIONS:
            return DIRECTIONS[event_id].family
        return C

    def choice_made(self, choice: str | None, outcome_id: str) -> None:
        self.last_choice = choice
        self.last_outcome = outcome_id

    def complete(self, event_id: str, now: float) -> None:
        if self.started_at is None:
            return
        self.completed.append((event_id, now))
        # Prompt + outcome are one encounter. The handoff has no new silence.
        if event_id == "trick_or_treat":
            return
        direction = DIRECTIONS.get(event_id)
        if direction is not None and direction.strong:
            self._last_strong_at = now
            self._calm_completions = self._peak_visits = 0
            self.recovery = True
            return
        self.recovery = False
        if self.level(now) == L3:
            self._peak_visits += 1
        self._calm_completions += 1
        # A peak is a short opportunity, never a permanent difficulty level.
        if self._peak_visits >= 3:
            self._calm_completions = 2
            self._peak_visits = 0

    def candidates(self, now: float) -> list[EventSpec]:
        if self.started_at is None:
            return []
        level = self.level(now)
        result = []
        for event_id, direction in DIRECTIONS.items():
            event = EVENTS[event_id]
            if direction.minimum_level > level or self.elapsed(now) < direction.earliest_s:
                continue
            if not self.selector.available(event, now):
                continue
            if direction.strong and self._last_strong_at is not None:
                if now - self._last_strong_at < STRONG_RECOVERY_S:
                    continue
            if any(id_ == event_id and now - started < direction.cooldown_s
                   for id_, started in self.selector.history):
                continue
            result.append(event)
        return result

    def choose(self, now: float) -> EventSpec | None:
        candidates = self.candidates(now)
        if not candidates:
            return None  # silence is preferable to bypassing a cooldown
        families = list(dict.fromkeys(self.family(e.id) for e in candidates))
        recent = [self.family(id_) for id_, _ in self.completed[-2:]]
        if len(recent) == 2 and recent[0] == recent[1] and len(families) > 1:
            families = [f for f in families if f != recent[-1]]
        family_weights = [
            FAMILY_WEIGHTS[self.level(now)][f] * (.4 if recent and recent[-1] == f else 1)
            for f in families
        ]
        family = self._rng.choices(families, weights=family_weights, k=1)[0]
        candidates = [e for e in candidates if self.family(e.id) == family]
        counts = Counter(id_ for id_, _ in self.completed)
        weights = []
        for event in candidates:
            weight = RARITY_WEIGHT[DIRECTIONS[event.id].rarity] / (1 + .5 * counts[event.id])
            if event.id in {"raven_duet","raven_dive","trick_behind_you","trick_raven_box","treat_ghost"} and event.id not in self.discovered:
                weight *= 1.12  # small unseen-encounter preference, after all pacing constraints
            if self.last_outcome:
                # Soften repeated emotional payoffs, without changing the
                # selector's 65/35 rule for an actual TRICK/TREAT choice.
                last_category = EVENTS[self.last_outcome].category
                if event.category == last_category:
                    weight *= .65
            weights.append(weight)
        return self._rng.choices(candidates, weights=weights, k=1)[0]
