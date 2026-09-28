#!/usr/bin/env python3
"""PostToolUse hook: format the file Claude just edited.

Looks up the matching "area" in .aderx-dev/config.json (by file extension and by
the file living under the area's root) and runs that area's `format` command
with `{file}` replaced by the edited file's path.

Exit codes:
  0  nothing to do, or formatting succeeded (or the formatter isn't installed)
  2  the formatter ran and failed; stderr is shown to Claude so it can react
     (e.g. a syntax error it just introduced)
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

from aderx_dev_common import load_config, read_payload

# Dependency, build-output and tooling directories that are never formatted.
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode",
    "node_modules", "vendor", "third_party",
    ".venv", "venv", "__pycache__", ".tox", ".mypy_cache", ".ruff_cache",
    "dist", "build", "out", "target", ".next", ".nuxt", ".gradle",
}
TIMEOUT_SECONDS = 30


def pick_command(config: dict, root: Path, path: Path) -> tuple[list[str], Path] | None:
    """Return (argv, cwd) for the first area that owns this file, else None."""
    for area in (config.get("areas") or {}).values():
        if not isinstance(area, dict):
            continue
        command = area.get("format")
        extensions = area.get("extensions") or []
        if not command or "{file}" not in command or path.suffix not in extensions:
            continue
        area_root = (root / (area.get("root") or ".")).resolve()
        try:
            path.resolve().relative_to(area_root)
        except ValueError:
            continue  # file is outside this area
        argv = [part.replace("{file}", str(path)) for part in shlex.split(command)]
        return argv, area_root
    return None


def main() -> int:
    payload = read_payload()
    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0

    path = Path(file_path)
    if not path.is_file():
        return 0

    root, config = load_config(payload)
    if root is None or not config:
        return 0

    # Judge skip rules on the path *inside* the repo, so that a checkout that happens
    # to live under a directory called "build" or "out" is still formatted.
    try:
        inside_repo = path.resolve().relative_to(root.resolve())
    except ValueError:
        return 0  # file is outside the repo
    if SKIP_DIRS & set(inside_repo.parts[:-1]):
        return 0

    picked = pick_command(config, root, path)
    if picked is None:
        return 0
    argv, cwd = picked

    try:
        result = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0  # formatter missing or too slow: never block the edit flow

    if result.returncode != 0:
        output = (result.stderr or result.stdout or "").strip()
        tail = "\n".join(output.splitlines()[-15:])
        print(f"aderx-dev: formatter failed for {path.name}:\n{tail}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
