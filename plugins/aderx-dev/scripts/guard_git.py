#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash): keeps git pushes under the user's control.

Runs only in repositories that have .aderx-dev/config.json.

BLOCKS (exit 2, the agent is told why):
  * force pushes (--force, -f, --force-with-lease, +refspec, --mirror)
  * pushes that would update a protected branch (config git.protectedBranches, plus
    git.baseBranch), including a bare `git push` while ON a protected branch
  * `git push --all` (would include protected branches)
  * `gh pr merge` (merging is a human decision in this workflow)

ASKS (permissionDecision "ask") for every other real `git push`. Claude Code then shows
its own confirmation prompt to the user, even if an allow rule would otherwise let the
command through, and the prompt describes what is about to be published. `--dry-run`
pushes publish nothing and are not prompted.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterator, Optional

from aderx_dev_common import DEFAULT_PROTECTED, load_config, read_payload

OPERATORS = {"&&", "||", ";", "|", "&"}
GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
SHORT_FORCE = re.compile(r"-[A-Za-z]*f[A-Za-z]*")
CRUDE_PUSH = re.compile(r"\bgit\b[^\n;&|]*\bpush\b")
MAX_SUBJECTS = 5


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def is_protected(branch: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(branch, pattern) for pattern in patterns)


def git_invocations(tokens: list[str]) -> Iterator[tuple[str, list[str]]]:
    """Yield (subcommand, args) for every `git` invocation in a token list."""
    for i, token in enumerate(tokens):
        if os.path.basename(token) != "git":
            continue
        j = i + 1
        while j < len(tokens) and tokens[j].startswith("-"):
            j += 2 if tokens[j] in GLOBAL_OPTS_WITH_VALUE else 1
        if j >= len(tokens):
            continue
        args: list[str] = []
        for tok in tokens[j + 1:]:
            if tok in OPERATORS or os.path.basename(tok) == "git":
                break
            args.append(tok)
        yield tokens[j], args


def pushes_in(command: str) -> list[list[str]]:
    """Argument lists of every `git push` in a command line.

    If the command cannot be tokenized but looks like it contains a push, return a single
    empty argument list, so the caller errs on the side of asking the user.
    """
    try:
        tokens = tokenize(command)
    except ValueError:
        return [[]] if CRUDE_PUSH.search(command) else []
    return [args for sub, args in git_invocations(tokens) if sub == "push"]


def is_dry_run(args: list[str]) -> bool:
    return "--dry-run" in args or "-n" in args


def check_push(args: list[str], current_branch: Optional[str], protected: list[str]) -> Optional[str]:
    """Return a block reason for `git push <args>`, or None if it is allowed."""
    for arg in args:
        if arg in ("--force", "--mirror", "--force-if-includes") or arg.startswith("--force-with-lease"):
            return f"force/mirror push ({arg}) is not allowed"
        if not arg.startswith("--") and SHORT_FORCE.fullmatch(arg):
            return f"force push ({arg}) is not allowed"
        if arg == "--all":
            return "`git push --all` would include protected branches"

    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]  # first positional is the remote

    targets: list[str] = []
    if not refspecs:
        if current_branch:
            targets.append(current_branch)  # bare push goes to the current branch
    for spec in refspecs:
        if spec.startswith("+"):
            return f"force push (+{spec[1:]}) is not allowed"
        src, colon, dst = spec.partition(":")
        target = (dst or src) if colon else src
        target = target.removeprefix("refs/heads/")
        if target == "HEAD" and current_branch:
            target = current_branch
        targets.append(target)

    for target in targets:
        if is_protected(target, protected):
            return f"pushing to protected branch '{target}' is not allowed"
    return None


