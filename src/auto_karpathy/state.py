"""Tiny JSON state file so --watch doesn't re-build the same tweet twice."""

from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_state_dir

APP = "auto-karpathy"


def _state_file() -> Path:
    p = Path(user_state_dir(APP)) / "seen.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_seen() -> set[str]:
    f = _state_file()
    if not f.exists():
        return set()
    try:
        return set(json.loads(f.read_text()))
    except (json.JSONDecodeError, OSError):
        return set()


def mark_seen(tweet_ids: list[str] | set[str]) -> None:
    seen = load_seen()
    seen.update(tweet_ids)
    _state_file().write_text(json.dumps(sorted(seen)))
