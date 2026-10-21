from collections import Counter

from nevermore.events import (
    CATALOG, EVENTS, RAVEN_IDS, TRICK_IDS, TREAT_IDS, EventSelector,
    Rarity,
)
from nevermore.scheduler import HauntSchedule
from nevermore.triggers import TriggerRouter


def test_catalogue_has_real_variations_and_short_lived_events() -> None:
    ids = [event.id for event in CATALOG]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 20
    assert len(RAVEN_IDS) >= 3
    assert len(TRICK_IDS) >= 3
    assert len(TREAT_IDS) >= 3
    assert all(0 < event.duration_ms <= 5500 for event in CATALOG)
    assert all(0 <= event.intensity <= 3 for event in CATALOG)


def test_cooldown_and_no_immediate_repeat() -> None:
    selector = EventSelector(seed=7)
    selector.record("eyes", 100.0)
    assert not selector.eligible(EVENTS["eyes"], 101.0)
    assert not selector.eligible(EVENTS["eyes"], 200.0)  # last event
    selector.record("ghost", 105.0)
    assert not selector.eligible(EVENTS["eyes"], 120.0)
    assert selector.eligible(EVENTS["eyes"], 141.0)
    assert all(selector.choose(142.0).id != selector.last_id for _ in range(50))
    selector.record("trick_or_treat", 200.0)
    assert not selector.eligible(EVENTS["trick_or_treat"], 300.0)
    selector.record("raven_dive", 310.0)
    assert not selector.eligible(EVENTS["glitch"], 400.0)


def test_rarity_weights_and_outcome_surprise() -> None:
    selector = EventSelector(seed=19)
    counts = Counter(selector.choose(0).rarity for _ in range(3000))
    assert counts[Rarity.COMMON] > counts[Rarity.UNCOMMON]
    assert counts[Rarity.UNCOMMON] > counts[Rarity.RARE]
    assert counts[Rarity.RARE] > counts[Rarity.VERY_RARE]
    for choice in ("TRICK", "TREAT", None):
        families = {selector.choose_outcome(choice).category for _ in range(150)}
        assert families == {"trick", "treat"}


def test_fast_timing_is_separate_from_normal_timing() -> None:
    schedule = HauntSchedule(seed=4)
    normal = [schedule.next_delay_ms() for _ in range(50)]
    assert min(normal) >= 20_000 and max(normal) <= 60_000
    schedule.set_demo_mode(True)
    fast = [schedule.next_delay_ms() for _ in range(50)]
    assert min(fast) >= 5_000 and max(fast) <= 9_000
    schedule.set_demo_mode(False)
    assert schedule.next_delay_ms() >= 20_000


def test_keyword_routes_through_the_same_event_dispatch() -> None:
    selected = []
    def dispatch(event, source):
        selected.append((event.id, source))
        return True
    router = TriggerRouter(EventSelector(seed=2), dispatch)
    assert not router.keyword_detected("nevermore")
    assert router.keyword_detected("  RAVEN  ")
    assert selected[0][0] in RAVEN_IDS
    assert selected[0][1] == "keyword"
    assert router.trigger_event("eyes", "button")
    assert selected[1] == ("eyes", "button")