def check_command(command: str, current_branch: Optional[str], protected: list[str]) -> Optional[str]:
    """Return a block reason for a full Bash command line, or None if allowed."""
    try:
        tokens = tokenize(command)
    except ValueError:
        return crude_check(command, protected)

    for sub, args in git_invocations(tokens):
        if sub == "push":
            reason = check_push(args, current_branch, protected)
            if reason:
                return reason

    for i, token in enumerate(tokens):
        if os.path.basename(token) == "gh":
            rest: list[str] = []
            for tok in tokens[i + 1:]:
                if tok in OPERATORS:
                    break
                rest.append(tok)
            if "pr" in rest and "merge" in rest[rest.index("pr") + 1:]:
                return "`gh pr merge` is not allowed: merging is a human decision"
    return None


def crude_check(command: str, protected: list[str]) -> Optional[str]:
    """Fallback when the command can't be tokenized (e.g. odd heredocs)."""
    if not CRUDE_PUSH.search(command):
        return None
    if re.search(r"(--force\b|--force-with-lease|--mirror|\s-[A-Za-z]*f\b|\s\+\S)", command):
        return "force push detected (command could not be parsed precisely)"
    for pattern in protected:
        if "*" not in pattern and re.search(rf"(?<![\w/-]){re.escape(pattern)}(?![\w/-])", command):
            return f"possible push to protected branch '{pattern}' (command could not be parsed precisely)"
    return None


def _git(cwd: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def current_branch_of(cwd: Path) -> Optional[str]:
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    return branch if branch and branch != "HEAD" else None


def describe_push(cwd: Path, args: list[str], current_branch: Optional[str]) -> str:
    """Human-readable summary of what a push would publish, for the approval prompt."""
    positional = [a for a in args if not a.startswith("-")]
    remote = positional[0] if positional else "origin"
    refspecs = positional[1:]
    url = _git(cwd, "remote", "get-url", remote)
    where = f"{url} ({remote})" if url else remote

    deleting = "--delete" in args or "-d" in args or any(s.startswith(":") for s in refspecs)
    if deleting:
        names = ", ".join(s.lstrip(":") or "?" for s in refspecs) or "a remote ref"
        return f"aderx-dev: approve this git push? It DELETES remote ref(s) {names} on {where}."

    target = ", ".join(refspecs) if refspecs else (current_branch or "the current branch")
    lines = [f"aderx-dev: approve this git push? It publishes code to {where}, ref: {target}."]

    src = (refspecs[0].lstrip("+").partition(":")[0] if refspecs else "") or "HEAD"
    remotes_arg = f"--remotes={remote}" if url else "--remotes"
    count = _git(cwd, "rev-list", "--count", src, "--not", remotes_arg)
    if count.isdigit():
        n = int(count)
        lines.append(f"Commits not yet on the remote: {n}.")
        if n:
            subjects = _git(cwd, "log", "--oneline", f"-{MAX_SUBJECTS}", src, "--not", remotes_arg)
            lines.extend(f"  {s}" for s in subjects.splitlines())
            if n > MAX_SUBJECTS:
                lines.append(f"  ... and {n - MAX_SUBJECTS} more")
    return "\n".join(lines)


def ask_decision(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    payload = read_payload()
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    root, config = load_config(payload)
    if root is None:
        return 0  # aderx-dev not initialised in this repo: stay out of the way

    git_cfg = (config or {}).get("git") or {}
    protected = list(git_cfg.get("protectedBranches") or DEFAULT_PROTECTED)
    if git_cfg.get("baseBranch"):
        protected.append(git_cfg["baseBranch"])

    cwd = Path(payload.get("cwd") or root)
    branch = current_branch_of(cwd)

    reason = check_command(command, branch, protected)
    if reason:
        print(
            f"aderx-dev guard: blocked. {reason}. "
            "Push a feature branch and open a PR instead, or ask the user to run this themselves.",
            file=sys.stderr,
        )
        return 2

    real_pushes = [args for args in pushes_in(command) if not is_dry_run(args)]
    if real_pushes:
        print(json.dumps(ask_decision(describe_push(cwd, real_pushes[0], branch))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
