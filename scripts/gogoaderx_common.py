"""Shared helpers for gogoaderx hook scripts.

Hooks only act in repositories that have run /gogoaderx:init, i.e. that contain
.gogoaderx/config.json. Everywhere else they exit 0 and stay out of the way.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

DEFAULT_PROTECTED = ["main", "master", "develop", "release/*"]


def read_payload() -> dict[str, Any]:
    """Read the hook's JSON payload from stdin (empty dict if unreadable)."""
    try:
        data = json.load(sys.stdin)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def project_dir(payload: dict[str, Any]) -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    cwd = payload.get("cwd")
    return Path(cwd) if cwd else Path.cwd()


def load_config(
    payload: dict[str, Any],
) -> Tuple[Optional[Path], Optional[dict[str, Any]]]:
    """Find .gogoaderx/config.json by walking up from the project dir.

    Returns (None, None) when gogoaderx is not set up in this repo.
    Returns (root, {}) when the file exists but is not valid JSON, so hooks fall
    back to safe defaults instead of silently turning themselves off.
    """
    start = project_dir(payload).resolve()
    for directory in [start, *start.parents]:
        candidate = directory / ".gogoaderx" / "config.json"
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                return directory, data if isinstance(data, dict) else {}
            except (OSError, json.JSONDecodeError):
                return directory, {}
    return None, None
