import io
import wave

from nevermore.audio import build_sound_bank, heartbeat, raven_caw, wing_rush


def _assert_valid_wav(data: bytes) -> None:
    assert data.startswith(b"RIFF")
    with wave.open(io.BytesIO(data), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 22050
        assert wav.getnframes() > 1000


def test_procedural_audio_is_valid_wav() -> None:
    for data in (
        raven_caw(),
        wing_rush(),
        heartbeat(),
    ):
        _assert_valid_wav(data)


def test_every_event_sound_is_valid_and_short() -> None:
    bank = build_sound_bank()
    for data in bank.values():
        _assert_valid_wav(data)
        with wave.open(io.BytesIO(data), "rb") as wav:
            assert wav.getnframes() / wav.getframerate() < 2.0
