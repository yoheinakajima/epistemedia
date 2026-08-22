from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from epistemedia.core import accepted_commit, accepted_timestamp


ROOT = Path(__file__).resolve().parents[1]


def test_container_context_excludes_local_and_secret_state() -> None:
    patterns = set((ROOT / ".dockerignore").read_text().splitlines())
    required = {
        ".git",
        ".venv",
        "**/__pycache__",
        "generated/public",
        ".env",
        ".env.*",
        "private",
        "internal",
        "**/*.pem",
        "**/*.key",
        "**/credentials.*",
        "**/secrets.*",
    }
    assert required <= patterns


def test_container_copies_declared_inputs_instead_of_the_whole_checkout() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "COPY . ." not in dockerfile
    assert "\nCOPY .git " not in dockerfile
    assert "EPISTEMEDIA_ACCEPTED_COMMIT" in dockerfile
    assert "SOURCE_DATE_EPOCH" in dockerfile
    assert "USER epistemedia" in dockerfile


def test_git_identity_wins_over_an_explicit_build_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    monkeypatch.setenv("EPISTEMEDIA_ACCEPTED_COMMIT", "not-a-commit")
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-epoch")
    assert accepted_commit(ROOT) == expected
    accepted_timestamp(ROOT)


def test_valid_build_identity_is_used_without_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = "a" * 40
    epoch = "1700000000"
    monkeypatch.setenv("EPISTEMEDIA_ACCEPTED_COMMIT", commit)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", epoch)
    assert accepted_commit(tmp_path) == commit
    assert accepted_timestamp(tmp_path) == (
        datetime.fromtimestamp(int(epoch), timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@pytest.mark.parametrize("value", ["A" * 40, "a" * 39, "g" * 40, "release-main"])
def test_malformed_build_commit_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("EPISTEMEDIA_ACCEPTED_COMMIT", value)
    with pytest.raises(ValueError, match="accepted commit"):
        accepted_commit(tmp_path)


@pytest.mark.parametrize("value", ["-1", "1.5", " 1700000000", "tomorrow"])
def test_malformed_source_epoch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", value)
    with pytest.raises(ValueError, match="accepted source timestamp"):
        accepted_timestamp(tmp_path)
