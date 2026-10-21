import pytest

from nevermore.scheduler import HauntSchedule, HauntTiming


def test_delay_stays_inside_window() -> None:
    schedule = HauntSchedule(
        HauntTiming(1.0, 2.0),
        seed=7,
    )
    values = [
        schedule.next_delay_ms()
        for _ in range(100)
    ]
    assert min(values) >= 1000
    assert max(values) <= 2000


def test_invalid_timing_is_rejected() -> None:
    with pytest.raises(ValueError):
        HauntSchedule(
            HauntTiming(0.0, 1.0)
        )

    with pytest.raises(ValueError):
        HauntSchedule(
            HauntTiming(3.0, 2.0)
        )
