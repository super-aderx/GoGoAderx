"""Run with: python3 -m pytest tests/  (from the plugin root)"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "skills" / "breakdown" / "scripts" / "check_breakdown.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_checker(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECKER), str(path)], capture_output=True, text=True)


def test_valid_breakdown_passes_and_derives_waves():
    result = run_checker(FIXTURES / "breakdown-valid.md")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    for line in ("wave 0: I1", "wave 1: I2, I3", "wave 2: I4", "max parallel: 2"):
        assert line in result.stdout, line


def test_invalid_breakdown_reports_unknown_deps_and_cycles():
    result = run_checker(FIXTURES / "breakdown-invalid.md")
    assert result.returncode == 1
    for problem in ("unknown issue I9", "dependency cycle"):
        assert problem in result.stdout, problem


def test_same_wave_overlap_is_reported(tmp_path):
    issues = [
        {"id": "I1", "touches": ["src/types.ts"]},
        {"id": "I2", "depends_on": ["I1"], "touches": ["src/api/"]},
        {"id": "I3", "depends_on": ["I1"], "touches": ["src/api/invite.ts"]},
    ]
    path = tmp_path / "breakdown.md"
    path.write_text("```json\n" + json.dumps({"issues": issues}) + "\n```\n")
    result = run_checker(path)
    assert result.returncode == 1
    assert "wave 1: I2 and I3 touch overlapping paths" in result.stdout


def test_missing_issues_block_is_bad_input(tmp_path):
    path = tmp_path / "breakdown.md"
    path.write_text("# Breakdown\n\nNo graph here.\n")
    result = run_checker(path)
    assert result.returncode not in (0, 1)
    assert "no ```json block" in result.stderr


@pytest.mark.parametrize(
    "issues, message",
    [
        ([], '"issues" is empty'),
        ([{"touches": ["a"]}], 'has no string "id"'),
        (["I1"], "is not an object"),
        ([{"id": "I1", "touches": "src/"}], '"touches" must be a list of strings'),
        ([{"id": "I1", "touches": ["a"], "depends_on": "I0"}], '"depends_on" must be a list'),
    ],
)
def test_malformed_issues_are_bad_input_not_a_crash(tmp_path, issues, message):
    path = tmp_path / "breakdown.md"
    path.write_text("```json\n" + json.dumps({"issues": issues}) + "\n```\n")
    result = run_checker(path)
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    assert message in result.stderr


def test_skills_have_matching_frontmatter():
    for skill in (ROOT / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\n"), skill
        block = text.split("---\n", 2)[1]
        fields = dict(line.split(":", 1) for line in block.splitlines() if ":" in line)
        assert fields["name"].strip() == skill.parent.name, skill
        assert fields["description"].strip(), skill


def test_manifest_and_cross_skill_references():
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "aderx-pm"
    skills = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        for ref in re.findall(r"aderx-pm:([\w-]+)", path.read_text(encoding="utf-8")):
            assert ref in skills, f"{path.parent.name} refers to missing skill aderx-pm:{ref}"
