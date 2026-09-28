"""Run with: python3 -m pytest tests/  (from the plugin root)"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from guard_git import check_command  # noqa: E402

PROTECTED = ["main", "master", "develop", "release/*"]


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin feature",
        "git push -f",
        "git push -uf origin feature",
        "git push --force-with-lease origin feature",
        "git push origin +feature",
        "git push origin main",
        "git push origin HEAD:main",
        "git push origin feature:refs/heads/main",
        "git push origin release/1.2",
        "git push origin --delete main",
        "git push --all",
        "git push --mirror",
        "git add . && git commit -m x && git push origin main",
        "git status\ngit push origin main",
        "git -C ../repo push origin main",
        "gh pr merge 12 --squash",
        "gh pr merge",
    ],
)
def test_blocked(command):
    assert check_command(command, "feature", PROTECTED), command


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin feature",
        "git push origin HEAD",
        "git push",
        "git push --set-upstream origin eng-123-add-rate-limit",
        "git push --follow-tags origin feature",
        "git commit -m 'docs: mention git push origin main'",
        "echo 'git push --force'",
        "git status && git diff --stat",
        "gh pr create --draft --title x --body y",
        "gh pr view 12",
    ],
)
def test_allowed(command):
    assert check_command(command, "feature", PROTECTED) is None, command


def test_bare_push_on_protected_branch_is_blocked():
    assert check_command("git push", "main", PROTECTED)
    assert check_command("git push origin HEAD", "main", PROTECTED)


def test_unparseable_command_falls_back_to_crude_check():
    assert check_command("git push --force origin x '", "feature", PROTECTED)
    assert check_command("echo 'unbalanced", "feature", PROTECTED) is None


def run_hook(script: str, payload: dict, cwd: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script)],
        input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=env,
    )


def make_repo(tmp_path: Path, config: dict | None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "feature"], cwd=tmp_path, check=True)
    if config is not None:
        (tmp_path / ".aderx-dev").mkdir()
        (tmp_path / ".aderx-dev" / "config.json").write_text(json.dumps(config))
    return tmp_path


def test_guard_inactive_without_config(tmp_path):
    repo = make_repo(tmp_path, None)
    result = run_hook("guard_git.py", {"cwd": str(repo), "tool_input": {"command": "git push -f"}}, repo)
    assert result.returncode == 0


def test_guard_blocks_with_config_and_uses_base_branch(tmp_path):
    repo = make_repo(tmp_path, {"git": {"baseBranch": "trunk", "protectedBranches": ["prod"]}})
    for command in ("git push origin trunk", "git push origin prod", "git push -f origin feature"):
        result = run_hook("guard_git.py", {"cwd": str(repo), "tool_input": {"command": command}}, repo)
        assert result.returncode == 2, command
        assert "aderx-dev guard" in result.stderr
    ok = run_hook("guard_git.py", {"cwd": str(repo), "tool_input": {"command": "git push -u origin feature"}}, repo)
    assert ok.returncode == 0


def test_guard_with_invalid_config_uses_defaults(tmp_path):
    repo = make_repo(tmp_path, {})
    (repo / ".aderx-dev" / "config.json").write_text("{ not json")
    result = run_hook("guard_git.py", {"cwd": str(repo), "tool_input": {"command": "git push origin main"}}, repo)
    assert result.returncode == 2


FORMATTER = "python3 -c \"import sys; open(sys.argv[1], 'a').write('# formatted\\n')\" {file}"


def area_config(**overrides) -> dict:
    area = {"root": "backend", "extensions": [".py"], "format": FORMATTER}
    area.update(overrides)
    return {"areas": {"backend": area}}


def test_format_runs_for_matching_file(tmp_path):
    repo = make_repo(tmp_path, area_config())
    target = repo / "backend" / "app.py"
    target.parent.mkdir()
    target.write_text("x = 1\n")
    result = run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
    assert result.returncode == 0
    assert target.read_text().endswith("# formatted\n")


def test_format_skips_other_extension_outside_root_and_vendor_dirs(tmp_path):
    repo = make_repo(tmp_path, area_config())
    (repo / "backend").mkdir()
    (repo / "backend" / "notes.md").write_text("hi\n")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "tool.py").write_text("x = 1\n")
    (repo / "backend" / "node_modules").mkdir()
    (repo / "backend" / "node_modules" / "dep.py").write_text("x = 1\n")
    for rel in ("backend/notes.md", "scripts/tool.py", "backend/node_modules/dep.py"):
        target = repo / rel
        before = target.read_text()
        result = run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
        assert result.returncode == 0
        assert target.read_text() == before, rel


def test_format_requires_file_placeholder(tmp_path):
    repo = make_repo(tmp_path, area_config(format="python3 -c pass"))
    target = repo / "backend" / "app.py"
    target.parent.mkdir()
    target.write_text("x = 1\n")
    result = run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
    assert result.returncode == 0


def test_format_failure_surfaces_to_claude(tmp_path):
    repo = make_repo(tmp_path, area_config(format="python3 -c \"import sys; sys.exit('bad syntax')\" {file}"))
    target = repo / "backend" / "app.py"
    target.parent.mkdir()
    target.write_text("x = 1\n")
    result = run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
    assert result.returncode == 2
    assert "bad syntax" in result.stderr


def test_format_missing_binary_is_silent(tmp_path):
    repo = make_repo(tmp_path, area_config(format="definitely-not-installed {file}"))
    target = repo / "backend" / "app.py"
    target.parent.mkdir()
    target.write_text("x = 1\n")
    result = run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
    assert result.returncode == 0


def test_format_runs_even_if_repo_lives_under_a_skipped_dir_name(tmp_path):
    repo = make_repo(tmp_path / "build" / "out" / "project", area_config())
    target = repo / "backend" / "app.py"
    target.parent.mkdir()
    target.write_text("x = 1\n")
    result = run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
    assert result.returncode == 0
    assert target.read_text().endswith("# formatted\n")


def test_format_respects_configured_ignore_dirs(tmp_path):
    config = area_config()
    config["hooks"] = {"formatIgnoreDirs": ["generated"]}
    repo = make_repo(tmp_path, config)
    skipped = repo / "backend" / "generated" / "api.py"
    skipped.parent.mkdir(parents=True)
    skipped.write_text("x = 1\n")
    normal = repo / "backend" / "api.py"
    normal.write_text("x = 1\n")
    for target in (skipped, normal):
        run_hook("format_on_edit.py", {"cwd": str(repo), "tool_input": {"file_path": str(target)}}, repo)
    assert skipped.read_text() == "x = 1\n"
    assert normal.read_text().endswith("# formatted\n")


# --------------------------------------------------------------------------------------
# Push approval: every real `git push` must trigger Claude Code's own confirmation prompt
# --------------------------------------------------------------------------------------
from guard_git import is_dry_run, parse_push_args, push_invocations  # noqa: E402


def decision(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout)["hookSpecificOutput"]


def run_guard(repo: Path, command: str) -> subprocess.CompletedProcess:
    return run_hook("guard_git.py", {"cwd": str(repo), "tool_input": {"command": command}}, repo)


@pytest.mark.parametrize(
    "command, expected",
    [
        ("git push origin feature", [([], ["origin", "feature"])]),
        ("git add . && git commit -m x && git push -u origin feature", [([], ["-u", "origin", "feature"])]),
        ("git -C ../other push origin x", [(["-C", "../other"], ["origin", "x"])]),
        ("git push origin a; git push origin b", [([], ["origin", "a"]), ([], ["origin", "b"])]),
        ("git status", []),
        ("git commit -m 'run git push later'", []),
        ("echo 'git push origin main'", []),
    ],
)
def test_push_invocations(command, expected):
    assert push_invocations(command) == expected


def test_push_invocations_err_toward_asking_when_unparseable():
    assert push_invocations("git push origin x '") == [([], [])]
    assert push_invocations("echo 'unbalanced") == []


def test_is_dry_run():
    assert is_dry_run(["--dry-run", "origin", "x"]) and is_dry_run(["-n"]) and is_dry_run(["-un"])
    assert not is_dry_run(["-u", "origin", "x"])
    assert not is_dry_run(["-o", "-n", "origin"])  # "-n" is the push option's value here


@pytest.mark.parametrize(
    "args, remote, refspecs",
    [
        (["-o", "ci.skip", "origin"], "origin", []),
        (["-oci.skip", "origin", "feature"], "origin", ["feature"]),
        (["--push-option", "x", "origin", "main"], "origin", ["main"]),
        (["--repo", "origin"], "origin", []),
        (["--repo=origin", "main"], "main", []),  # like git: the argument wins over --repo
        (["origin", "--", "-weird"], "origin", ["-weird"]),
    ],
)
def test_parse_push_args_reads_option_values_like_git(args, remote, refspecs):
    push = parse_push_args(args)
    assert (push.remote, push.refspecs) == (remote, refspecs)


@pytest.mark.parametrize(
    "command",
    ["git push -o ci.skip origin", "git push --push-option ci.skip origin",
     "git push --repo origin", "git push -uo ci.skip origin", "git push --branches"],
)
def test_option_values_do_not_hide_a_push_to_the_current_protected_branch(command):
    assert check_command(command, "main", PROTECTED), command


def test_option_values_are_not_mistaken_for_flags():
    assert check_command("git push -oforce origin feature", "feature", PROTECTED) is None


def test_git_dash_c_checks_the_branch_of_the_target_repo(tmp_path):
    repo = make_repo(tmp_path / "work", {"git": {"baseBranch": "main"}})
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=other, check=True)
    git(other, "commit", "--allow-empty", "-m", "on main")
    for command in ("git -C ../other push", "git -C ../other push origin HEAD", f"git -C {other} push origin"):
        result = run_guard(repo, command)
        assert result.returncode == 2, command
        assert "'main'" in result.stderr, command

    subprocess.run(["git", "checkout", "-q", "-b", "topic"], cwd=other, check=True)
    reason = decision(run_guard(repo, "git -C ../other push"))["permissionDecisionReason"]
    assert "ref: topic" in reason


def test_every_real_push_asks_the_user(tmp_path):
    repo = make_repo(tmp_path, {"git": {"baseBranch": "main"}})
    for command in (
        "git push",
        "git push -u origin feature",
        "git push origin HEAD",
        "git status && git push origin feature",
        "git push origin x '",  # unparseable: still asks
    ):
        result = run_guard(repo, command)
        assert result.returncode == 0, command
        out = decision(result)
        assert out["hookEventName"] == "PreToolUse", command
        assert out["permissionDecision"] == "ask", command
        assert "approve" in out["permissionDecisionReason"].lower(), command


def test_no_prompt_for_commands_that_do_not_publish(tmp_path):
    repo = make_repo(tmp_path, {"git": {"baseBranch": "main"}})
    for command in (
        "git status",
        "git commit -m 'git push later'",
        "git push --dry-run origin feature",
        "git push -n origin feature",
        "gh pr view 12",
    ):
        result = run_guard(repo, command)
        assert result.returncode == 0, command
        assert result.stdout.strip() == "", command


def test_blocked_pushes_are_denied_not_asked(tmp_path):
    repo = make_repo(tmp_path, {"git": {"baseBranch": "main"}})
    for command in ("git push -f origin feature", "git push origin main", "git push --all"):
        result = run_guard(repo, command)
        assert result.returncode == 2, command
        assert result.stdout.strip() == "", command  # a deny must never be softened into an ask


def test_no_prompt_outside_repos_without_aderx_dev_config(tmp_path):
    repo = make_repo(tmp_path, None)
    result = run_guard(repo, "git push -u origin feature")
    assert result.returncode == 0 and result.stdout.strip() == ""


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo, check=True, capture_output=True,
    )


def test_prompt_shows_what_will_be_published(tmp_path):
    repo = make_repo(tmp_path / "work", {"git": {"baseBranch": "main"}})
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "commit", "--allow-empty", "-m", "first change")
    git(repo, "commit", "--allow-empty", "-m", "second change")

    reason = decision(run_guard(repo, "git push -u origin feature"))["permissionDecisionReason"]
    assert str(remote) in reason
    assert "Commits not yet on the remote: 2" in reason
    assert "first change" in reason and "second change" in reason
    assert "feature" in reason

    # after pushing, nothing new is left to publish
    git(repo, "push", "-u", "origin", "feature")
    reason = decision(run_guard(repo, "git push"))["permissionDecisionReason"]
    assert "Commits not yet on the remote: 0" in reason


def test_prompt_summarises_many_commits(tmp_path):
    repo = make_repo(tmp_path / "work", {"git": {"baseBranch": "main"}})
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    for i in range(8):
        git(repo, "commit", "--allow-empty", "-m", f"change {i}")
    reason = decision(run_guard(repo, "git push origin feature"))["permissionDecisionReason"]
    assert "Commits not yet on the remote: 8" in reason
    assert "and 3 more" in reason


def test_deleting_a_remote_branch_is_described_as_a_deletion(tmp_path):
    repo = make_repo(tmp_path, {"git": {"baseBranch": "main"}})
    reason = decision(run_guard(repo, "git push origin --delete old-branch"))["permissionDecisionReason"]
    assert "DELETES" in reason and "old-branch" in reason
