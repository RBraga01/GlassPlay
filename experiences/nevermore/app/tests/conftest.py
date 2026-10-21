"""Never write test encounters into a user's persistent journal."""
import pytest

@pytest.fixture(autouse=True)
def isolated_discoveries(tmp_path,monkeypatch):
    monkeypatch.setenv("NEVERMORE_DATA_DIR",str(tmp_path/"user-data"))
