"""The reviewable event catalogue and its selection rules.

Nothing in this module depends on Qt. The foreground UI, a future keyword
spotter, and a possible RavenOS service can all use the same event IDs.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very rare"


RARITY_WEIGHT = {
    Rarity.COMMON: 12.0,
    Rarity.UNCOMMON: 5.0,
    Rarity.RARE: 1.4,
    Rarity.VERY_RARE: 0.3,
}


@dataclass(frozen=True)
class EventSpec:
    id: str
    category: str
    rarity: Rarity
    cooldown_s: float
    intensity: int
    duration_ms: int
    sound: str | None
    visual: str
    random_enabled: bool = True
    requires_choice: bool = False
    blocked_after: tuple[str, ...] = ()
    sound_at: float = 0.13


CATALOG = (
    EventSpec("raven_sweep", "raven", Rarity.COMMON, 35, 2, 4000, "raven", "raven_sweep"),
    EventSpec("raven_dive", "raven", Rarity.UNCOMMON, 45, 3, 3000, None, "raven_dive"),
    EventSpec("raven_perch", "raven", Rarity.UNCOMMON, 45, 1, 5500, "raven", "raven_perch", sound_at=.61),
    EventSpec("raven_shadow", "raven", Rarity.RARE, 60, 2, 1500, "wing", "raven_shadow"),
    EventSpec("raven_duet", "raven", Rarity.VERY_RARE, 90, 3, 5000, "raven", "raven_duet"),
    EventSpec("eyes", "ambient", Rarity.COMMON, 40, 1, 3000, "heartbeat", "eyes"),
    EventSpec("nevermore", "ambient", Rarity.UNCOMMON, 55, 1, 3300, "wind", "nevermore"),
    EventSpec("ghost", "ambient", Rarity.COMMON, 35, 1, 3300, "ghost", "ghost"),
    EventSpec("spider", "ambient", Rarity.UNCOMMON, 45, 1, 2700, None, "spider"),
    EventSpec("shadow", "ambient", Rarity.COMMON, 32, 1, 2300, "wing", "shadow"),
    EventSpec("glitch", "scare", Rarity.RARE, 65, 2, 2600, "impact", "glitch",
              blocked_after=("raven_dive", "raven_duet")),
    EventSpec("pumpkin", "playful", Rarity.UNCOMMON, 45, 1, 3100, "jingle", "pumpkin"),
    EventSpec("trick_or_treat", "prompt", Rarity.UNCOMMON, 80, 1, 5500, "chime", "prompt", requires_choice=True),
    EventSpec("trick_raven_box", "trick", Rarity.RARE, 45, 3, 3000, "raven", "trick_raven_box", False),
    EventSpec("trick_spider", "trick", Rarity.UNCOMMON, 35, 2, 2700, "impact", "trick_spider", False),
    EventSpec("trick_behind_you", "trick", Rarity.UNCOMMON, 40, 2, 2900, "whisper", "trick_behind_you", False),
    EventSpec("treat_candy", "treat", Rarity.COMMON, 25, 1, 3300, "jingle", "treat_candy", False),
    EventSpec("treat_ghost", "treat", Rarity.COMMON, 25, 1, 3300, "ghost", "treat_ghost", False),
    EventSpec("treat_pumpkin", "treat", Rarity.COMMON, 25, 1, 3100, "jingle", "treat_pumpkin", False),
    EventSpec("treat_badge", "treat", Rarity.UNCOMMON, 30, 1, 2800, "chime", "treat_badge", False),
)

EVENTS = {event.id: event for event in CATALOG}
RAVEN_IDS = tuple(event.id for event in CATALOG if event.category == "raven")
TRICK_IDS = tuple(event.id for event in CATALOG if event.category == "trick")
TREAT_IDS = tuple(event.id for event in CATALOG if event.category == "treat")
MANUAL_IDS = tuple(event.id for event in CATALOG)


class EventSelector:
    """Session history, weighted rarity, and per-event cooldowns."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self.history: list[tuple[str, float]] = []

    @property
    def last_id(self) -> str | None:
        return self.history[-1][0] if self.history else None

    def record(self, event_id: str, now: float) -> None:
        if event_id not in EVENTS:
            raise KeyError(event_id)
        self.history.append((event_id, now))

    def eligible(self, event: EventSpec, now: float) -> bool:
        return event.random_enabled and self.available(event, now)

    def available(self, event: EventSpec, now: float) -> bool:
        """Shared cooldown/repeat rules, including authored direct encounters."""
        if event.id == self.last_id:
            return False
        if self.last_id in event.blocked_after:
            return False
        return all(
            event_id != event.id or now - started >= event.cooldown_s
            for event_id, started in self.history
        )

    def choose(self, now: float) -> EventSpec | None:
        candidates = [event for event in CATALOG if self.eligible(event, now)]
        if not candidates:
            return None
        weights = [RARITY_WEIGHT[event.rarity] / max(1, event.intensity) for event in candidates]
        return self._rng.choices(candidates, weights=weights, k=1)[0]

    def choose_raven(self) -> EventSpec:
        candidates = [EVENTS[id_] for id_ in RAVEN_IDS if id_ != self.last_id]
        return self._rng.choice(candidates)

    def choose_outcome(self, choice: str | None,
                       exclude: frozenset[str] | set[str] = frozenset()) -> EventSpec:
        """A choice biases the result, but never promises safety or danger.

        ``exclude`` removes outcomes still in recovery (e.g. strong scares)
        after the family draw, so the 65/35 family bias is unchanged.
        """
        if choice not in (None, "TRICK", "TREAT"):
            raise ValueError(choice)
        if choice is None:
            family = self._rng.choice((TRICK_IDS, TREAT_IDS))
        else:
            expected = TRICK_IDS if choice == "TRICK" else TREAT_IDS
            surprise = TREAT_IDS if choice == "TRICK" else TRICK_IDS
            family = expected if self._rng.random() < 0.65 else surprise
        candidates = [id_ for id_ in family if id_ != self.last_id]
        candidates = [id_ for id_ in candidates if id_ not in exclude] or candidates
        return EVENTS[self._rng.choice(candidates)]
