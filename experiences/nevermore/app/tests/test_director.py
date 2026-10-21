"""Long sessions and transition boundaries, without waiting twenty minutes."""

from collections import Counter

from nevermore.director import DIRECTIONS, EventDirector, Family, Intensity
from nevermore.events import EVENTS, EventSelector
from nevermore.scheduler import HauntSchedule


def encounter(director, event_id, start):
    director.selector.record(event_id, start)
    director.complete(event_id, start + EVENTS[event_id].duration_ms / 1000)


def session(seed, seconds=1800):
    selector = EventSelector(seed)
    director = EventDirector(selector, seed)
    schedule = HauntSchedule(seed=seed)
    director.begin(0)
    encounter(director, "trick_or_treat", 2)
    result = selector.choose_outcome("TREAT")
    director.choice_made("TREAT", result.id)
    encounter(director, result.id, 7.5)
    now = 7.5 + result.duration_ms / 1000
    trace = []
    while now < seconds:
        wait = schedule.next_delay_ms(recovery=director.recovery,
                                      session_seconds=director.elapsed(now)) / 1000
        now += wait
        event = director.choose(now)
        if event is None:
            continue
        trace.append((event.id, now, director.level(now), wait))
        encounter(director, event.id, now)
        now += event.duration_ms / 1000
        if event.requires_choice:
            result = selector.choose_outcome("TRICK")
            director.choice_made("TRICK", result.id)
            encounter(director, result.id, now)
            now += result.duration_ms / 1000
    return director, trace


def test_opt_in_and_fresh_session():
    director = EventDirector(EventSelector(1), 1)
    assert director.choose(1000) is None
    director.begin(1000)
    assert director.level(1000) == Intensity.QUIET
    assert {e.id for e in director.candidates(1000)} == {"eyes", "shadow"}
    encounter(director, "eyes", 1000)
    director.end()
    assert director.choose(2000) is None
    director.begin(3000)
    assert director.completed == []
    assert director.selector.history == []
    assert director.level(3000) == Intensity.QUIET


def test_strong_event_resets_intensity_and_requires_presence():
    director = EventDirector(EventSelector(), 1)
    director.begin(0)
    for n in range(8):
        encounter(director, "eyes" if n % 2 else "shadow", n * 60)
    assert director.level(500) == Intensity.PEAK
    encounter(director, "raven_dive", 500)
    assert director.recovery
    assert director.level(503) == Intensity.QUIET
    assert all(director.family(e.id) == Family.PRESENCE for e in director.candidates(590))
    # Even rapid manual quiet encounters cannot bypass the global scare rest.
    for n in range(8):
        encounter(director, "eyes" if n % 2 else "shadow", 510 + 4 * n)
    assert all(not DIRECTIONS[e.id].strong for e in director.candidates(600))


def test_peak_is_not_permanent_even_when_no_scare_is_drawn():
    director = EventDirector(EventSelector(), 5)
    director.begin(0)
    levels = []
    for n in range(20):
        encounter(director, "eyes" if n % 2 else "shadow", n * 60)
        levels.append(director.level(n * 60 + 3))
    assert Intensity.PEAK in levels
    assert any(a == Intensity.PEAK and b < a for a, b in zip(levels, levels[1:]))


def test_director_preserves_cooldowns_and_no_repeat_over_seeded_sessions():
    counts = Counter()
    for seed in range(80):
        director, trace = session(seed)
        history = director.selector.history
        for index, (event_id, started, level, wait) in enumerate(trace):
            direction = DIRECTIONS[event_id]
            counts[event_id] += 1
            assert level >= direction.minimum_level
            assert started >= direction.earliest_s
            previous = [(id_, at) for id_, at in history if at < started - .0001]
            assert not previous or previous[-1][0] != event_id
            assert all(started - at >= max(EVENTS[event_id].cooldown_s, direction.cooldown_s)
                       for id_, at in previous if id_ == event_id)
            assert wait >= 20
            if direction.strong:
                assert all(started - end >= 180 for id_, end in director.completed
                           if end < started and id_ in DIRECTIONS and DIRECTIONS[id_].strong)
        # The prompt is less frequent than autonomous encounters.
        assert sum(id_ == "trick_or_treat" for id_, *_ in trace) < len(trace) / 3
    assert counts["raven_sweep"] > counts["raven_dive"] > counts["raven_duet"] > 0
    assert counts["eyes"] > counts["trick_or_treat"] > 0
    assert counts["treat_ghost"] > 0 and counts["trick_behind_you"] > 0
    assert not {"ghost", "spider", "pumpkin"} & counts.keys()  # use approved pack


def test_longer_recovery_and_late_session_quiet_but_demo_remains_fast():
    schedule = HauntSchedule(seed=5)
    assert all(60_000 <= schedule.next_delay_ms(recovery=True) <= 90_000 for _ in range(30))
    assert all(30_000 <= schedule.next_delay_ms(session_seconds=1200) <= 90_000 for _ in range(30))
    schedule.set_demo_mode(True)
    assert all(5000 <= schedule.next_delay_ms(recovery=True, session_seconds=1800) <= 9000
               for _ in range(30))


def test_trick_treat_bias_is_unchanged_and_choice_history_is_recorded():
    for choice in ("TRICK", "TREAT"):
        selector = EventSelector(19)
        results = [selector.choose_outcome(choice) for _ in range(10_000)]
        proportion = sum(e.category.upper() == choice for e in results) / len(results)
        assert .63 < proportion < .67
    director = EventDirector(EventSelector())
    director.begin(0)
    director.choice_made("TREAT", "trick_raven_box")
    assert director.last_choice == "TREAT"
    assert director.last_outcome == "trick_raven_box"


def test_trick_outcome_respects_strong_event_recovery():
    selector = EventSelector(3)
    director = EventDirector(selector, 3)
    director.begin(0)
    encounter(director, "raven_dive", 400)
    now = 400 + EVENTS["raven_dive"].duration_ms / 1000 + 120
    blocked = director.strong_blocked(now)
    assert blocked == {"trick_raven_box", "trick_behind_you", "raven_dive", "raven_duet"}
    results = Counter(selector.choose_outcome("TRICK", exclude=blocked).id
                      for _ in range(2000))
    assert not set(results) & blocked
    # The 65/35 family bias is unchanged: a TRICK choice still mostly tricks.
    tricks = sum(n for id_, n in results.items() if EVENTS[id_].category == "trick")
    assert 0.6 < tricks / 2000 < 0.7
    assert director.strong_blocked(now + 61) == set()
