"""Structural checks: naming, language-agnosticism, profile format, wiring."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "skills" / "init" / "profiles"
REQUIRED_SECTIONS = [
    "Detect", "Area defaults", "Where to look", "Testing conventions",
    "Dependency manifests", "Build notes", "Shortcuts to flag", "Review checklist",
]
LANGUAGE_TERMS = re.compile(
    r"\b(python|pytest|pip|poetry|ruff|mypy|pyright|django|flask|fastapi|pydantic|"
    r"react|jsx|tsx|typescript|eslint|prettier|vitest|jest|tsc|npm|npx|pnpm|yarn)\b",
    re.IGNORECASE,
)


def text_files():
    skip = {".pytest_cache", "__pycache__"}
    for path in ROOT.rglob("*"):
        if path.is_file() and not (skip & set(path.parts)) and path.suffix in {".md", ".json", ".py"}:
            yield path


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    block = text.split("---\n", 2)[1]
    return {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in block.splitlines() if ":" in l)}


def real_profiles():
    return sorted(p for p in PROFILES_DIR.glob("*.md") if p.name != "_template.md")


def test_no_leftover_old_name():
    # Built up so this file does not match itself. The marketplace is still called
    # gogo-aderx, so only the old plugin forms (/x:plan, .x/config.json, x_common) count.
    old = "gogo" + "aderx"
    pattern = re.compile(rf"dev{'flow'}|\.{old}|{old}[:_]")
    offenders = [str(p) for p in text_files() if pattern.search(p.read_text(encoding="utf-8").lower())]
    assert not offenders, offenders


def test_plugin_manifest_name():
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "aderx-dev"


def test_skills_and_agents_are_language_agnostic():
    """Language-specific content must live in profiles, not in skills or agents."""
    targets = [p for p in (ROOT / "skills").rglob("*.md") if PROFILES_DIR not in p.parents]
    targets += list((ROOT / "agents").glob("*.md"))
    assert targets
    offenders = {}
    for path in targets:
        hits = sorted({m.group(0).lower() for m in LANGUAGE_TERMS.finditer(path.read_text(encoding="utf-8"))})
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    assert not offenders, offenders


def test_skill_and_agent_frontmatter():
    for skill in (ROOT / "skills").glob("*/SKILL.md"):
        fm = frontmatter(skill)
        assert fm["name"] == skill.parent.name
        assert fm["description"]
    for agent in (ROOT / "agents").glob("*.md"):
        fm = frontmatter(agent)
        assert fm["name"] == agent.stem
        assert fm["description"]


def test_there_are_builtin_profiles_and_a_template():
    assert (PROFILES_DIR / "_template.md").is_file()
    assert {p.stem for p in real_profiles()} >= {"python", "react"}


@pytest.mark.parametrize("path", real_profiles() + [PROFILES_DIR / "_template.md"], ids=lambda p: p.name)
def test_profile_has_all_sections(path):
    text = path.read_text(encoding="utf-8")
    headings = set(re.findall(r"^## (.+)$", text, re.MULTILINE))
    missing = [s for s in REQUIRED_SECTIONS if s not in headings]
    assert not missing, f"{path.name} is missing sections: {missing}"


@pytest.mark.parametrize("path", real_profiles(), ids=lambda p: p.name)
def test_builtin_profile_area_defaults_are_valid(path):
    assert frontmatter(path)["name"] == path.stem
    section = re.search(r"## Area defaults\s+```json\n(.*?)```", path.read_text(encoding="utf-8"), re.DOTALL)
    assert section, f"{path.name}: no json block under Area defaults"
    defaults = json.loads(section.group(1))
    assert defaults["profile"] == path.stem
    assert "{file}" in defaults["format"]
    assert defaults["extensions"] and defaults["test"]


def test_init_schema_example_parses_and_hooks_scripts_exist():
    init = (ROOT / "skills" / "init" / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"## Config schema\s+```json\n(.*?)```", init, re.DOTALL).group(1)
    config = json.loads(block)
    assert {"profiles", "areas", "git", "hooks"} <= set(config)

    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    for entries in hooks["hooks"].values():
        for entry in entries:
            for hook in entry["hooks"]:
                match = re.search(r"scripts/([\w.]+)", hook["command"])
                assert match and (ROOT / "scripts" / match.group(1)).is_file(), hook["command"]


def test_skills_reference_profile_sections_that_exist():
    used = set()
    for path in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md")):
        used |= set(re.findall(r"`(Where to look|Testing conventions|Dependency manifests|Build notes|Shortcuts to flag|Review checklist)`",
                               path.read_text(encoding="utf-8")))
    assert used == {"Where to look", "Testing conventions", "Dependency manifests",
                    "Build notes", "Shortcuts to flag", "Review checklist"}


SPEC_ORDER = [
    "Overview", "Goals and non-goals", "Interface and I/O contract", "Architecture",
    "Dependencies", "Approach", "Affected scope", "Acceptance criteria", "Test plan",
    "Risks and open questions", "Deviations", "Implementation notes", "Verification",
]


def spec_skeleton() -> str:
    plan = (ROOT / "skills" / "plan" / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"````markdown\n(.*?)\n````", plan, re.DOTALL)
    assert match, "spec skeleton block not found in plan skill"
    return match.group(1)


def test_spec_skeleton_follows_the_intended_flow():
    """requirements -> interface & I/O -> architecture -> dependencies -> steps -> criteria/tests."""
    skeleton = spec_skeleton()
    # Only look at level-2 headings outside of fenced code blocks.
    outside_code = re.sub(r"```.*?```", "", skeleton, flags=re.DOTALL)
    headings = re.findall(r"^## (.+)$", outside_code, re.MULTILINE)
    assert headings == SPEC_ORDER


def test_spec_skeleton_covers_interface_details():
    skeleton = spec_skeleton()
    for sub in ("Interface", "Input", "Output", "Error behavior", "Examples"):
        assert re.search(rf"^### {re.escape(sub)}$", skeleton, re.MULTILINE), sub
    assert "Not allowed" in skeleton and "Reuse" in skeleton  # explicit dependency policy
    assert not re.search(r"^## \d+\.", skeleton, re.MULTILINE), "spec headings must be unnumbered"


def test_sections_referenced_by_other_steps_exist_in_the_skeleton():
    skeleton_headings = set(re.findall(r"^## (.+)$", spec_skeleton(), re.MULTILINE))
    for name in ("build", "pr-create"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        for ref in re.findall(r"`## ([^`]+)`", text):
            assert ref in skeleton_headings, f"{name} refers to missing spec section '{ref}'"
    build = (ROOT / "skills" / "build" / "SKILL.md").read_text(encoding="utf-8")
    assert "Interface and I/O contract" in build and "Dependencies" in build
    verifier = (ROOT / "agents" / "verifier.md").read_text(encoding="utf-8")
    assert "Interface and I/O contract" in verifier and "Dependencies" in verifier


def test_pr_create_has_a_dedicated_push_approval_gate():
    text = (ROOT / "skills" / "pr-create" / "SKILL.md").read_text(encoding="utf-8")
    steps = re.findall(r"^### (\d+)\. (.+)$", text, re.MULTILINE)
    titles = {int(n): title for n, title in steps}
    approve_push = next(n for n, title in titles.items() if "approval to push" in title.lower())
    do_push = next(n for n, title in titles.items() if title.lower().startswith("push"))
    commits_approval = next(n for n, title in titles.items() if title.lower().startswith("approve the commits"))
    # commits approved first, then a *separate* push approval, then the push itself
    assert commits_approval < approve_push < do_push
    # the push command only appears at/after the push step, never before its approval
    section_starts = {n: text.index(f"### {n}. ") for n in titles}
    before_approval = text[: section_starts[approve_push]]
    assert "git push -u origin <branch>" not in before_approval.split("## Steps", 1)[1]
    gate = text[section_starts[approve_push]: section_starts[do_push]]
    for required in ("never approval to push", "clear yes", "do not push", "Do not retry"):
        assert required.lower() in gate.lower(), required


def test_guard_hook_is_registered_for_bash_and_asks_on_push():
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"]
    assert any(entry["matcher"] == "Bash" and "guard_git.py" in entry["hooks"][0]["command"] for entry in hooks)
    source = (ROOT / "scripts" / "guard_git.py").read_text(encoding="utf-8")
    assert '"permissionDecision": "ask"' in source


def test_manifest_description_is_language_neutral():
    description = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["description"]
    assert not LANGUAGE_TERMS.search(description), description


def test_no_dead_config_keys():
    """Every key that init tells users to set must actually be read by something."""
    init = (ROOT / "skills" / "init" / "SKILL.md").read_text(encoding="utf-8")
    schema = json.loads(re.search(r"## Config schema\s+```json\n(.*?)```", init, re.DOTALL).group(1))

    corpus = ""
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        if path.parent.name != "init":
            corpus += path.read_text(encoding="utf-8")
    for path in list((ROOT / "agents").glob("*.md")) + list((ROOT / "scripts").glob("*.py")):
        corpus += path.read_text(encoding="utf-8")

    def keys(node, prefix=""):
        for key, value in node.items():
            if key == "areas":
                for area in value.values():
                    for area_key in area:
                        yield f"area:{area_key}"
            elif isinstance(value, dict):
                yield from keys(value, f"{prefix}{key}.")
            else:
                yield f"{prefix}{key}"

    dead = []
    for key in keys(schema):
        if key == "version":
            continue  # schema version marker, reserved for future migrations
        if key.startswith("area:"):
            name = key[5:]
            found = f"`{name}`" in corpus or f'"{name}"' in corpus  # prose or code
        else:
            found = key in corpus
        if not found:
            dead.append(key)
    assert not dead, f"config keys documented in init but never used: {dead}"


def test_every_hook_matcher_names_real_tools():
    real_tools = {"Bash", "Edit", "Write", "Read", "Glob", "Grep"}
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
    for entries in hooks.values():
        for entry in entries:
            assert set(entry["matcher"].split("|")) <= real_tools, entry["matcher"]
