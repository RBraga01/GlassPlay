"""Input boundary shared by buttons, shortcuts and a future keyword spotter."""

from __future__ import annotations

from collections.abc import Callable
import time

from .events import EVENTS, EventSelector, EventSpec


class TriggerRouter:
    def __init__(self, selector: EventSelector,
                 dispatch: Callable[[EventSpec, str], bool],
                 summon: Callable[[float], EventSpec | None] | None = None) -> None:
        self.selector = selector
        self.dispatch = dispatch
        self.summon = summon
        self.last_summon = float("-inf")

    def trigger_event(self, event_id: str, source: str = "manual") -> bool:
        return self.dispatch(EVENTS[event_id], source)

    def trigger_raven(self, source: str = "manual") -> bool:
        if self.summon is not None:
            now=time.monotonic()
            if now-self.last_summon<30:
                return False
            event=self.summon(now)
            if event is None or not self.dispatch(event,source):
                return False
            self.last_summon=now
            return True
        return self.dispatch(self.selector.choose_raven(), source)

    def keyword_detected(self, text: str) -> bool:
        """The caller must be a real detector; this method does no listening."""
        if text.strip().casefold() != "raven":
            return False
        return self.trigger_raven("keyword")
