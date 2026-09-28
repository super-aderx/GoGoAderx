"""Structural checks: frontmatter, cross-references between steps, the push gate, config wiring."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    block = text.split("---\n", 2)[1]
    return {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in block.splitlines() if ":" in l)}


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def config_schema() -> dict:
    return json.loads(re.search(r"## Config schema\s+```json\n(.*?)```", skill_text("init"), re.DOTALL).group(1))


def test_skill_and_agent_frontmatter():
    for skill in (ROOT / "skills").glob("*/SKILL.md"):
        fm = frontmatter(skill)
        assert fm["name"] == skill.parent.name
        assert fm["description"]
    for agent in (ROOT / "agents").glob("*.md"):
        fm = frontmatter(agent)
        assert fm["name"] == agent.stem
        assert fm["description"]


def test_cross_references_point_at_real_skills_and_agents():
    names = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")} | {p.stem for p in (ROOT / "agents").glob("*.md")}
    for path in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md")):
        for ref in re.findall(r"aderx-dev:([\w-]+)", path.read_text(encoding="utf-8")):
            assert ref in names, f"{path.relative_to(ROOT)} refers to missing aderx-dev:{ref}"


def test_sections_referenced_by_other_steps_exist_in_the_spec_skeleton():
    skeleton = re.search(r"````markdown\n(.*?)\n````", skill_text("plan"), re.DOTALL).group(1)
    headings = set(re.findall(r"^## (.+)$", skeleton, re.MULTILINE))
    for name in ("build", "pr-create", "pr-feedback"):
        for ref in re.findall(r"`## ([^`]+)`", skill_text(name)):
            assert ref in headings, f"{name} refers to missing spec section '{ref}'"


def test_pr_create_asks_for_push_separately_and_before_pushing():
    text = skill_text("pr-create")
    titles = {int(n): title.lower() for n, title in re.findall(r"^### (\d+)\. (.+)$", text, re.MULTILINE)}
    commits = next(n for n, t in titles.items() if t.startswith("approve the commits"))
    approve_push = next(n for n, t in titles.items() if "approval to push" in t)
    push = next(n for n, t in titles.items() if t.startswith("push"))
    assert commits < approve_push < push
    before_gate = text[text.index("## Steps"): text.index(f"### {approve_push}. ")]
    assert "git push -u origin <branch>" not in before_gate


def test_init_schema_parses_and_hook_scripts_exist():
    assert {"linear", "git", "areas"} <= set(config_schema())
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
    assert any(e["matcher"] == "Bash" and "guard_git.py" in e["hooks"][0]["command"] for e in hooks["PreToolUse"])
    for entries in hooks.values():
        for entry in entries:
            for hook in entry["hooks"]:
                match = re.search(r"scripts/([\w.]+)", hook["command"])
                assert match and (ROOT / "scripts" / match.group(1)).is_file(), hook["command"]


def test_no_dead_config_keys():
    """Every key that init tells users to set must actually be read by something."""
    corpus = "".join(
        p.read_text(encoding="utf-8")
        for p in [*(ROOT / "skills").glob("*/SKILL.md"), *(ROOT / "agents").glob("*.md"), *(ROOT / "scripts").glob("*.py")]
        if p.parent.name != "init"
    )

    def keys(node, prefix=""):
        for key, value in node.items():
            if key == "areas":
                yield from (f"area:{k}" for area in value.values() for k in area)
            elif isinstance(value, dict):
                yield from keys(value, f"{prefix}{key}.")
            else:
                yield f"{prefix}{key}"

    dead = []
    for key in keys(config_schema()):
        if key.startswith("area:"):
            found = f"`{key[5:]}`" in corpus or f'"{key[5:]}"' in corpus  # prose or code
        else:
            found = key in corpus
        if not found:
            dead.append(key)
    assert not dead, f"config keys documented in init but never used: {dead}"
