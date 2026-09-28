#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash): blocks the git operations that are hard to undo.

Runs only in repositories that have .aderx-dev/config.json.

BLOCKS (exit 2, the agent is told why):
  * force pushes (--force, -f, --force-with-lease, +refspec, --mirror)
  * pushes that would update a protected branch (config git.protectedBranches, plus
    git.baseBranch), including a bare `git push` while ON a protected branch; with
    `git -C <path>` the branch is looked up in the repository at <path>
  * `git push --all` / `--branches` (would include protected branches)
  * `gh pr merge` (merging is a human decision in this workflow)

Every other command is left alone: Claude Code's own permission prompt and pr-create's
push approval decide whether it runs. The real protection for the base branch belongs on
the server (branch protection or rulesets); this hook is an early, local warning.
"""
from __future__ import annotations

import fnmatch
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterator, NamedTuple, Optional, Sequence

from aderx_dev_common import DEFAULT_PROTECTED, load_config, read_payload

OPERATORS = {"&&", "||", ";", "|", "&"}
GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
# `git push` options whose value may be the next token (`-o ci.skip`, `--repo origin`).
# Read as positionals, the value would pass for the remote and the remote for a refspec,
# hiding which branch is really pushed.
PUSH_OPTS_WITH_VALUE = {"--repo", "--push-option", "--receive-pack", "--exec", "--recurse-submodules"}
SHORT_PUSH_OPT_WITH_VALUE = "o"
SHORT_FORCE = re.compile(r"-[A-Za-z]*f[A-Za-z]*")
CRUDE_PUSH = re.compile(r"\bgit\b[^\n;&|]*\bpush\b")


class PushArgs(NamedTuple):
    options: list[str]  # flags as written, with option values removed
    remote: Optional[str]
    refspecs: list[str]


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def is_protected(branch: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(branch, pattern) for pattern in patterns)


def git_invocations(tokens: list[str]) -> Iterator[tuple[str, list[str], list[str]]]:
    """Yield (subcommand, args, global options) for every `git` invocation in a token list.

    The global options (`-C <path>`, `--git-dir=...`) matter: they choose which repository
    the subcommand acts on.
    """
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
        yield tokens[j], args, tokens[i + 1:j]


def parse_push_args(args: list[str]) -> PushArgs:
    """Split `git push` arguments the way git does, so option values are never positionals."""
    options: list[str] = []
    positional: list[str] = []
    repo_option: Optional[str] = None
    i = 0
    while i < len(args):
        arg = args[i]
        i += 1
        if arg == "--":
            positional.extend(args[i:])
            break
        if arg.startswith("--"):
            name, eq, value = arg.partition("=")
            if name in PUSH_OPTS_WITH_VALUE:
                if not eq and i < len(args):
                    value = args[i]
                    i += 1
                if name == "--repo":
                    repo_option = value
                options.append(name)
            else:
                options.append(arg)
        elif arg.startswith("-") and len(arg) > 1:
            flags = arg[1:]
            cut = flags.find(SHORT_PUSH_OPT_WITH_VALUE)
            if cut != -1:
                if cut == len(flags) - 1 and i < len(args):
                    i += 1  # `-o value`; otherwise the rest of the cluster is the value
                flags = flags[:cut]
            if flags:
                options.append("-" + flags)
        else:
            positional.append(arg)
    # A repository given as an argument wins over --repo, as in git.
    remote = positional[0] if positional else repo_option
    return PushArgs(options, remote, positional[1:])


def check_push(args: list[str], current_branch: Optional[str], protected: list[str]) -> Optional[str]:
    """Return a block reason for `git push <args>`, or None if it is allowed."""
    push = parse_push_args(args)
    for opt in push.options:
        if opt in ("--force", "--mirror", "--force-if-includes") or opt.startswith("--force-with-lease"):
            return f"force/mirror push ({opt}) is not allowed"
        if not opt.startswith("--") and SHORT_FORCE.fullmatch(opt):
            return f"force push ({opt}) is not allowed"
        if opt in ("--all", "--branches"):
            return f"`git push {opt}` would include protected branches"

    targets: list[str] = []
    if not push.refspecs:
        if current_branch:
            targets.append(current_branch)  # bare push goes to the current branch
    for spec in push.refspecs:
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


def check_command(
    command: str,
    current_branch: Optional[str],
    protected: list[str],
    branch_of: Optional[Callable[[list[str]], Optional[str]]] = None,
) -> Optional[str]:
    """Return a block reason for a full Bash command line, or None if allowed.

    `branch_of(global_opts)` returns the current branch of the repository a git invocation
    acts on (`git -C ../other push` pushes other's branch). Without it, `current_branch`
    is used for every invocation.
    """
    try:
        tokens = tokenize(command)
    except ValueError:
        return crude_check(command, protected)

    for sub, args, global_opts in git_invocations(tokens):
        if sub == "push":
            branch = branch_of(global_opts) if branch_of else current_branch
            reason = check_push(args, branch, protected)
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


def current_branch_of(cwd: Path, git_opts: Sequence[str] = ()) -> Optional[str]:
    branch = _git(cwd, *git_opts, "rev-parse", "--abbrev-ref", "HEAD")
    return branch if branch and branch != "HEAD" else None


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

    def branch_of(git_opts: Sequence[str]) -> Optional[str]:
        return current_branch_of(cwd, git_opts)

    reason = check_command(command, None, protected, branch_of)
    if reason:
        print(
            f"aderx-dev guard: blocked. {reason}. "
            "Push a feature branch and open a PR instead, or ask the user to run this themselves.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
